# Render デプロイ手順

## 1. GitHubリポジトリを作成

```bash
cd linebot/
git init
git add .
git commit -m "初回コミット"
```

GitHubで新しいリポジトリを作成して push してください。

---

## 2. Renderにデプロイ

1. https://render.com にログイン（無料アカウントで OK）
2. 「New +」→「Web Service」をクリック
3. GitHubリポジトリを選択して接続
4. 以下の設定を確認：
   - **Name**: catloaf-tnr-bot（任意）
   - **Region**: Singapore（日本に近い）
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 60`
   - **Instance Type**: Free

5. 「Environment」タブで以下の環境変数を設定：

| Key | Value |
|-----|-------|
| `CHANNEL_SECRET` | 83fd873c5d61e24fbe33b7a82446746c |
| `ACCESS_TOKEN` | LINE Messaging APIのアクセストークン |
| `ADMIN_USER_ID` | あなたのLINE User ID（後述） |

6. 「Create Web Service」をクリック
7. デプロイ完了後、URLが発行されます（例: `https://catloaf-tnr-bot.onrender.com`）

---

## 3. LINE DevelopersにWebhook URLを設定

1. https://developers.line.biz/ にログイン
2. 対象チャンネルを選択
3. 「Messaging API設定」タブ
4. **Webhook URL** に `https://catloaf-tnr-bot.onrender.com/callback` を入力
5. 「Webhookの利用」を **ON** に
6. 「検証」ボタンで動作確認（200 OKが返れば成功）

---

## 4. 管理者 User ID を取得する

1. 上記設定後、ボットに話しかける
2. Renderのログ（「Logs」タブ）を開く
3. `user_id=Uxxxxxxxxxx` の形式でログに表示される
4. その値を `ADMIN_USER_ID` 環境変数に設定して保存

---

## 5. リッチメニューを作成する

ローカル環境で一度だけ実行：

```bash
cd linebot/
pip install line-bot-sdk Pillow requests
python create_rich_menu.py
```

---

## 6. 動作確認チェックリスト

- [ ] リッチメニューが表示される
- [ ] 「野良猫の情報を提供する」→ 写真→場所→頭数→時間帯→餌やり の流れで完了できる
- [ ] 「TNRの相談をしたい」→ 注意事項→同意→餌やり→場所→頭数 の流れで完了できる
- [ ] 完了後に管理者（自分）にLINE通知が届く
- [ ] 「キャンセル」でフローが中断される

---

## Render 無料プランの注意点

- 15分間アクセスがないとサーバーがスリープします
- スリープ中のメッセージはサーバー起動後（30秒〜1分）に処理されます
- 月750時間の無料枠あり（1台なら常時稼働可能）
- スリープ対策には UptimeRobot などで15分ごとに `https://your-app.onrender.com/` にアクセスさせると解消できます
