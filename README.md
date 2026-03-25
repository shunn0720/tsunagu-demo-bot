# つなぐラボ デモサーバーBot

教育系・福祉系NPO法人への営業時に「実際に触って体験できるデモ環境」として使用するDiscordサーバーを、**ワンコマンドで構築**するBotです。

---

## 機能一覧

| 機能 | 説明 |
|---|---|
| `!setup` ワンコマンド構築 | チャンネル・カテゴリ・ロール・Embed・FAQを一括生成。2回目以降は既存をスキップ（冪等性） |
| 自習サポートAI | #自習サポート でAIがヒント型学習支援。答えは教えず考え方を導く（Gemini 3.1 Flash-Lite） |
| 学習記録 | 質問の教科・回数を自動記録。#学習記録 にミニEmbed投稿。`/study-summary` で日次・週次サマリ |
| FAQ応答 | PersistentViewボタン式FAQ（4項目）。Bot再起動後も動作 |
| 導入相談通知 | #導入相談 への投稿を #bot-log に自動通知。スタッフが即対応可能 |
| ダッシュボード | `/dashboard` でAI利用回数・教科別質問数・アクティブユーザー数を集計表示 |
| Welcome対応 | メンバー参加時に「体験ユーザー」ロール自動付与 + DM + bot-log通知 |

---

## 技術スタック

| 項目 | 技術 |
|---|---|
| 言語 | Python 3.11+ |
| Discord | discord.py v2.3.2+ |
| AI API | Gemini 3.1 Flash-Lite（google-genai SDK） |
| DB | PostgreSQL（asyncpg） |
| デプロイ | Railway（GitHub連携 → 自動デプロイ） |

---

## ファイル構成

```
tsunagu-demo-bot/
├── main.py                  # Bot起動・Cog読み込み・on_ready
├── config.py                # 設定値（チャンネル名・ロール名・Embed色等）
├── db.py                    # PostgreSQL接続・テーブル作成（asyncpg）
├── cogs/
│   ├── __init__.py
│   ├── setup_server.py      # !setup コマンド（一括構築）
│   ├── welcome.py           # メンバー参加時のWelcome DM + ロール付与
│   ├── study.py             # 自習サポートBot（メインAI機能）
│   ├── study_log.py         # 学習記録の自動投稿・集計
│   ├── faq.py               # FAQ応答（PersistentView）
│   ├── inquiry.py           # 導入相談チャンネル管理
│   └── dashboard.py         # 利用状況ダッシュボード
├── utils/
│   ├── __init__.py
│   ├── ai_client.py         # Gemini API呼び出し
│   ├── embed_builder.py     # Embed生成ユーティリティ（色統一）
│   └── rate_limiter.py      # ユーザーごとのAPI制限管理
├── .env.example             # ローカル開発用テンプレート
├── .gitignore
├── requirements.txt
├── railway.json             # Railway デプロイ設定
├── Procfile
└── README.md
```

---

## ローカル開発セットアップ

### 前提条件
- Python 3.11+
- PostgreSQL（ローカルまたはDocker）
- Discord Bot トークン（[Developer Portal](https://discord.com/developers/applications) で取得）
- Gemini API キー（[Google AI Studio](https://aistudio.google.com/) で取得）

### 手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/shunn0720/tsunagu-demo-bot.git
cd tsunagu-demo-bot

# 2. 仮想環境を作成・有効化
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# 4. 環境変数を設定
cp .env.example .env
# .env を編集して各トークン・接続情報を入力

# 5. PostgreSQLデータベースを準備
createdb tsunagu_demo
# または Docker: docker run -d -p 5432:5432 -e POSTGRES_DB=tsunagu_demo -e POSTGRES_PASSWORD=password postgres:16

# 6. Bot起動
python main.py
```

起動後、Discordサーバーで `!setup` を実行するとチャンネル・ロール・Embedが一括生成されます。

---

## Railwayデプロイ

```
1. GitHubリポジトリを連携
   - railway.app にログイン
   - 「New Project」→「Deploy from GitHub Repo」

2. PostgreSQLアドオンを追加
   - プロジェクト画面で「+ New」→「Database」→「PostgreSQL」
   - DATABASE_URL が自動注入される

3. 環境変数を設定（Railway管理画面 → Variables）
   DISCORD_TOKEN=xxxxx
   GUILD_ID=xxxxx
   GEMINI_API_KEY=xxxxx
   DAILY_QUESTION_LIMIT=30
   BOT_PREFIX=!
   LOG_LEVEL=INFO

4. git push で自動デプロイ

5. 動作確認
   - DiscordでBotがオンラインか確認
   - !setup を実行
   - #自習サポート でAI応答テスト
```

---

## コマンド一覧

| コマンド | 種別 | 権限 | 説明 |
|---|---|---|---|
| `!setup` | テキストコマンド | 管理者 | サーバー一括構築（チャンネル・ロール・Embed） |
| `/study-summary` | スラッシュコマンド | 全員 | 学習記録の日次・週次サマリ |
| `/dashboard` | スラッシュコマンド | スタッフ以上 | 利用状況ダッシュボード |

---

## Embed色ルール

| 用途 | 色コード | 色名 |
|---|---|---|
| 教育系 | `0xFFC6E2` | ピンク |
| 福祉系 | `0xC6C6FF` | ラベンダー |
| 通知・警告 | `0xFFFFC6` | イエロー |
| 成功 | `0x4ECDC4` | ティール |
| エラー | `0xFF6B6B` | レッド |

---

## ライセンス

MIT License
