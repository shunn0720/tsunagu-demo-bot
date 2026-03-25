"""
つなぐラボ デモサーバーBot - 学習記録
AI応答完了後の自動記録・#学習記録への投稿・サマリコマンド
"""

import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands
from discord import app_commands

from config import COLOR_EDUCATION, EMBED_FOOTER
from utils.embed_builder import education_embed

logger = logging.getLogger("tsunagu-bot.study_log")

STUDY_LOG_CHANNEL_NAME = "学習記録"


class StudyLog(commands.Cog):
    """学習記録の管理・投稿・集計"""

    def __init__(self, bot):
        self.bot = bot

    async def log_study(self, pool, user_id, user_name, question, subject, channel_id, guild_id):
        """
        学習記録をDBに保存し、#学習記録チャンネルにミニEmbedを投稿する。

        Args:
            pool: asyncpg.Pool
            user_id: int
            user_name: str
            question: str
            subject: str
            channel_id: int
            guild_id: int
        """
        # DBに保存
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO study_logs (user_id, user_name, question, subject, channel_id, guild_id)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    user_id,
                    user_name,
                    question,
                    subject,
                    channel_id,
                    guild_id,
                )
            logger.info(f"Logged study: user={user_name}, subject={subject}")
        except Exception as e:
            logger.error(f"Failed to log study: {e}", exc_info=True)
            return

        # #学習記録チャンネルにミニEmbed投稿
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        log_channel = discord.utils.get(guild.text_channels, name=STUDY_LOG_CHANNEL_NAME)
        if not log_channel:
            return

        now = datetime.now(timezone.utc)
        embed = discord.Embed(
            title="📖 学習記録",
            color=COLOR_EDUCATION,
        )
        embed.add_field(name="ユーザー", value=user_name, inline=True)
        embed.add_field(name="教科", value=subject, inline=True)
        embed.add_field(
            name="時刻",
            value=discord.utils.format_dt(now, "T"),
            inline=True,
        )
        embed.set_footer(text=EMBED_FOOTER)

        try:
            await log_channel.send(embed=embed)
        except discord.HTTPException as e:
            logger.error(f"Failed to post study log embed: {e}")

    @app_commands.command(name="study-summary", description="学習記録の日次・週次サマリを表示します")
    async def study_summary(self, interaction):
        """学習サマリを表示する"""
        await interaction.response.defer()

        if not self.bot.pool:
            await interaction.followup.send("データベースに接続できません。", ephemeral=True)
            return

        guild_id = interaction.guild_id

        async with self.bot.pool.acquire() as conn:
            # 今日の教科別集計
            daily_rows = await conn.fetch(
                """
                SELECT subject, COUNT(*) as cnt
                FROM study_logs
                WHERE guild_id = $1 AND created_at::date = CURRENT_DATE
                GROUP BY subject
                ORDER BY cnt DESC
                """,
                guild_id,
            )

            # 今週の教科別集計
            weekly_rows = await conn.fetch(
                """
                SELECT subject, COUNT(*) as cnt
                FROM study_logs
                WHERE guild_id = $1
                  AND created_at >= date_trunc('week', CURRENT_DATE)
                GROUP BY subject
                ORDER BY cnt DESC
                """,
                guild_id,
            )

            # 今日の合計
            daily_total = await conn.fetchval(
                """
                SELECT COUNT(*) FROM study_logs
                WHERE guild_id = $1 AND created_at::date = CURRENT_DATE
                """,
                guild_id,
            )

            # 今週の合計
            weekly_total = await conn.fetchval(
                """
                SELECT COUNT(*) FROM study_logs
                WHERE guild_id = $1
                  AND created_at >= date_trunc('week', CURRENT_DATE)
                """,
                guild_id,
            )

        # テキストバーチャート生成
        def bar_chart(rows, total):
            if not rows or total == 0:
                return "まだ記録がありません"
            lines = []
            max_count = max(r["cnt"] for r in rows)
            for row in rows:
                subject = row["subject"] or "その他"
                cnt = row["cnt"]
                bar_len = int((cnt / max_count) * 10) if max_count > 0 else 0
                bar = "█" * bar_len + "░" * (10 - bar_len)
                lines.append(f"`{subject:　<4}` {bar} **{cnt}**回")
            return "\n".join(lines)

        embed = discord.Embed(
            title="📊 学習サマリ",
            color=COLOR_EDUCATION,
        )

        embed.add_field(
            name=f"📅 今日の学習（合計 {daily_total}回）",
            value=bar_chart(daily_rows, daily_total),
            inline=False,
        )

        embed.add_field(
            name=f"📆 今週の学習（合計 {weekly_total}回）",
            value=bar_chart(weekly_rows, weekly_total),
            inline=False,
        )

        embed.set_footer(text=EMBED_FOOTER)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(StudyLog(bot))
