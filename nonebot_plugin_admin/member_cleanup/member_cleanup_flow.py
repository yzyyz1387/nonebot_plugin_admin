from __future__ import annotations

import asyncio
import datetime
from random import randint
from typing import Any, Awaitable, Callable, Sequence

from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.exception import ActionFailed

SleepFunc = Callable[[float], Awaitable[None]]
RandomFunc = Callable[[int, int], int]

CANCEL_WORDS = frozenset({"取消", "算了", "退出", "结束"})


def should_cancel(arg: str) -> bool:
    """
    处理 should_cancel 的业务逻辑
    :param arg: 参数值
    :return: bool
    """
    return arg in CANCEL_WORDS


def build_category_prompt(category: str) -> str:
    """
    构建categoryprompt
    :param category: category 参数
    :return: str
    """
    prompts = {
        "1": "等级(数字)：\n例如：2 则踢出等级 <= 2 的成员\n☆ 1 ☆ 4 ☆ = 16\n输入“取消”取消操作\n请等待...",
        "2": "最后发言时间(8位日期)：\n例如：20230912 则踢出 2023-09-12 后未发言的成员\n输入“取消”取消操作\n请等待...",
    }
    return prompts.get(category, "")


def build_cleanup_preview(kick_list: list[int], category: str, data_dict: dict[int, int]) -> str:
    """
    构建清理preview
    :param kick_list: 列表数据
    :param category: category 参数
    :param data_dict: data_dict 参数
    :return: str
    """
    prompt = {
        "1": ("将踢出等级 <= ", " 的成员：\n", "等级："),
        "2": ("将踢出在 ", " 之后未发言的成员：\n", "最后："),
    }
    title, suffix, label = prompt[category]
    send_text = f"{title}{category}{suffix}"
    if kick_list:
        for qq in kick_list:
            detail = data_dict[qq] if category == "1" else datetime.datetime.fromtimestamp(data_dict[qq])
            send_text += f"{qq}：{label}{detail}\n"
    else:
        send_text += "没有满足条件的成员，已取消操作。"
    return send_text


def _extract_member_level(info: dict[str, Any]) -> int:
    """
    处理 _extract_member_level 的业务逻辑
    :param info: info 参数
    :return: int
    """
    for key in ("level", "qqLevel", "qq_level"):
        value = info.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            logger.warning(f"成员等级字段无法解析: key={key} value={value!r}")
            return 0
    logger.warning(f"未在陌生人信息中找到等级字段，返回 0: keys={list(info.keys())}")
    return 0


async def get_member_levels(bot: Bot, user_ids: Sequence[int]) -> dict[int, int]:
    """
    获取成员levels
    :param bot: Bot 实例
    :param user_ids: 标识列表
    :return: dict[int, int]
    """
    levels: dict[int, int] = {}
    for user_id in user_ids:
        try:
            info = await bot.get_stranger_info(user_id=user_id, no_cache=True)
        except ActionFailed as err:
            logger.warning(f"获取成员 {user_id} 陌生人信息失败，按 0 级处理: {err}")
            levels[user_id] = 0
            continue
        except Exception as err:
            logger.warning(f"获取成员 {user_id} 等级信息异常，按 0 级处理: {type(err).__name__}: {err}")
            levels[user_id] = 0
            continue

        if not isinstance(info, dict):
            logger.warning(f"成员 {user_id} 的陌生人信息格式异常，按 0 级处理: {info!r}")
            levels[user_id] = 0
            continue

        levels[user_id] = _extract_member_level(info)
    return levels


def filter_members_by_level(levels: dict[int, int], threshold: int) -> tuple[list[int], list[int]]:
    """
    处理 filter_members_by_level 的业务逻辑
    :param levels: levels 参数
    :param threshold: threshold 参数
    :return: tuple[list[int], list[int]]
    """
    kick_list = [qq for qq, level in levels.items() if 0 < level <= threshold]
    zero_level_list = [qq for qq, level in levels.items() if level == 0]
    return kick_list, zero_level_list


def build_zero_level_notice(zero_level_list: list[int]) -> str:
    """
    构建zerolevel通知
    :param zero_level_list: 列表数据
    :return: str
    """
    if not zero_level_list:
        return ""
    send_text = "0级成员：\n"
    send_text += " ".join(str(qq) for qq in zero_level_list)
    send_text += "\n0级成员可能是未获取到等级信息，不做处理\n"
    return send_text


def extract_last_sent_times(member_list: Sequence[dict]) -> dict[int, int]:
    """
    处理 extract_last_sent_times 的业务逻辑
    :param member_list: 列表数据
    :return: dict[int, int]
    """
    return {member["user_id"]: member["last_sent_time"] for member in member_list}


def parse_cleanup_date(raw_date: str) -> datetime.datetime:
    """
    解析清理date
    :param raw_date: raw_date 参数
    :return: datetime.datetime
    """
    if len(raw_date) != 8:
        raise ValueError("invalid_length")
    return datetime.datetime.strptime(raw_date, "%Y%m%d")


def filter_members_by_last_sent(last_sent_map: dict[int, int], input_time: datetime.datetime) -> list[int]:
    """
    处理 filter_members_by_last_sent 的业务逻辑
    :param last_sent_map: 映射数据
    :param input_time: input_time 参数
    :return: list[int]
    """
    kick_list: list[int] = []
    for qq, last_sent in last_sent_map.items():
        try:
            if datetime.datetime.fromtimestamp(last_sent) <= input_time:
                kick_list.append(qq)
        except ValueError:
            continue
    return kick_list


def should_abort_for_remaining(member_count: int, kick_count: int) -> bool:
    """
    处理 should_abort_for_remaining 的业务逻辑
    :param member_count: member_count 参数
    :param kick_count: kick_count 参数
    :return: bool
    """
    return member_count - kick_count <= 3


async def execute_member_cleanup(
    bot: Bot,
    group_id: int,
    operator_id: int,
    kick_list: Sequence[int],
    *,
    sleep_func: SleepFunc = asyncio.sleep,
    random_func: RandomFunc = randint,
) -> tuple[list[int], list[int]]:
    """
    处理 execute_member_cleanup 的业务逻辑
    :param bot: Bot 实例
    :param group_id: 群号
    :param operator_id: 标识值
    :param kick_list: 列表数据
    :param sleep_func: sleep_func 参数
    :param random_func: random_func 参数
    :return: tuple[list[int], list[int]]
    """
    success: list[int] = []
    fail: list[int] = []
    for qq in kick_list:
        try:
            await sleep_func(random_func(0, 5))
            await bot.set_group_kick(group_id=group_id, user_id=qq)
            success.append(qq)
        except ActionFailed:
            fail.append(qq)
    return success, fail
