from __future__ import annotations

from collections.abc import Iterable

from nonebot import logger
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import ActionFailed, Bot

from .broadcast_store import get_excluded_groups
from .broadcast_text import format_broadcast_preview, format_excluded_group_list, format_group_list

CANCEL_WORDS = {"取消", "算了", "退出"}
CONFIRM_WORDS = {"确认", "确定", "发送", "开始"}


def is_cancel_input(text: str) -> bool:
    """
    处理 is_cancel_input 的业务逻辑
    :param text: 文本内容
    :return: bool
    """
    return text.strip() in CANCEL_WORDS


def is_confirm_input(text: str) -> bool:
    """
    处理 is_confirm_input 的业务逻辑
    :param text: 文本内容
    :return: bool
    """
    return text.strip() in CONFIRM_WORDS


def normalize_group_tokens(raw_text: str) -> list[str]:
    """
    规范化群tokens
    :param raw_text: 文本内容
    :return: list[str]
    """
    return [token for token in str(raw_text).split() if token]


def build_message_preview(message: Message, limit: int = 200) -> str:
    """
    构建消息preview
    :param message: 消息内容
    :param limit: 数量限制
    :return: str
    """
    text = str(message).strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


async def fetch_group_catalog(bot: Bot) -> list[dict]:
    """
    拉取群catalog
    :param bot: Bot 实例
    :return: list[dict]
    """
    groups = await bot.get_group_list()
    return [
        {
            "group_id": int(group["group_id"]),
            "group_name": group["group_name"],
        }
        for group in groups
    ]


async def prepare_broadcast_preview(bot: Bot, user_id: str, message: Message, superusers: Iterable[str]) -> dict:
    """
    处理 prepare_broadcast_preview 的业务逻辑
    :param bot: Bot 实例
    :param user_id: 用户号
    :param message: 消息内容
    :param superusers: 超管列表
    :return: dict
    """
    groups = await fetch_group_catalog(bot)
    excluded_ids = set(await get_excluded_groups(user_id, superusers))
    target_groups = [group for group in groups if str(group["group_id"]) not in excluded_ids]
    excluded_groups = [group for group in groups if str(group["group_id"]) in excluded_ids]
    preview_text = format_broadcast_preview(
        build_message_preview(message),
        target_groups,
        excluded_groups,
    )
    return {
        "text": preview_text,
        "target_groups": target_groups,
        "excluded_groups": excluded_groups,
    }


async def get_excluded_group_list_message(bot: Bot, excluded_group_ids: list[str]) -> str:
    """
    获取excluded群list消息
    :param bot: Bot 实例
    :param excluded_group_ids: 标识列表
    :return: str
    """
    groups = await fetch_group_catalog(bot)
    groups_by_id = {str(group["group_id"]): group for group in groups}
    ordered_groups = [groups_by_id[group_id] for group_id in excluded_group_ids if group_id in groups_by_id]
    return format_excluded_group_list(ordered_groups)


async def get_group_list_message(bot: Bot) -> tuple[str, list[str]]:
    """
    获取群list消息
    :param bot: Bot 实例
    :return: tuple[str, list[str]]
    """
    groups = await fetch_group_catalog(bot)
    return format_group_list(groups), [str(group["group_id"]) for group in groups]


async def execute_broadcast(bot: Bot, target_groups: list[dict], message: Message) -> tuple[list[int], list[int]]:
    """
    处理 execute_broadcast 的业务逻辑
    :param bot: Bot 实例
    :param target_groups: target_groups 参数
    :param message: 消息内容
    :return: tuple[list[int], list[int]]
    """
    success: list[int] = []
    failed: list[int] = []
    for group in target_groups:
        group_id = int(group["group_id"])
        try:
            logger.debug("正在向群 %s 广播 %s", group_id, message)
            await bot.send_group_msg(group_id=group_id, message="广播：")
            await bot.send_group_msg(group_id=group_id, message=message)
            success.append(group_id)
        except ActionFailed as err:
            logger.error("广播到群 %s 失败: %s", group_id, err)
            failed.append(group_id)
    return success, failed
