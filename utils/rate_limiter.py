"""
つなぐラボ デモサーバーBot - レート制限管理
PostgreSQLのrate_limitsテーブルでユーザーごとの日次制限を管理する
"""

import logging

import asyncpg

logger = logging.getLogger("tsunagu-bot.rate_limiter")


async def check_and_increment(pool, user_id, guild_id, limit):
    """
    ユーザーの本日の利用回数を確認し、制限内であればカウントを+1する。

    Args:
        pool: asyncpg.Pool
        user_id: int
        guild_id: int
        limit: int - 1日の上限回数

    Returns:
        bool: True=利用可能（カウント済み）、False=制限到達
    """
    async with pool.acquire() as conn:
        # UPSERT でカウントを確認・更新（アトミック操作）
        row = await conn.fetchrow(
            """
            INSERT INTO rate_limits (user_id, guild_id, date, count)
            VALUES ($1, $2, CURRENT_DATE, 1)
            ON CONFLICT (user_id, guild_id, date)
            DO UPDATE SET count = rate_limits.count + 1
            WHERE rate_limits.count < $3
            RETURNING count
            """,
            user_id,
            guild_id,
            limit,
        )

        if row is None:
            # WHERE句で弾かれた = 制限到達済み
            logger.info(f"Rate limit reached for user {user_id} in guild {guild_id}")
            return False

        logger.debug(f"Rate limit count for user {user_id}: {row['count']}/{limit}")
        return True


async def get_remaining(pool, user_id, guild_id, limit):
    """
    ユーザーの本日の残り回数を取得する。

    Args:
        pool: asyncpg.Pool
        user_id: int
        guild_id: int
        limit: int - 1日の上限回数

    Returns:
        int: 残り回数
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT count FROM rate_limits
            WHERE user_id = $1 AND guild_id = $2 AND date = CURRENT_DATE
            """,
            user_id,
            guild_id,
        )

        if row is None:
            return limit

        return max(0, limit - row["count"])
