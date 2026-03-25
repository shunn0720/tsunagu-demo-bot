"""
つなぐラボ デモサーバーBot - Embed生成ユーティリティ
用途別のEmbed色を統一管理し、共通フッターを設定する
"""

from typing import Optional

import discord

from config import (
    COLOR_EDUCATION,
    COLOR_WELFARE,
    COLOR_NOTIFY,
    COLOR_SUCCESS,
    COLOR_ERROR,
    EMBED_FOOTER,
)


def _build_embed(
    color: int,
    title: str,
    description: Optional[str] = None,
    fields: Optional[list[dict]] = None,
) -> discord.Embed:
    """共通のEmbed生成処理"""
    embed = discord.Embed(title=title, color=color)

    if description:
        embed.description = description

    if fields:
        for field in fields:
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", False),
            )

    embed.set_footer(text=EMBED_FOOTER)
    return embed


def education_embed(
    title: str,
    description: Optional[str] = None,
    fields: Optional[list[dict]] = None,
) -> discord.Embed:
    """教育系Embed（ピンク: 0xffc6e2）"""
    return _build_embed(COLOR_EDUCATION, title, description, fields)


def welfare_embed(
    title: str,
    description: Optional[str] = None,
    fields: Optional[list[dict]] = None,
) -> discord.Embed:
    """福祉系Embed（ラベンダー: 0xc6c6ff）"""
    return _build_embed(COLOR_WELFARE, title, description, fields)


def notify_embed(
    title: str,
    description: Optional[str] = None,
    fields: Optional[list[dict]] = None,
) -> discord.Embed:
    """通知・警告Embed（イエロー: 0xffffc6）"""
    return _build_embed(COLOR_NOTIFY, title, description, fields)


def success_embed(
    title: str,
    description: Optional[str] = None,
    fields: Optional[list[dict]] = None,
) -> discord.Embed:
    """成功Embed（ティール: 0x4ECDC4）"""
    return _build_embed(COLOR_SUCCESS, title, description, fields)


def error_embed(
    title: str,
    description: Optional[str] = None,
    fields: Optional[list[dict]] = None,
) -> discord.Embed:
    """エラーEmbed（レッド: 0xFF6B6B）"""
    return _build_embed(COLOR_ERROR, title, description, fields)
