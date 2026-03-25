"""
つなぐラボ デモサーバーBot - メインエントリーポイント
discord.py v2.3.2+ / asyncpg / Cog自動読み込み
"""

import logging
import os

import asyncpg
import discord
from discord.ext import commands

# ローカル開発時のみ .env を読む（Railway上では不要）
if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()

from config import ENV_DISCORD_TOKEN, ENV_GUILD_ID, ENV_BOT_PREFIX, ENV_LOG_LEVEL
from config import DEFAULT_BOT_PREFIX, DEFAULT_LOG_LEVEL
from db import create_pool, init_tables

# ロギング設定
log_level = os.environ.get(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL)
logging.basicConfig(
    level=getattr(logging, log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tsunagu-bot")

# 読み込むCog一覧
COG_EXTENSIONS = [
    "cogs.setup_server",
    "cogs.welcome",
    "cogs.study",
    "cogs.study_log",
    "cogs.faq",
    "cogs.inquiry",
    "cogs.dashboard",
]


class TsunaguBot(commands.Bot):
    """つなぐラボ デモサーバーBot"""

    def __init__(self) -> None:
        prefix = os.environ.get(ENV_BOT_PREFIX, DEFAULT_BOT_PREFIX)
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(command_prefix=prefix, intents=intents)
        self.pool: asyncpg.Pool | None = None

    async def setup_hook(self) -> None:
        """Bot起動時の初期化処理"""
        # 1. DB接続 & テーブル作成
        logger.info("Connecting to database...")
        self.pool = await create_pool()
        await init_tables(self.pool)
        logger.info("Database initialized.")

        # 2. Cog読み込み
        for ext in COG_EXTENSIONS:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded extension: {ext}")
            except Exception as e:
                logger.error(f"Failed to load extension {ext}: {e}")

        # 3. PersistentView登録
        # 各Cogの cog_load / setup 内で bot.add_view() を呼ぶ設計

        # 4. スラッシュコマンド同期（guild同期）
        guild_id = os.environ.get(ENV_GUILD_ID)
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Synced command tree to guild {guild_id}")
        else:
            await self.tree.sync()
            logger.info("Synced command tree globally")

    async def close(self) -> None:
        """Bot終了時のクリーンアップ"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed.")
        await super().close()

    async def on_ready(self) -> None:
        """Bot起動完了時のログ出力"""
        logger.info(f"Bot is ready! Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")


def main() -> None:
    """エントリーポイント"""
    token = os.environ.get(ENV_DISCORD_TOKEN)
    if not token:
        raise RuntimeError(f"{ENV_DISCORD_TOKEN} is not set")

    bot = TsunaguBot()
    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()
