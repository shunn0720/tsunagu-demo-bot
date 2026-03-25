# つなぐラボ デモサーバーBot

教育系・福祉系NPO法人への営業時に「実際に触って体験できるデモ環境」として使用するDiscordサーバーを、**ワンコマンドで構築**するBotです。

## 主な機能

- **`!setup` ワンコマンド構築** — チャンネル・カテゴリ・ロール・Embed・FAQを一括生成
- **自習サポートBot** — AIがヒント型で学習を支援（答えは教えない）
- **学習記録** — 質問内容・教科・回数を自動記録・可視化
- **FAQ応答** — PersistentViewによるボタン式FAQ（Bot再起動後も動作）
- **導入相談通知** — 相談チャンネルへの投稿をスタッフに自動通知
- **ダッシュボード** — 利用状況をEmbed集計で表示

## 技術スタック

| 項目 | 技術 |
|---|---|
| 言語 | Python 3.11+ |
| Discord | discord.py v2.3.2+ |
| AI API | Gemini 3.1 Flash-Lite（google-genai SDK） |
| DB | PostgreSQL（asyncpg） |
| デプロイ | Railway（GitHub連携 → 自動デプロイ） |

## ファイル構成

```
tsunagu-demo-bot/
├── main.py                  # Bot起動・Cog読み込み・on_ready
├── config.py                # 設定値（チャンネル名・ロール名・Embed色等）
├── db.py                    # PostgreSQL接続・テーブル作成（asyncpg）
├── cogs/
│   ├── setup_server.py      # !setup コマンド（一括構築）
│   ├── welcome.py           # メンバー参加時のWelcome DM + ロール付与
│   ├── study.py             # 自習サポートBot（メインAI機能）
│   ├── study_log.py         # 学習記録の自動投稿・集計
│   ├── faq.py               # FAQ応答（PersistentView）
│   ├── inquiry.py           # 導入相談チャンネル管理
│   └── dashboard.py         # 利用状況ダッシュボード
├── utils/
│   ├── ai_client.py         # Gemini API呼び出し
│   ├── embed_builder.py     # Embed生成ユーティリティ（色統一）
│   └── rate_limiter.py      # ユーザーごとのAPI制限管理
├── .env.example
├── requirements.txt
├── railway.json
└── Procfile
```

## セットアップ（ローカル開発）

```bash
# 1. リポジトリをクローン
git clone https://github.com/shunn0720/tsunagu-demo-bot.git
cd tsunagu-demo-bot

# 2. 仮想環境を作成
python -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# 4. 環境変数を設定
cp .env.example .env
# .env を編集してトークン等を設定

# 5. Bot起動
python main.py
```

## 環境変数

| 変数名 | 説明 | 必須 |
|---|---|---|
| `DISCORD_TOKEN` | Discord Botトークン | ✅ |
| `GUILD_ID` | 対象サーバーのID | ✅ |
| `GEMINI_API_KEY` | Gemini APIキー | ✅ |
| `DATABASE_URL` | PostgreSQL接続URL | ✅ |
| `DAILY_QUESTION_LIMIT` | 1日あたりの質問上限（デフォルト: 30） | |
| `BOT_PREFIX` | コマンドプレフィックス（デフォルト: `!`） | |
| `LOG_LEVEL` | ログレベル（デフォルト: `INFO`） | |

## Railwayデプロイ

1. [Railway](https://railway.app) でプロジェクト作成 → GitHubリポジトリ連携
2. PostgreSQLアドオンを追加（`DATABASE_URL` が自動注入される）
3. Variables タブで `DISCORD_TOKEN` / `GUILD_ID` / `GEMINI_API_KEY` を設定
4. `git push` で自動デプロイ

## コマンド一覧

| コマンド | 権限 | 説明 |
|---|---|---|
| `!setup` | 管理者 | サーバー一括構築 |
| `/study-summary` | 全員 | 学習記録の日次・週次サマリ |
| `/dashboard` | スタッフ以上 | 利用状況ダッシュボード |
