"""
つなぐラボ デモサーバーBot - ダッシュボード
/dashboard コマンドで利用状況をEmbed集計表示する
"""

import logging

import discord
from discord.ext import commands
from discord import app_commands

from config import COLOR_WELFARE, EMBED_FOOTER

logger = logging.getLogger("tsunagu-bot.dashboard")


def _has_staff_role():
    """スタッフ以上のロールチェック"""
    async def predicate(interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        staff_role = discord.utils.get(interaction.guild.roles, name="スタッフ")
        if staff_role and staff_role in interaction.user.roles:
            return True
        admin_role = discord.utils.get(interaction.guild.roles, name="管理者")
        if admin_role and admin_role in interaction.user.roles:
            return True
        raise app_commands.MissingPermissions(["スタッフ以上のロールが必要です"])
    return app_commands.check(predicate)


class Dashboard(commands.Cog):
    """利用状況ダッシュボード"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dashboard", description="利用状況ダッシュボードを表示します")
    @_has_staff_role()
    async def dashboard(self, interaction):
        """ダッシュボードを表示する（スタッフ以上）"""
        await interaction.response.defer()

        if not self.bot.pool:
            await interaction.followup.send("データベースに接続できません。", ephemeral=True)
            return

        guild_id = interaction.guild_id

        async with self.bot.pool.acquire() as conn:
            # 今日のAI利用回数
            daily_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM study_logs
                WHERE guild_id = $1 AND created_at::date = CURRENT_DATE
                """,
                guild_id,
            )

            # 今週の教科別質問数
            weekly_subjects = await conn.fetch(
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

            # アクティブユーザー数（直近7日）
            active_users = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT user_id) FROM study_logs
                WHERE guild_id = $1
                  AND created_at >= NOW() - INTERVAL '7 days'
                """,
                guild_id,
            )

        # サーバー参加者数
        member_count = interaction.guild.member_count

        # 教科別バーチャート
        def subject_chart(rows):
            if not rows:
                return "まだ記録がありません"
            lines = []
            max_cnt = max(r["cnt"] for r in rows)
            for row in rows:
                subj = row["subject"] or "その他"
                cnt = row["cnt"]
                bar_len = int((cnt / max_cnt) * 10) if max_cnt > 0 else 0
                bar = "\u2588" * bar_len + "\u2591" * (10 - bar_len)
                lines.append(f"`{subj:　<4}` {bar} **{cnt}**回")
            return "\n".join(lines)

        embed = discord.Embed(
            title="\U0001f4ca ダッシュボード",
            color=COLOR_WELFARE,
        )

        embed.add_field(
            name="\U0001f4c5 今日のAI利用回数",
            value=f"**{daily_count}** 回",
            inline=True,
        )

        embed.add_field(
            name="\U0001f465 アクティブユーザー（7日間）",
            value=f"**{active_users}** 人",
            inline=True,
        )

        embed.add_field(
            name="\U0001f30d サーバー参加者数",
            value=f"**{member_count}** 人",
            inline=True,
        )

        embed.add_field(
            name="\U0001f4c6 今週の教科別質問数",
            value=subject_chart(weekly_subjects),
            inline=False,
        )

        embed.set_footer(text=EMBED_FOOTER)
        await interaction.followup.send(embed=embed)

    @dashboard.error
    async def dashboard_error(self, interaction, error):
        """ダッシュボードのエラーハンドリング"""
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "\u26d4 このコマンドはスタッフ以上のロールが必要です。",
                ephemeral=True,
            )
        else:
            logger.error(f"Dashboard error: {error}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "エラーが発生しました。管理者にお知らせください。",
                    ephemeral=True,
                )


async def setup(bot):
    await bot.add_cog(Dashboard(bot))
