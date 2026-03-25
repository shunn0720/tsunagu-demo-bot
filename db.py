"""
つなぐラボ デモサーバーBot - データベース接続・テーブル作成
PostgreSQL（asyncpg）によるコネクションプール管理
"""

import os
import asyncpg


async def create_pool() -> asyncpg.Pool:
    """
    コネクションプールを作成して返す。
    Railway環境: DATABASE_URL が自動注入される
    ローカル環境: .env から読み込む
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    pool = await asyncpg.create_pool(
        database_url,
        min_size=2,
        max_size=10,
        command_timeout=60,
    )
    return pool


async def init_tables(pool: asyncpg.Pool) -> None:
    """
    Bot起動時にテーブルを自動作成する。
    再デプロイのたびに実行されるため、すべて IF NOT EXISTS を使用。
    """
    async with pool.acquire() as conn:
        # 学習記録テーブル
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS study_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                user_name VARCHAR(100) NOT NULL,
                question TEXT NOT NULL,
                subject VARCHAR(50),
                channel_id BIGINT NOT NULL,
                guild_id BIGINT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_study_logs_user
                ON study_logs(user_id);
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_study_logs_guild_date
                ON study_logs(guild_id, created_at);
        """)

        # レート制限管理テーブル
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                guild_id BIGINT NOT NULL,
                date DATE NOT NULL DEFAULT CURRENT_DATE,
                count INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, guild_id, date)
            );
        """)

        # サーバーセットアップ状態管理テーブル
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS setup_state (
                guild_id BIGINT PRIMARY KEY,
                setup_completed BOOLEAN DEFAULT FALSE,
                setup_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
