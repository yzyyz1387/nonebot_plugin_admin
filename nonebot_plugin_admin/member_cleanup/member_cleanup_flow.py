from __future__ import annotations

import asyncio
import datetime
import unicodedata
from random import randint
from typing import Any, Awaitable, Callable, Sequence

from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.exception import ActionFailed

SleepFunc = Callable[[float], Awaitable[None]]
RandomFunc = Callable[[int, int], int]
ProgressFunc = Callable[[int, int], Awaitable[None]]

CANCEL_WORDS = frozenset({"取消", "算了", "退出", "结束"})
GROUP_LEVEL_KEYS = ("level",)
QQ_LEVEL_KEYS = ("qq_level", "qqLevel")


def should_cancel(arg: str) -> bool:
    """
    处理 should_cancel 的业务逻辑
    :param arg: 参数值
    :return: bool
    """
    return arg in CANCEL_WORDS


def build_protected_member_ids(member_list: Sequence[dict], bot_id: int | str, superusers: Sequence[int | str]) -> set[str]:
    """
    构建受保护成员集合
    :param member_list: 成员列表
    :param bot_id: 机器人号
    :param superusers: 超管列表
    :return: set[str]
    """
    protected: set[str] = set()
    superuser_ids = {str(user_id) for user_id in superusers}
    bot_id_text = str(bot_id)
    for member in member_list:
        user_id = member.get("user_id")
        if user_id is None:
            continue
        user_id_text = str(user_id)
        role = str(member.get("role") or "")
        if role in {"owner", "admin"} or member.get("is_robot") or user_id_text == bot_id_text or user_id_text in superuser_ids:
            protected.add(user_id_text)
    return protected


def get_targetable_member_ids(member_list: Sequence[dict], bot_id: int | str, superusers: Sequence[int | str]) -> list[int]:
    """
    获取可清理成员 ID
    :param member_list: 成员列表
    :param bot_id: 机器人号
    :param superusers: 超管列表
    :return: list[int]
    """
    protected = build_protected_member_ids(member_list, bot_id, superusers)
    targetable: list[int] = []
    seen: set[str] = set()
    for member in member_list:
        user_id = member.get("user_id")
        if user_id is None:
            continue
        user_id_text = str(user_id)
        if user_id_text in protected or user_id_text in seen:
            continue
        try:
            targetable.append(int(user_id))
            seen.add(user_id_text)
        except (TypeError, ValueError):
            logger.warning(f"成员 user_id 无法解析，已跳过: {user_id!r}")
    return targetable


def parse_cleanup_exclusions(raw_text: str, total: int) -> list[int] | None:
    """
    解析清理排除序号
    :param raw_text: 原始文本
    :param total: 可选总数
    :return: 排除序号列表，无法解析时返回 None
    """
    text = unicodedata.normalize("NFKC", raw_text).strip()
    if text in {"0", "确认", "确定", "执行", "是", "好", "好的"}:
        return []
    parts = [part.strip() for part in text.split(",")]
    if not parts or any(not part.isdigit() for part in parts):
        return None

    numbers: list[int] = []
    for part in parts:
        number = int(part)
        if number < 1 or number > total:
            return None
        if number not in numbers:
            numbers.append(number)
    return numbers


def build_category_prompt(category: str) -> str:
    """
    构建categoryprompt
    :param category: category 参数
    :return: str
    """
    prompts = {
        "1": "群聊等级(数字)：\n例如：2 则踢出群聊等级 <= 2 的成员\n输入“取消”取消操作\n请等待...",
        "2": "QQ等级(数字)：\n例如：16 则踢出 QQ等级 <= 16 的成员\n⭐=1，🌙=4，☀️=16\n输入“取消”取消操作\n请等待...",
        "3": "最后发言时间(8位日期)：\n例如：20230912 则踢出 2023-09-12 后未发言的成员\n输入“取消”取消操作\n请等待...",
    }
    return prompts.get(category, "")


def build_cleanup_preview(kick_list: list[int], category: str, data_dict: dict[int, int], condition: str) -> str:
    """
    构建清理preview
    :param kick_list: 列表数据
    :param category: category 参数
    :param data_dict: data_dict 参数
    :param condition: 条件文本
    :return: str
    """
    prompt = {
        "1": ("将踢出群聊等级 <= ", " 的成员：\n", "群聊等级："),
        "2": ("将踢出 QQ等级 <= ", " 的成员：\n", "QQ等级："),
        "3": ("将踢出在 ", " 之后未发言的成员：\n", "最后："),
    }
    title, suffix, label = prompt[category]
    send_text = f"{title}{condition}{suffix}"
    if kick_list:
        for qq in kick_list:
            detail = data_dict[qq] if category in ("1", "2") else datetime.datetime.fromtimestamp(data_dict[qq])
            send_text += f"{qq}：{label}{detail}\n"
    else:
        send_text += "没有满足条件的成员，已取消操作。"
    return send_text


def _extract_int_field(info: dict[str, Any], keys: Sequence[str], field_name: str) -> int | None:
    """
    处理 _extract_int_field 的业务逻辑
    :param info: info 参数
    :param keys: 字段名列表
    :param field_name: 字段显示名
    :return: int | None
    """
    for key in keys:
        value = info.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            logger.warning(f"成员{field_name}字段无法解析: key={key} value={value!r}")
            return None
    logger.warning(f"未在群成员信息中找到{field_name}字段: keys={list(info.keys())}")
    return None


async def get_member_info_map(
    bot: Bot,
    group_id: int,
    user_ids: Sequence[int],
    *,
    progress_callback: ProgressFunc | None = None,
    progress_interval: float = 15.0,
) -> dict[int, dict[str, Any]]:
    """
    获取群成员详情映射
    :param bot: Bot 实例
    :param group_id: 群号
    :param user_ids: 标识列表
    :param progress_callback: 查询进度回调
    :param progress_interval: 进度回调间隔秒数
    :return: dict[int, dict[str, Any]]
    """
    infos: dict[int, dict[str, Any]] = {}
    total = len(user_ids)
    loop = asyncio.get_running_loop()
    last_progress = loop.time()
    for index, user_id in enumerate(user_ids, start=1):
        info = None
        try:
            info = await bot.get_group_member_info(group_id=group_id, user_id=user_id, no_cache=True)
        except ActionFailed as err:
            logger.warning(f"获取成员 {user_id} 群成员信息失败: {err}")
        except Exception as err:
            logger.warning(f"获取成员 {user_id} 群成员信息异常: {type(err).__name__}: {err}")

        if info is None:
            pass
        elif not isinstance(info, dict):
            logger.warning(f"成员 {user_id} 的群成员信息格式异常: {info!r}")
        else:
            infos[user_id] = info

        now = loop.time()
        if progress_callback and (index == total or now - last_progress >= progress_interval):
            await progress_callback(index, total)
            last_progress = now
    return infos


async def get_member_levels(
    bot: Bot,
    group_id: int,
    user_ids: Sequence[int],
    *,
    level_keys: Sequence[str] = GROUP_LEVEL_KEYS,
    level_name: str = "等级",
) -> dict[int, int]:
    """
    获取成员levels
    :param bot: Bot 实例
    :param group_id: 群号
    :param user_ids: 标识列表
    :param level_keys: 等级字段名列表
    :param level_name: 等级名称
    :return: dict[int, int]
    """
    infos = await get_member_info_map(bot, group_id, user_ids)
    return extract_member_levels(infos, user_ids, level_keys=level_keys, level_name=level_name)


def extract_member_levels(
    infos: dict[int, dict[str, Any]],
    user_ids: Sequence[int],
    *,
    level_keys: Sequence[str] = GROUP_LEVEL_KEYS,
    level_name: str = "等级",
) -> dict[int, int]:
    """
    从群成员详情中提取等级
    :param infos: 群成员详情映射
    :param user_ids: 标识列表
    :param level_keys: 等级字段名列表
    :param level_name: 等级名称
    :return: dict[int, int]
    """
    levels: dict[int, int] = {}
    for user_id in user_ids:
        info = infos.get(user_id)
        if not info:
            levels[user_id] = 0
            continue
        levels[user_id] = _extract_int_field(info, level_keys, level_name) or 0
    return levels


async def get_member_last_sent_times(bot: Bot, group_id: int, user_ids: Sequence[int]) -> dict[int, int]:
    """
    获取成员最后发言时间
    :param bot: Bot 实例
    :param group_id: 群号
    :param user_ids: 标识列表
    :return: dict[int, int]
    """
    infos = await get_member_info_map(bot, group_id, user_ids)
    return extract_member_last_sent_times(infos)


def extract_member_last_sent_times(infos: dict[int, dict[str, Any]]) -> dict[int, int]:
    """
    从群成员详情中提取最后发言时间
    :param infos: 群成员详情映射
    :return: dict[int, int]
    """
    last_sent_map: dict[int, int] = {}
    for user_id, info in infos.items():
        last_sent = _extract_int_field(info, ("last_sent_time",), "最后发言时间")
        if last_sent is not None:
            last_sent_map[user_id] = last_sent
    return last_sent_map


def filter_members_by_level(levels: dict[int, int], threshold: int, *, include_zero: bool = False) -> tuple[list[int], list[int]]:
    """
    处理 filter_members_by_level 的业务逻辑
    :param levels: levels 参数
    :param threshold: threshold 参数
    :param include_zero: 是否处理 0 级
    :return: tuple[list[int], list[int]]
    """
    kick_list = [qq for qq, level in levels.items() if (include_zero or level > 0) and level <= threshold]
    zero_level_list = [] if include_zero else [qq for qq, level in levels.items() if level == 0]
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
