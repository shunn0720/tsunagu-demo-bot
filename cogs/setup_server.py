"""
つなぐラボ デモサーバーBot - ワンコマンド一括構築
!setup コマンドでチャンネル・ロール・Embed・FAQを一括生成する
"""

import logging

import discord
from discord.ext import commands
from discord import ui

from config import (
    SERVER_NAME,
    ROLES,
    CATEGORIES,
    CHANNEL_PERMISSIONS,
    COLOR_EDUCATION,
    COLOR_WELFARE,
    COLOR_NOTIFY,
    COLOR_SUCCESS,
    EMBED_FOOTER,
    FAQ_ANSWERS,
)

logger = logging.getLogger("tsunagu-bot.setup")


# =============================================================================
# 権限ヘルパー
# =============================================================================

def _perm_overwrite(perm_type, is_voice=False):
    """config.pyの権限文字列をPermissionOverwriteに変換する"""
    if perm_type is None:
        return discord.PermissionOverwrite(
            view_channel=False,
        )
    if perm_type == "read":
        ow = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=False,
            add_reactions=False,
        )
        if is_voice:
            ow.connect = False
            ow.speak = False
        return ow
    if perm_type == "read_btn":
        return discord.PermissionOverwrite(
            view_channel=True,
            send_messages=False,
            add_reactions=False,
            use_external_emojis=True,
        )
    if perm_type == "read_send":
        return discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            add_reactions=True,
        )
    if perm_type == "vc":
        return discord.PermissionOverwrite(
            view_channel=True,
            connect=True,
            speak=True,
        )
    if perm_type == "all":
        return discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True,
            add_reactions=True,
            connect=True,
            speak=True,
            manage_permissions=True,
        )
    return discord.PermissionOverwrite()


def _build_overwrites(guild, channel_name, role_map):
    """チャンネル名に対応する権限オーバーライト辞書を構築する"""
    perms = CHANNEL_PERMISSIONS.get(channel_name, {})
    is_voice = channel_name == "声の教室"
    overwrites = {}

    # @everyone
    everyone_perm = perms.get("everyone")
    overwrites[guild.default_role] = _perm_overwrite(everyone_perm, is_voice)

    # 各ロール
    for role_name in ["体験ユーザー", "スタッフ", "管理者"]:
        perm_type = perms.get(role_name)
        role = role_map.get(role_name)
        if role:
            overwrites[role] = _perm_overwrite(perm_type, is_voice)

    return overwrites


# =============================================================================
# FAQ PersistentView（セクション6-3 / 7-5）
# =============================================================================

class FAQView(ui.View):
    """よくある質問のPersistentView（4ボタン、ephemeral応答）"""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Discordって何？", style=discord.ButtonStyle.primary, custom_id="faq_discord")
    async def faq_discord(self, interaction, button):
        await interaction.response.send_message(FAQ_ANSWERS["faq_discord"], ephemeral=True)

    @ui.button(label="AIって安全？", style=discord.ButtonStyle.primary, custom_id="faq_ai_safety")
    async def faq_ai_safety(self, interaction, button):
        await interaction.response.send_message(FAQ_ANSWERS["faq_ai_safety"], ephemeral=True)

    @ui.button(label="費用はかかる？", style=discord.ButtonStyle.primary, custom_id="faq_cost")
    async def faq_cost(self, interaction, button):
        await interaction.response.send_message(FAQ_ANSWERS["faq_cost"], ephemeral=True)

    @ui.button(label="導入は難しい？", style=discord.ButtonStyle.primary, custom_id="faq_difficulty")
    async def faq_difficulty(self, interaction, button):
        await interaction.response.send_message(FAQ_ANSWERS["faq_difficulty"], ephemeral=True)


# =============================================================================
# Embed生成（セクション6）
# =============================================================================

def _welcome_embed():
    """#ようこそ Embed（セクション6-1）"""
    embed = discord.Embed(
        title="\U0001f3e0 つなぐラボ デモサーバーへようこそ！",
        description=(
            "このサーバーは、教育・福祉の現場で使える\n"
            "「オンラインの居場所 \u00d7 AI」の体験版です。\n\n"
            "\U0001f539 実際にAIに質問してみる \u2192 #自習サポート\n"
            "\U0001f539 どんな機能があるか見る \u2192 #できること一覧\n"
            "\U0001f539 よくある疑問を確認  \u2192 #よくある質問\n"
            "\U0001f539 導入について相談する \u2192 #導入相談\n\n"
            "まずは気軽に触ってみてください！"
        ),
        color=COLOR_EDUCATION,
    )
    embed.set_footer(text=EMBED_FOOTER)
    return embed


def _education_embed():
    """#できること一覧 Embed 1: 教育支援（セクション6-2）"""
    embed = discord.Embed(
        title="\U0001f4da 教育支援での活用イメージ",
        color=COLOR_EDUCATION,
    )
    embed.add_field(
        name="自習サポート",
        value="AIがヒントを出しながら、生徒の自学自習を支えます。答えは出さず、考え方を導くスタイルです。",
        inline=False,
    )
    embed.add_field(
        name="学習記録の可視化",
        value="質問内容・教科・回数を自動記録。生徒の学習状況をスタッフが把握できます。",
        inline=False,
    )
    embed.add_field(
        name="オンライン自習室",
        value="ボイスチャンネルで「誰かがいる安心感」のある自習空間を作れます。",
        inline=False,
    )
    embed.set_footer(text=EMBED_FOOTER)
    return embed


def _welfare_embed():
    """#できること一覧 Embed 2: 福祉支援（セクション6-2）"""
    embed = discord.Embed(
        title="\U0001f91d 福祉支援での活用イメージ",
        color=COLOR_WELFARE,
    )
    embed.add_field(
        name="相談窓口",
        value="AIが一次対応し、必要に応じてスタッフに通知。24時間受付が可能に。",
        inline=False,
    )
    embed.add_field(
        name="お知らせ配信",
        value="施設からの連絡をテンプレートで簡単に配信。既読確認も可能です。",
        inline=False,
    )
    embed.add_field(
        name="活動記録",
        value="支援内容を簡易入力 \u2192 自動で記録化。報告書作成の手間を減らします。",
        inline=False,
    )
    embed.set_footer(text=EMBED_FOOTER)
    return embed


def _faq_embed():
    """#よくある質問 Embed（セクション6-3）"""
    embed = discord.Embed(
        title="\u2753 よくある質問",
        description="気になる項目のボタンを押してください。",
        color=COLOR_NOTIFY,
    )
    embed.set_footer(text=EMBED_FOOTER)
    return embed


# =============================================================================
# Setup Cog
# =============================================================================

class SetupServer(commands.Cog):
    """!setup でサーバーを一括構築するCog"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        """Cog読み込み時にPersistentViewを登録"""
        self.bot.add_view(FAQView())

    @commands.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        """サーバーを一括構築する（管理者のみ）"""
        guild = ctx.guild
        if not guild:
            return

        status_msg = await ctx.send(
            embed=discord.Embed(
                title="\u23f3 セットアップを開始します...",
                color=COLOR_NOTIFY,
            )
        )

        created_roles = []
        created_categories = []
        created_channels = []
        skipped = []

        try:
            # ----------------------------------------------------------
            # 1. サーバー名変更
            # ----------------------------------------------------------
            if guild.name != SERVER_NAME:
                await guild.edit(name=SERVER_NAME)
                logger.info(f"Server name changed to: {SERVER_NAME}")

            # ----------------------------------------------------------
            # 2. ロール作成（既存はスキップ）
            # ----------------------------------------------------------
            existing_role_names = {r.name for r in guild.roles}
            role_map = {}

            for role_def in ROLES:
                name = role_def["name"]
                if name in existing_role_names:
                    role_map[name] = discord.utils.get(guild.roles, name=name)
                    skipped.append(f"ロール: {name}")
                else:
                    role = await guild.create_role(
                        name=name,
                        color=discord.Color(role_def["color"]),
                        reason="!setup による一括構築",
                    )
                    role_map[name] = role
                    created_roles.append(name)
                    logger.info(f"Created role: {name}")

            # ----------------------------------------------------------
            # 3-5. カテゴリ・チャンネル作成 + 権限設定
            # ----------------------------------------------------------
            existing_cats = {c.name: c for c in guild.categories}
            existing_chs = {
                c.name: c for c in guild.channels
                if not isinstance(c, discord.CategoryChannel)
            }

            for cat_def in CATEGORIES:
                cat_name = cat_def["name"]

                # カテゴリ作成 or 既存取得
                if cat_name in existing_cats:
                    category = existing_cats[cat_name]
                    skipped.append(f"カテゴリ: {cat_name}")
                else:
                    category = await guild.create_category(
                        name=cat_name,
                        reason="!setup による一括構築",
                    )
                    created_categories.append(cat_name)
                    logger.info(f"Created category: {cat_name}")

                # チャンネル作成
                for ch_def in cat_def["channels"]:
                    ch_name = ch_def["name"]
                    ch_type = ch_def["type"]

                    if ch_name in existing_chs:
                        skipped.append(f"チャンネル: #{ch_name}")
                        # 既存チャンネルでも権限を更新
                        channel = existing_chs[ch_name]
                        overwrites = _build_overwrites(guild, ch_name, role_map)
                        await channel.edit(overwrites=overwrites)
                        continue

                    overwrites = _build_overwrites(guild, ch_name, role_map)

                    if ch_type == "voice":
                        channel = await guild.create_voice_channel(
                            name=ch_name,
                            category=category,
                            overwrites=overwrites,
                            reason="!setup による一括構築",
                        )
                    else:
                        channel = await guild.create_text_channel(
                            name=ch_name,
                            category=category,
                            overwrites=overwrites,
                            reason="!setup による一括構築",
                        )

                    created_channels.append(f"#{ch_name}")
                    logger.info(f"Created channel: #{ch_name} ({ch_type})")

            # ----------------------------------------------------------
            # 6. 初期Embed配置
            # ----------------------------------------------------------

            # #ようこそ
            welcome_ch = discord.utils.get(guild.text_channels, name="ようこそ")
            if welcome_ch:
                history = [m async for m in welcome_ch.history(limit=10)]
                bot_messages = [m for m in history if m.author == self.bot.user and m.embeds]
                if not bot_messages:
                    await welcome_ch.send(embed=_welcome_embed())
                    logger.info("Posted welcome embed")

            # #できること一覧（2枚）
            features_ch = discord.utils.get(guild.text_channels, name="できること一覧")
            if features_ch:
                history = [m async for m in features_ch.history(limit=10)]
                bot_messages = [m for m in history if m.author == self.bot.user and m.embeds]
                if not bot_messages:
                    await features_ch.send(embed=_education_embed())
                    await features_ch.send(embed=_welfare_embed())
                    logger.info("Posted feature embeds")

            # #よくある質問（FAQ PersistentView付き）
            faq_ch = discord.utils.get(guild.text_channels, name="よくある質問")
            if faq_ch:
                history = [m async for m in faq_ch.history(limit=10)]
                bot_messages = [m for m in history if m.author == self.bot.user and m.embeds]
                if not bot_messages:
                    await faq_ch.send(embed=_faq_embed(), view=FAQView())
                    logger.info("Posted FAQ embed with PersistentView")

            # ----------------------------------------------------------
            # 7. セットアップ状態をDBに記録
            # ----------------------------------------------------------
            if self.bot.pool:
                async with self.bot.pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO setup_state (guild_id, setup_completed, setup_at)
                        VALUES ($1, TRUE, NOW())
                        ON CONFLICT (guild_id)
                        DO UPDATE SET setup_completed = TRUE, setup_at = NOW()
                        """,
                        guild.id,
                    )

            # ----------------------------------------------------------
            # 8. 完了メッセージ
            # ----------------------------------------------------------
            summary_lines = []
            if created_roles:
                summary_lines.append(f"**ロール作成**: {', '.join(created_roles)}")
            if created_categories:
                summary_lines.append(f"**カテゴリ作成**: {', '.join(created_categories)}")
            if created_channels:
                summary_lines.append(f"**チャンネル作成**: {', '.join(created_channels)}")
            if skipped:
                summary_lines.append(f"**スキップ（既存）**: {len(skipped)}件")

            if not summary_lines:
                summary_lines.append("すべて作成済みのため、変更はありません。")

            complete_embed = discord.Embed(
                title="\u2705 セットアップ完了！",
                description="\n".join(summary_lines),
                color=COLOR_SUCCESS,
            )
            complete_embed.set_footer(text=EMBED_FOOTER)
            await status_msg.edit(embed=complete_embed)
            logger.info("Setup completed successfully")

        except Exception as e:
            logger.error(f"Setup failed: {e}", exc_info=True)
            error_embed = discord.Embed(
                title="\u274c セットアップ中にエラーが発生しました",
                description=f"```{e}```\n作成済みのものはそのまま残っています。再度 `!setup` を実行できます。",
                color=0xFF6B6B,
            )
            error_embed.set_footer(text=EMBED_FOOTER)
            await status_msg.edit(embed=error_embed)

    @setup.error
    async def setup_error(self, ctx, error):
        """!setup のエラーハンドリング"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="\u26d4 権限不足",
                description="このコマンドは管理者のみ実行できます。",
                color=0xFF6B6B,
            )
            embed.set_footer(text=EMBED_FOOTER)
            await ctx.send(embed=embed)
        else:
            logger.error(f"Setup command error: {error}", exc_info=True)


async def setup(bot):
    await bot.add_cog(SetupServer(bot))
