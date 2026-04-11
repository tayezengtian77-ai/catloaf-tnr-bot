"""
キャットローフ TNR活動 LINE チャットボット
"""
import logging
import uuid
import requests as http_requests
from datetime import datetime
from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    PushMessageRequest,
    QuickReply,
    QuickReplyItem,
    LocationAction,
    MessageAction,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    FollowEvent,
    ImageMessageContent,
    LocationMessageContent,
    MessageEvent,
    TextMessageContent,
)

import config

# ─── 初期化 ────────────────────────────────────────────────────────────────────
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

line_config = Configuration(access_token=config.ACCESS_TOKEN)
handler = WebhookHandler(config.CHANNEL_SECRET)

# ─── セッション管理（インメモリ） ──────────────────────────────────────────────
sessions: dict[str, dict] = {}

# ─── ボットオフユーザー管理 ───────────────────────────────────────────────────
bot_off_users: set[str] = set()  # ボットをオフにしているユーザーIDのセット

# ─── 状態定数 ──────────────────────────────────────────────────────────────────
IDLE           = "idle"
INFO_PHOTO     = "info_photo"       # 写真受付中（複数枚対応）
INFO_LOCATION  = "info_location"
INFO_COUNT     = "info_count"
INFO_TIMING    = "info_timing"      # 自由テキスト入力
INFO_FEEDER    = "info_feeder"
INFO_SUPPLEMENT= "info_supplement"  # 補足入力
TNR_CONSENT    = "tnr_consent"
TNR_LOCATION   = "tnr_location"    # 場所（STEP1）
TNR_DETAIL     = "tnr_detail"      # 自由記入（STEP2）

# ─── セッションヘルパー ────────────────────────────────────────────────────────
def get_session(user_id: str) -> dict:
    if user_id not in sessions:
        sessions[user_id] = {"state": IDLE, "data": {}}
    return sessions[user_id]

def set_state(user_id: str, state: str) -> None:
    get_session(user_id)["state"] = state

def get_state(user_id: str) -> str:
    return get_session(user_id)["state"]

def save_data(user_id: str, key: str, value) -> None:
    get_session(user_id)["data"][key] = value

def get_data(user_id: str) -> dict:
    return get_session(user_id)["data"]

def reset_session(user_id: str) -> None:
    sessions[user_id] = {"state": IDLE, "data": {}}

# ─── LINE API ヘルパー ──────────────────────────────────────────────────────────
def reply(reply_token: str, messages: list) -> None:
    with ApiClient(line_config) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=messages)
        )

def push(user_id: str, messages: list) -> None:
    if not user_id:
        return
    with ApiClient(line_config) as api_client:
        MessagingApi(api_client).push_message(
            PushMessageRequest(to=user_id, messages=messages)
        )

def get_display_name(user_id: str) -> str:
    try:
        with ApiClient(line_config) as api_client:
            profile = MessagingApi(api_client).get_profile(user_id)
            return profile.display_name
    except Exception:
        return "不明"

def text_msg(text: str, quick_reply: QuickReply = None) -> TextMessage:
    return TextMessage(text=text, quick_reply=quick_reply)

def quick_reply_buttons(*labels: str) -> QuickReply:
    return QuickReply(
        items=[
            QuickReplyItem(action=MessageAction(label=lb, text=lb))
            for lb in labels
        ]
    )

def quick_reply_with_location(*labels: str) -> QuickReply:
    items = [
        QuickReplyItem(action=MessageAction(label=lb, text=lb))
        for lb in labels
    ]
    items.append(QuickReplyItem(action=LocationAction(label="📍 位置情報を送る")))
    return QuickReply(items=items)

# ─── 管理者通知 ────────────────────────────────────────────────────────────────
def notify_admin_info(user_id: str, data: dict) -> None:
    if not config.ADMIN_USER_ID:
        return
    display_name = get_display_name(user_id)
    photos = f"{data.get('photo_count', 0)}枚" if data.get("photo_count") else "なし"
    supplement = data.get("supplement", "なし")
    if supplement == "なし":
        supplement = "なし"
    msg = config.ADMIN_INFO_TEMPLATE.format(
        display_name=display_name,
        user_id=user_id,
        datetime=datetime.now().strftime("%Y/%m/%d %H:%M"),
        photos=photos,
        location=data.get("location", "未回答"),
        count=data.get("count", "未回答"),
        timing=data.get("timing", "未回答"),
        feeder=data.get("feeder", "未回答"),
        supplement=supplement,
    )
    push(config.ADMIN_USER_ID, [text_msg(msg)])

def notify_admin_tnr(user_id: str, data: dict) -> None:
    if not config.ADMIN_USER_ID:
        return
    display_name = get_display_name(user_id)
    msg = config.ADMIN_TNR_TEMPLATE.format(
        display_name=display_name,
        user_id=user_id,
        datetime=datetime.now().strftime("%Y/%m/%d %H:%M"),
        location=data.get("location", "未回答"),
        detail=data.get("detail", "未回答"),
    )
    push(config.ADMIN_USER_ID, [text_msg(msg)])

# ─── フロー開始 ────────────────────────────────────────────────────────────────
def start_info_flow(reply_token: str, user_id: str) -> None:
    reset_session(user_id)
    set_state(user_id, INFO_PHOTO)
    reply(reply_token, [text_msg(config.INFO_START)])

def start_tnr_flow(reply_token: str, user_id: str) -> None:
    reset_session(user_id)
    set_state(user_id, TNR_CONSENT)
    qr = quick_reply_buttons(*config.TNR_CONSENT_OPTIONS)
    reply(reply_token, [text_msg(config.TNR_CAUTIONS, quick_reply=qr)])

# ─── 各ステップのメッセージ送信 ────────────────────────────────────────────────
def ask_info_location(reply_token: str) -> None:
    reply(reply_token, [text_msg(config.INFO_ASK_LOCATION, quick_reply=quick_reply_with_location())])

def ask_info_count(reply_token: str) -> None:
    reply(reply_token, [text_msg(config.INFO_ASK_COUNT, quick_reply=quick_reply_buttons(*config.INFO_COUNT_OPTIONS))])

def ask_info_timing(reply_token: str) -> None:
    # 自由テキスト入力のためボタンなし
    reply(reply_token, [text_msg(config.INFO_ASK_TIMING)])

def ask_info_feeder(reply_token: str) -> None:
    reply(reply_token, [text_msg(config.INFO_ASK_FEEDER, quick_reply=quick_reply_buttons(*config.INFO_FEEDER_OPTIONS))])

def ask_info_supplement(reply_token: str) -> None:
    reply(reply_token, [text_msg(config.INFO_ASK_SUPPLEMENT, quick_reply=quick_reply_buttons(*config.INFO_SUPPLEMENT_OPTIONS))])

def ask_tnr_location(reply_token: str) -> None:
    reply(reply_token, [text_msg(config.TNR_ASK_LOCATION, quick_reply=quick_reply_with_location())])

def ask_tnr_detail(reply_token: str) -> None:
    reply(reply_token, [text_msg(config.TNR_ASK_DETAIL)])

def send_to_gas(payload: dict) -> None:
    """Google Apps Script（スプレッドシート＆マップ）にデータを送信"""
    if not config.GAS_URL:
        return
    try:
        http_requests.post(config.GAS_URL, json=payload, timeout=10)
        logger.info("GAS送信完了")
    except Exception as e:
        logger.warning(f"GAS送信エラー: {e}")

def complete_flow(reply_token: str, user_id: str, flow: str) -> None:
    data = get_data(user_id)
    reply(reply_token, [text_msg(config.COMPLETE_MESSAGE)])

    if flow == "info":
        notify_admin_info(user_id, data)
        # スプレッドシート・マップに送信
        loc = data.get("location", "")
        lat = data.get("lat", "")
        lng = data.get("lng", "")
        notes = f"【時間帯】{data.get('timing','')}\n【餌やり】{data.get('feeder','')}\n【補足】{data.get('supplement','')}"
        send_to_gas({
            "id": str(uuid.uuid4())[:8],
            "date": datetime.now().strftime("%Y/%m/%d %H:%M"),
            "address": loc,
            "lat": lat,
            "lng": lng,
            "catCount": data.get("count", ""),
            "feeding": data.get("feeder", ""),
            "cooperation": "",
            "cost": "",
            "notes": notes,
            "reporter": get_display_name(user_id),
            "photos": [],
            "type": "野良猫情報"
        })
    else:
        notify_admin_tnr(user_id, data)
        # スプレッドシート・マップに送信
        loc = data.get("location", "")
        send_to_gas({
            "id": str(uuid.uuid4())[:8],
            "date": datetime.now().strftime("%Y/%m/%d %H:%M"),
            "address": loc,
            "lat": data.get("lat", ""),
            "lng": data.get("lng", ""),
            "catCount": "",
            "feeding": "",
            "cooperation": "",
            "cost": "",
            "notes": data.get("detail", ""),
            "reporter": get_display_name(user_id),
            "photos": [],
            "type": "TNR相談"
        })

    reset_session(user_id)

# ─── Webhook エンドポイント ────────────────────────────────────────────────────
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    logger.info("Webhook received")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning("Invalid signature")
        abort(400)
    return "OK"

# ─── フォローイベント ──────────────────────────────────────────────────────────
@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    logger.info(f"Follow: user_id={user_id}")
    reply(event.reply_token, [text_msg(config.WELCOME_MESSAGE)])

# ─── テキストメッセージ ────────────────────────────────────────────────────────
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    state = get_state(user_id)
    token = event.reply_token

    logger.info(f"Text: user_id={user_id} state={state} text={text[:30]}")

    # ─── 管理者コマンド（/off・/on）半角・全角スラッシュ両対応 ──────────────
    normalized = text.replace("／", "/")  # 全角スラッシュを半角に統一
    if "/off " in normalized:
        target_id = normalized[normalized.index("/off ") + 5:].strip().split()[0]
        bot_off_users.add(target_id)
        reply(token, [text_msg(f"✅ ボットをオフにしました。\n対象: {target_id}\n\n元に戻すには:\n/on {target_id}")])
        return
    if normalized.startswith("/on "):
        target_id = normalized[4:].strip().split()[0]
        bot_off_users.discard(target_id)
        reply(token, [text_msg(f"✅ ボットをオンに戻しました。\n対象: {target_id}")])
        return

    # ─── ユーザー側からスタッフ直接相談モード ─────────────────────────────────
    if text == "スタッフに相談" and user_id != config.ADMIN_USER_ID:
        bot_off_users.add(user_id)
        display_name = get_display_name(user_id)
        push(config.ADMIN_USER_ID, [text_msg(
            f"💬【直接相談リクエスト】\n"
            f"━━━━━━━━━━━━━━\n"
            f"送信者: {display_name}\n"
            f"ユーザーID: {user_id}\n"
            f"━━━━━━━━━━━━━━\n"
            f"ボットをオフにしました。\n"
            f"LINE公式アカウント管理画面から返信してください。\n\n"
            f"終了後: /on {user_id}"
        )])
        reply(token, [text_msg(
            "スタッフに繋ぎます🐱\n\n"
            "担当者からLINEでご連絡いたします。\n"
            "しばらくお待ちください。"
        )])
        return

    # ─── ボットオフのユーザーはスルー ─────────────────────────────────────────
    if user_id in bot_off_users:
        push(config.ADMIN_USER_ID, [text_msg(f"💬 {get_display_name(user_id)}（{user_id}）からメッセージ：\n{text}")])
        return

    # ─ フロー開始トリガー ─
    if text in ("野良猫の情報を提供する", "情報提供"):
        start_info_flow(token, user_id)
        return
    if text in ("TNRの相談をしたい", "TNR相談"):
        start_tnr_flow(token, user_id)
        return
    if text == "キャンセル":
        reset_session(user_id)
        reply(token, [text_msg(config.CANCEL_MESSAGE)])
        return

    # ─── 情報提供フロー ─────────────────────────────────────────────────────────
    if state == INFO_PHOTO:
        if text == "スキップ":
            save_data(user_id, "photo_count", 0)
            set_state(user_id, INFO_LOCATION)
            ask_info_location(token)
        elif text == config.INFO_PHOTO_DONE_OPTION:
            # 「送り終わりました」ボタンが押された
            set_state(user_id, INFO_LOCATION)
            ask_info_location(token)
        else:
            reply(token, [text_msg(
                "写真を送るか、「スキップ」と入力してください📷",
                quick_reply=quick_reply_buttons("スキップ")
            )])

    elif state == INFO_LOCATION:
        save_data(user_id, "location", text)
        set_state(user_id, INFO_COUNT)
        ask_info_count(token)

    elif state == INFO_COUNT:
        save_data(user_id, "count", text)
        set_state(user_id, INFO_TIMING)
        ask_info_timing(token)

    elif state == INFO_TIMING:
        save_data(user_id, "timing", text)
        set_state(user_id, INFO_FEEDER)
        ask_info_feeder(token)

    elif state == INFO_FEEDER:
        save_data(user_id, "feeder", text)
        set_state(user_id, INFO_SUPPLEMENT)
        ask_info_supplement(token)

    elif state == INFO_SUPPLEMENT:
        save_data(user_id, "supplement", text)
        complete_flow(token, user_id, "info")

    # ─── TNR相談フロー ──────────────────────────────────────────────────────────
    elif state == TNR_CONSENT:
        if text == "同意する":
            set_state(user_id, TNR_LOCATION)
            ask_tnr_location(token)
        else:
            reset_session(user_id)
            reply(token, [text_msg(config.CANCEL_MESSAGE)])

    elif state == TNR_LOCATION:
        save_data(user_id, "location", text)
        set_state(user_id, TNR_DETAIL)
        ask_tnr_detail(token)

    elif state == TNR_DETAIL:
        save_data(user_id, "detail", text)
        complete_flow(token, user_id, "tnr")

    # else: フロー外のメッセージは無視（管理者と自由にやり取りできるよう）

# ─── 画像メッセージ ────────────────────────────────────────────────────────────
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    user_id = event.source.user_id
    state = get_state(user_id)
    token = event.reply_token

    if state == INFO_PHOTO:
        session = get_session(user_id)
        count = session["data"].get("photo_count", 0) + 1
        session["data"]["photo_count"] = count
        session["data"].setdefault("photo_ids", []).append(event.message.id)

        # 何枚でも受け付け、「送り終わりました」ボタンを常に表示
        qr = quick_reply_buttons(config.INFO_PHOTO_DONE_OPTION)
        reply(token, [text_msg(
            f"写真 {count}枚目を受け取りました📷\n"
            "追加の写真があればそのまま送ってください。\n"
            "送り終わったら下のボタンを押してください👇",
            quick_reply=qr
        )])
    # else: フロー外は無視

# ─── 位置情報メッセージ ────────────────────────────────────────────────────────
@handler.add(MessageEvent, message=LocationMessageContent)
def handle_location(event):
    user_id = event.source.user_id
    state = get_state(user_id)
    token = event.reply_token

    loc = event.message
    address = loc.address or f"緯度:{loc.latitude:.5f} 経度:{loc.longitude:.5f}"
    location_text = f"{loc.title + ' / ' if loc.title else ''}{address}"

    if state == INFO_LOCATION:
        save_data(user_id, "location", location_text)
        save_data(user_id, "lat", loc.latitude)
        save_data(user_id, "lng", loc.longitude)
        set_state(user_id, INFO_COUNT)
        ask_info_count(token)

    elif state == TNR_LOCATION:
        save_data(user_id, "location", location_text)
        save_data(user_id, "lat", loc.latitude)
        save_data(user_id, "lng", loc.longitude)
        set_state(user_id, TNR_DETAIL)
        ask_tnr_detail(token)

    # else: フロー外は無視

# ─── ヘルスチェック ────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
