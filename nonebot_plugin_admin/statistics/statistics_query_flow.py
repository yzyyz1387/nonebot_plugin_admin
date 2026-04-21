from __future__ import annotations

from typing import Iterable

from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot


async def resolve_member_display_name(bot: Bot, group_id: int | str, user_id: int | str) -> str:
    """
    解析成员displayname
    :param bot: Bot 实例
    :param group_id: 群号
    :param user_id: 用户号
    :return: str
    """
    try:
        member = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
    except Exception as err:
        logger.warning(f"获取群成员信息失败，group_id={group_id}, user_id={user_id}, err={err}")
        return str(user_id)
    return member.get("card") or member.get("nickname") or str(user_id)


async def _filter_ranked_members(bot: Bot, group_id: int | str, stats: dict[str, int]) -> list[tuple[str, int]]:
    """
    处理 _filter_ranked_members 的业务逻辑
    :param bot: Bot 实例
    :param group_id: 群号
    :param stats: stats 参数
    :return: list[tuple[str, int]]
    """
    ranked_stats = sorted(((str(user_id), int(count)) for user_id, count in stats.items()), key=lambda item: item[1], reverse=True)
    if not ranked_stats:
        return []

    try:
        members = await bot.get_group_member_list(group_id=int(group_id))
    except Exception as err:
        logger.warning(f"获取群成员列表失败，group_id={group_id}, err={err}")
        return ranked_stats

    member_ids = {str(member.get('user_id')) for member in members}
    return [item for item in ranked_stats if item[0] in member_ids]


async def build_top_speaker_message(bot: Bot, group_id: int | str, stats: dict[str, int]) -> str | None:
    """
    构建topspeaker消息
    :param bot: Bot 实例
    :param group_id: 群号
    :param stats: stats 参数
    :return: str | None
    """
    ranked_stats = await _filter_ranked_members(bot, group_id, stats)
    if not ranked_stats:
        return None
    user_id, count = ranked_stats[0]
    nickname = await resolve_member_display_name(bot, group_id, user_id)
    return f"太强了！今日榜首：\n{nickname}，发了{count}条消息"


async def build_ranking_message(bot: Bot, group_id: int | str, stats: dict[str, int], limit: int = 10) -> str | None:
    """
    构建ranking消息
    :param bot: Bot 实例
    :param group_id: 群号
    :param stats: stats 参数
    :param limit: 数量限制
    :return: str | None
    """
    ranked_stats = await _filter_ranked_members(bot, group_id, stats)
    if not ranked_stats:
        return None
    lines: list[str] = []
    for index, (user_id, count) in enumerate(ranked_stats[:limit], start=1):
        nickname = await resolve_member_display_name(bot, group_id, user_id)
        lines.append(f"{index}. {nickname}，发了{count}条消息")
    return "\n".join(lines)


async def build_member_count_messages(
    bot: Bot,
    group_id: int | str,
    stats: dict[str, int],
    user_ids: Iterable[int | str],
    *,
    today: bool,
) -> list[str]:
    """
    构建成员count消息
    :param bot: Bot 实例
    :param group_id: 群号
    :param stats: stats 参数
    :param user_ids: 标识列表
    :param today: 是否按今日统计
    :return: list[str]
    """
    messages: list[str] = []
    for user_id in user_ids:
        nickname = await resolve_member_display_name(bot, group_id, user_id)
        normalized_user_id = str(user_id)
        if normalized_user_id in stats:
            count = stats[normalized_user_id]
            if today:
                messages.append(f"今天{nickname}发了{count}条消息")
            else:
                messages.append(f"有记录以来{nickname}在本群发了{count}条消息")
        else:
            if today:
                messages.append(f"今天{nickname}没有发消息")
            else:
                messages.append(f"{nickname}没有发消息")
    return messages
