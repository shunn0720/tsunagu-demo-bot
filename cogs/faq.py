"""
つなぐラボ デモサーバーBot - FAQ応答
FAQView は cogs/setup_server.py で定義済み。
このCogではPersistentViewの再登録のみ行う。
"""

import logging

from discord.ext import commands

from cogs.setup_server import FAQView

logger = logging.getLogger("tsunagu-bot.faq")


class FAQ(commands.Cog):
    """FAQ PersistentView の再登録用Cog"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        """Cog読み込み時にPersistentViewを再登録（Bot再起動対応）"""
        self.bot.add_view(FAQView())
        logger.info("FAQView registered")


async def setup(bot):
    await bot.add_cog(FAQ(bot))
