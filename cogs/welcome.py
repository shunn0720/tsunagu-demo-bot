"""
つなぐラボ デモサーバーBot - メンバー参加対応
on_member_join でロール自動付与・bot-log通知・DM送信
"""

import logging

import discord
from discord.ext import commands

from config import COLOR_NOTIFY, EMBED_FOOTER

logger = logging.getLogger("tsunagu-bot.welcome")


class Welcome(commands.Cog):
    """メンバー参加時のWelcome処理"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """メンバー参加時の処理"""
        guild = member.guild

        # ----------------------------------------------------------
        # 1. 「体験ユーザー」ロールを自動付与
        # ----------------------------------------------------------
        role = discord.utils.get(guild.roles, name="体験ユーザー")
        if role:
            try:
                await member.add_roles(role, reason="自動付与: メンバー参加")
                logger.info(f"Assigned role '体験ユーザー' to {member} ({member.id})")
            except discord.Forbidden:
                logger.warning(f"Failed to assign role to {member}: permission denied")
            except discord.HTTPException as e:
                logger.error(f"Failed to assign role to {member}: {e}")

        # ----------------------------------------------------------
        # 2. #bot-log に参加通知Embed
        # ----------------------------------------------------------
        bot_log = discord.utils.get(guild.text_channels, name="bot-log")
        if bot_log:
            embed = discord.Embed(
                title="\U0001f4e5 メンバー参加",
                description=f"**{member.display_name}** さんがデモサーバーに参加しました",
                color=COLOR_NOTIFY,
            )
            embed.add_field(
                name="ユーザー",
                value=f"{member.mention} ({member.id})",
                inline=False,
            )
            embed.add_field(
                name="アカウント作成日",
                value=discord.utils.format_dt(member.created_at, "R"),
                inline=False,
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=EMBED_FOOTER)
            try:
                await bot_log.send(embed=embed)
            except discord.HTTPException as e:
                logger.error(f"Failed to send join log: {e}")

        # ----------------------------------------------------------
        # 3. DM送信（失敗時はスキップ）
        # ----------------------------------------------------------
        dm_text = (
            "つなぐラボのデモサーバーへようこそ！\n"
            "まずは #自習サポート でAIに質問してみてください \U0001f4dd"
        )
        try:
            await member.send(dm_text)
            logger.info(f"Sent welcome DM to {member}")
        except (discord.Forbidden, discord.HTTPException):
            logger.info(f"Could not send DM to {member} (DM disabled or blocked)")


async def setup(bot):
    await bot.add_cog(Welcome(bot))
