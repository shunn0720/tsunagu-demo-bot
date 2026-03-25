"""
つなぐラボ デモサーバーBot - 自習サポートBot（コア機能）
#自習サポート チャンネルでのAI質問応答
"""

import logging
import os

import discord
from discord.ext import commands
from discord import ui

from config import (
    COLOR_EDUCATION,
    COLOR_ERROR,
    EMBED_FOOTER,
    ENV_DAILY_QUESTION_LIMIT,
    DEFAULT_DAILY_QUESTION_LIMIT,
)
from utils.ai_client import generate_study_response
from utils.rate_limiter import check_and_increment, get_remaining
from utils.embed_builder import education_embed, error_embed

logger = logging.getLogger("tsunagu-bot.study")

STUDY_CHANNEL_NAME = "自習サポート"
RATE_LIMIT_MESSAGE = "今日はたくさん勉強したね！また明日も待ってるよ 💪"


def _get_daily_limit():
    """環境変数から日次制限を取得"""
    try:
        return int(os.environ.get(ENV_DAILY_QUESTION_LIMIT, DEFAULT_DAILY_QUESTION_LIMIT))
    except ValueError:
        return DEFAULT_DAILY_QUESTION_LIMIT


async def _build_history(channel, bot_user, limit=5):
    """
    チャンネルから直近の会話履歴を取得する。
    limit往復分（= limit*2 メッセージ）を取得。
    """
    history = []
    messages = []

    async for msg in channel.history(limit=limit * 2 + 5):
        if msg.author.bot and msg.author != bot_user:
            continue
        messages.append(msg)

    # 古い順に並べる
    messages.reverse()

    # 直近limit往復を抽出
    pairs = []
    i = 0
    while i < len(messages) - 1:
        if not messages[i].author.bot and messages[i + 1].author == bot_user:
            pairs.append((messages[i], messages[i + 1]))
            i += 2
        else:
            i += 1

    # 最新limit往復のみ
    for user_msg, bot_msg in pairs[-limit:]:
        history.append({"role": "user", "text": user_msg.content})
        # Bot応答からEmbedのdescriptionを取得（Embed応答の場合）
        if bot_msg.embeds:
            history.append({"role": "model", "text": bot_msg.embeds[0].description or ""})
        else:
            history.append({"role": "model", "text": bot_msg.content})

    return history


async def _handle_study_question(bot, channel, user, question):
    """自習サポートの質問処理（共通ロジック）"""
    guild = channel.guild
    daily_limit = _get_daily_limit()

    # レート制限チェック
    allowed = await check_and_increment(bot.pool, user.id, guild.id, daily_limit)
    if not allowed:
        embed = education_embed(
            title="📚 今日の自習おつかれさま！",
            description=RATE_LIMIT_MESSAGE,
        )
        await channel.send(embed=embed, reference=None)
        return

    # タイピング表示
    async with channel.typing():
        # 会話履歴を取得
        history = await _build_history(channel, bot.user, limit=5)

        # AI応答生成
        result = await generate_study_response(question, history)

    subject = result.get("subject", "その他")
    response_text = result.get("response", "")

    # 残り回数を取得
    remaining = await get_remaining(bot.pool, user.id, guild.id, daily_limit)

    # 応答Embed
    embed = education_embed(
        title="💡 自習サポート",
        description=response_text,
    )
    embed.set_footer(text=f"残り{remaining}回 / {daily_limit}回｜{EMBED_FOOTER}")
    await channel.send(embed=embed)

    # 学習記録を保存
    study_log_cog = bot.get_cog("StudyLog")
    if study_log_cog:
        await study_log_cog.log_study(
            pool=bot.pool,
            user_id=user.id,
            user_name=user.display_name,
            question=question,
            subject=subject,
            channel_id=channel.id,
            guild_id=guild.id,
        )


# =============================================================================
# 質問モーダル
# =============================================================================

class StudyQuestionModal(ui.Modal, title="📝 質問する"):
    """自習サポート用の質問入力モーダル"""

    question = ui.TextInput(
        label="質問内容",
        style=discord.TextStyle.paragraph,
        placeholder="わからないことを書いてね（例: 二次方程式の解き方がわかりません）",
        max_length=500,
    )

    async def on_submit(self, interaction):
        await interaction.response.defer()
        bot = interaction.client
        channel = interaction.channel
        user = interaction.user
        await _handle_study_question(bot, channel, user, self.question.value)


# =============================================================================
# 質問ボタン PersistentView
# =============================================================================

class StudyView(ui.View):
    """自習サポートの質問ボタン（PersistentView）"""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="📝 質問する",
        style=discord.ButtonStyle.success,
        custom_id="study_question_btn",
    )
    async def study_question(self, interaction, button):
        await interaction.response.send_modal(StudyQuestionModal())


# =============================================================================
# Study Cog
# =============================================================================

class Study(commands.Cog):
    """自習サポートBot（コア機能）"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        """Cog読み込み時にPersistentViewを登録"""
        self.bot.add_view(StudyView())

    @commands.Cog.listener()
    async def on_message(self, message):
        """#自習サポート チャンネルでのメッセージ検知"""
        # Bot自身のメッセージは無視
        if message.author.bot:
            return

        # DMは無視
        if not message.guild:
            return

        # #自習サポート チャンネルのみ対応
        if message.channel.name != STUDY_CHANNEL_NAME:
            return

        # コマンドプレフィックスで始まるメッセージは無視
        if message.content.startswith(self.bot.command_prefix):
            return

        # DB接続チェック
        if not self.bot.pool:
            embed = error_embed(
                title="⚠️ エラー",
                description="データベースに接続できません。管理者にお知らせください。",
            )
            await message.channel.send(embed=embed)
            return

        try:
            await _handle_study_question(
                self.bot, message.channel, message.author, message.content
            )
        except Exception as e:
            logger.error(f"Study handler error: {e}", exc_info=True)
            embed = error_embed(
                title="⚠️ エラー",
                description="ごめんね、ちょっと調子が悪いみたい。もう一度試してみてね",
            )
            await message.channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Study(bot))
