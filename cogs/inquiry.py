"""
つなぐラボ デモサーバーBot - 導入相談チャンネル管理
#導入相談 へのメッセージを検知し、#bot-log に通知する
"""

import logging

import discord
from discord.ext import commands

from config import COLOR_NOTIFY, EMBED_FOOTER

logger = logging.getLogger("tsunagu-bot.inquiry")

INQUIRY_CHANNEL_NAME = "導入相談"
BOT_LOG_CHANNEL_NAME = "bot-log"


class Inquiry(commands.Cog):
    """導入相談チャンネルの監視・通知"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """#導入相談 チャンネルでのメッセージ検知"""
        # Bot自身のメッセージは無視
        if message.author.bot:
            return

        # DMは無視
        if not message.guild:
            return

        # #導入相談 チャンネルのみ対応
        if message.channel.name != INQUIRY_CHANNEL_NAME:
            return

        # 1. ユーザーの投稿にリアクション
        try:
            await message.add_reaction("\u2705")
        except discord.HTTPException as e:
            logger.error(f"Failed to add reaction: {e}")

        # 2. #bot-log に通知Embed
        bot_log = discord.utils.get(message.guild.text_channels, name=BOT_LOG_CHANNEL_NAME)
        if not bot_log:
            logger.warning(f"#{BOT_LOG_CHANNEL_NAME} channel not found")
            return

        # メッセージ冒頭50文字
        preview = message.content[:50]
        if len(message.content) > 50:
            preview += "..."

        embed = discord.Embed(
            title="\U0001f4e9 導入相談に新しいメッセージがあります",
            color=COLOR_NOTIFY,
        )
        embed.add_field(
            name="ユーザー",
            value=f"{message.author.display_name} ({message.author.mention})",
            inline=False,
        )
        embed.add_field(
            name="内容",
            value=preview if preview else "（テキストなし）",
            inline=False,
        )
        embed.add_field(
            name="リンク",
            value=f"[メッセージへ移動]({message.jump_url})",
            inline=False,
        )
        embed.set_footer(text=EMBED_FOOTER)

        try:
            await bot_log.send(embed=embed)
            logger.info(f"Inquiry notification sent for message by {message.author}")
        except discord.HTTPException as e:
            logger.error(f"Failed to send inquiry notification: {e}")


async def setup(bot):
    await bot.add_cog(Inquiry(bot))
