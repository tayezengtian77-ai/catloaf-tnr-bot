"""
リッチメニュー作成スクリプト
デプロイ後に一度だけ実行してください。

使用方法:
    pip install line-bot-sdk Pillow
    python create_rich_menu.py
"""
import io
import json
import sys

import requests
from PIL import Image, ImageDraw, ImageFont

import config


def create_rich_menu_image() -> bytes:
    """2パネルのリッチメニュー画像を生成する"""
    W, H = 2500, 843

    img = Image.new("RGB", (W, H), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    # 左パネル（情報提供）
    draw.rectangle([0, 0, W // 2 - 1, H], fill="#FFF0E0")
    # 右パネル（TNR相談）
    draw.rectangle([W // 2, 0, W, H], fill="#E8F5E9")

    # 区切り線
    draw.rectangle([W // 2 - 3, 0, W // 2 + 3, H], fill="#CCCCCC")

    # フォント（システムフォントを試みる）
    font_large = None
    font_small = None
    font_paths = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in font_paths:
        try:
            font_large = ImageFont.truetype(path, 90)
            font_small = ImageFont.truetype(path, 55)
            break
        except (IOError, OSError):
            continue

    if font_large is None:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 左パネルテキスト
    draw.text((W // 4, H // 2 - 120), "🐱", font=font_large, fill="#FF8C00", anchor="mm")
    draw.text((W // 4, H // 2 + 20), "野良猫の情報を", font=font_small, fill="#333333", anchor="mm")
    draw.text((W // 4, H // 2 + 90), "提供する", font=font_small, fill="#333333", anchor="mm")

    # 右パネルテキスト
    draw.text((W * 3 // 4, H // 2 - 120), "✂️", font=font_large, fill="#2E7D32", anchor="mm")
    draw.text((W * 3 // 4, H // 2 + 20), "TNRの相談を", font=font_small, fill="#333333", anchor="mm")
    draw.text((W * 3 // 4, H // 2 + 90), "したい", font=font_small, fill="#333333", anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def create_rich_menu(api_endpoint: str, headers: dict) -> str:
    """リッチメニューを作成して menu_id を返す"""
    body = {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": "TNRメニュー",
        "chatBarText": "メニューを開く",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 1250, "height": 843},
                "action": {
                    "type": "message",
                    "text": "野良猫の情報を提供する",
                },
            },
            {
                "bounds": {"x": 1250, "y": 0, "width": 1250, "height": 843},
                "action": {
                    "type": "message",
                    "text": "TNRの相談をしたい",
                },
            },
        ],
    }
    res = requests.post(
        f"{api_endpoint}/richmenu",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(body),
    )
    res.raise_for_status()
    menu_id = res.json()["richMenuId"]
    print(f"✅ リッチメニュー作成: {menu_id}")
    return menu_id


def upload_image(api_endpoint: str, headers: dict, menu_id: str, image_bytes: bytes) -> None:
    """リッチメニューに画像をアップロード"""
    res = requests.post(
        f"https://api-data.line.me/v2/bot/richmenu/{menu_id}/content",
        headers={**headers, "Content-Type": "image/jpeg"},
        data=image_bytes,
    )
    res.raise_for_status()
    print("✅ 画像アップロード完了")


def set_default_rich_menu(api_endpoint: str, headers: dict, menu_id: str) -> None:
    """デフォルトのリッチメニューに設定"""
    res = requests.post(
        f"{api_endpoint}/user/all/richmenu/{menu_id}",
        headers=headers,
    )
    res.raise_for_status()
    print("✅ デフォルトリッチメニューに設定完了")


def delete_all_rich_menus(api_endpoint: str, headers: dict) -> None:
    """既存のリッチメニューを全削除（再作成時に使用）"""
    res = requests.get(f"{api_endpoint}/richmenu/list", headers=headers)
    if res.ok:
        for menu in res.json().get("richmenus", []):
            mid = menu["richMenuId"]
            requests.delete(f"{api_endpoint}/richmenu/{mid}", headers=headers)
            print(f"🗑️ 削除: {mid}")


def main():
    api_endpoint = "https://api.line.me/v2/bot"
    headers = {"Authorization": f"Bearer {config.ACCESS_TOKEN}"}

    print("=== リッチメニュー作成開始 ===")

    # 既存メニューを削除するか確認
    ans = input("既存のリッチメニューをすべて削除しますか？ (y/N): ").strip().lower()
    if ans == "y":
        delete_all_rich_menus(api_endpoint, headers)

    # メニュー作成
    menu_id = create_rich_menu(api_endpoint, headers)

    # 画像生成 & アップロード
    print("🖼️  メニュー画像を生成中...")
    image_bytes = create_rich_menu_image()
    upload_image(api_endpoint, headers, menu_id, image_bytes)

    # デフォルトに設定
    set_default_rich_menu(api_endpoint, headers, menu_id)

    print(f"\n🎉 完了！リッチメニューID: {menu_id}")
    print("LINE公式アカウントのチャット画面に2択メニューが表示されます。")


if __name__ == "__main__":
    main()
