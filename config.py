"""
設定ファイル — ここを編集することでメッセージや選択肢を変更できます
"""
import os

# ─── LINE API 認証情報 ───────────────────────────────────────────────────────
CHANNEL_SECRET = os.environ.get(
    "CHANNEL_SECRET", "83fd873c5d61e24fbe33b7a82446746c"
)
ACCESS_TOKEN = os.environ.get(
    "ACCESS_TOKEN",
    "nyb6dw0abZB60zOWzbdWDOhGqkwRY0N8+l6qAi0wUzMh1CCv3Kmxws8Cw7FzZN0JXdL"
    "/MRIQj8z0lhXFEryFKzo65eOXzOD4cyMGUd/h/cNGGu4ol7Z66IsH2MNwGzURNIrbG6E"
    "BAep38o+GET29OgdB04t89/1O/w1cDnyilFU=",
)

# 管理者の LINE User ID
ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID", "Uad47c684ec4b35fb22caf8d6d7a8b519")

# Google Apps Script Web App URL（マップ・スプレッドシート連携）
GAS_URL = os.environ.get(
    "GAS_URL",
    "https://script.google.com/macros/s/AKfycbzOeCvJ8Ln1ytFZWcvxapfPY4zB9tZe8OM9ZJTF8AWVvD_xsuEnHdFMq3w1bV3OulWi/exec"
)

# LIFF ID（LINE Developers で発行。例: 2000000000-aBcDeFgH）
LIFF_ID = os.environ.get("LIFF_ID", "")
# LIFF URL（ユーザーに案内するリンク）
LIFF_URL = f"https://liff.line.me/{LIFF_ID}" if LIFF_ID else ""

# ─── 共通メッセージ ────────────────────────────────────────────────────────────
WELCOME_MESSAGE = (
    "キャットローフのTNR活動LINEへようこそ！🐱\n"
    "下のメニューからお選びください。"
)

COMPLETE_MESSAGE = (
    "ご報告ありがとうございます🐾\n\n"
    "内容を確認後、順次対応させていただきます。\n"
    "場所や内容によっては対応できない場合もございます。\n\n"
    "詳しくお聞きしたい場合はこちらからご連絡させていただく場合もあります。\n\n"
    "お時間をいただく場合がありますが、どうぞよろしくお願いいたします🐾"
)

UNKNOWN_MESSAGE = (
    "メニューから操作を選んでください🐱\n"
    "下のリッチメニューをタップするか、\n"
    "「情報提供」または「TNR相談」と入力してください。"
)

CANCEL_MESSAGE = "キャンセルしました。またいつでもどうぞ🐾"

# ─── 情報提供フロー ────────────────────────────────────────────────────────────
INFO_START = (
    "野良猫の情報提供ありがとうございます🐱\n\n"
    "【STEP 1/6】\n"
    "耳カットのない猫の写真を送ってください📷\n"
    "複数枚ある場合はすべて送ってから\n「送り終わりました」ボタンを押してください。\n\n"
    "※ 写真がない場合は「スキップ」と入力してください"
)

INFO_PHOTO_ADDING = (
    "写真を受け取りました📷\n"
    "追加の写真があればそのまま送ってください。\n"
    "送り終わったら下のボタンを押してください👇"
)

INFO_ASK_LOCATION = (
    "【STEP 2/6】\n"
    "猫を見かけた場所を教えてください📍\n\n"
    "テキストで住所・目印を入力するか、\n"
    "下の「位置情報を送る」ボタンをご利用ください。"
)

INFO_ASK_COUNT = (
    "【STEP 3/6】\n"
    "何匹いましたか？\n"
    "下のボタンから選んでください👇"
)

INFO_ASK_TIMING = (
    "【STEP 4/6】\n"
    "見かけた時間帯を教えてください🕐\n\n"
    "例：朝7時頃、夕方17〜18時頃、夜21時頃　など\n"
    "テキストで自由に入力してください。"
)

INFO_ASK_FEEDER = (
    "【STEP 5/6】\n"
    "ご飯をあげている人は分かりますか？"
)

INFO_ASK_SUPPLEMENT = (
    "【STEP 6/6】\n"
    "最後に補足で伝えたいことがあれば入力してください📝\n\n"
    "特になければ「なし」ボタンを押してください。"
)

# 情報提供フロー 選択肢
INFO_PHOTO_DONE_OPTION = "送り終わりました"
INFO_COUNT_OPTIONS = ["1匹", "2〜5匹", "5匹以上", "わからない"]
INFO_FEEDER_OPTIONS = ["はい", "いいえ", "わからない"]
INFO_SUPPLEMENT_OPTIONS = ["なし"]

# ─── TNR相談フロー ─────────────────────────────────────────────────────────────
TNR_CAUTIONS = (
    "✂️ TNR（捕獲・不妊手術・元の場所へのリリース）のご相談を承ります。\n\n"
    "ご依頼の前に以下の注意事項をご確認ください。\n\n"
    "━━━━━━━━━━━━━━━━\n"
    "・場所や状況によってはお受けできない場合もありますのでご了承ください\n\n"
    "・ご飯をあげている方には、費用の一部をご負担いただく場合があります\n"
    "　補助金制度をご利用の場合はお知らせください\n\n"
    "・手術は「香川スペイクリニック」にて行う予定です\n"
    "　費用の目安：1匹 5,500円\n"
    "　https://kagawa-spay.com\n\n"
    "・ご相談から対応まで数週間〜数ヶ月お時間をいただく場合があります\n\n"
    "・当活動では猫の保護・引き取りは行っておりません\n"
    "　ご自身で保護をご希望の場合はその旨をお知らせください\n\n"
    "・いただいた個人情報は活動目的以外には使用いたしません\n"
    "━━━━━━━━━━━━━━━━\n\n"
    "上記にご同意いただける場合は「同意する」を押してください。"
)

TNR_ASK_LOCATION = (
    "【STEP 1/2】\n"
    "猫のいる場所を教えてください📍\n\n"
    "テキストで住所・目印を入力するか、\n"
    "下の「位置情報を送る」ボタンをご利用ください。"
)

TNR_ASK_DETAIL = (
    "【STEP 2/2】\n"
    "相談内容を自由に入力してください📝\n\n"
    "例）・猫は3匹いて子猫もいます\n"
    "　　・毎朝7時頃にご飯をあげています\n"
    "　　・近所の方も気にしているようです\n\n"
    "頭数・時間帯・状況など、わかる範囲で教えてください。"
)

# TNR相談フロー 選択肢
TNR_CONSENT_OPTIONS = ["同意する", "キャンセル"]

# ─── 管理者通知テンプレート ────────────────────────────────────────────────────
ADMIN_INFO_TEMPLATE = (
    "📋【野良猫 情報提供】\n"
    "━━━━━━━━━━━━━━\n"
    "日時: {datetime}\n"
    "━━━━━━━━━━━━━━\n"
    "📸 写真: {photos}\n"
    "📍 場所: {location}\n"
    "🐱 頭数: {count}\n"
    "🕐 時間帯: {timing}\n"
    "🍚 餌やり: {feeder}\n"
    "📝 補足: {supplement}\n"
    "━━━━━━━━━━━━━━\n"
    "送信者LINEで確認してください"
)

ADMIN_TNR_TEMPLATE = (
    "📋【TNR相談】\n"
    "━━━━━━━━━━━━━━\n"
    "送信者: {display_name}\n"
    "ユーザーID: {user_id}\n"
    "日時: {datetime}\n"
    "━━━━━━━━━━━━━━\n"
    "📍 場所: {location}\n"
    "📝 相談内容: {detail}\n"
    "━━━━━━━━━━━━━━\n"
    "🔇 ボット停止: /off {user_id}"
)
