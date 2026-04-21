from __future__ import annotations

import datetime

from .config_orm_store import (
    orm_disable_group_record,
    orm_enable_group_record,
    orm_is_group_record_enabled,
    orm_load_daily_message_stats,
    orm_load_history_message_stats,
    orm_load_record_setting_groups,
)


def _normalize_group_id(group_id: int | str) -> str:
    """
    规范化群id
    :param group_id: 群号
    :return: str
    """
    return str(group_id)


def _normalize_date(day: datetime.date | str | None = None) -> str:
    """
    规范化date
    :param day: day 参数
    :return: str
    """
    if day is None:
        return datetime.date.today().strftime("%Y-%m-%d")
    if isinstance(day, str):
        return day
    return day.strftime("%Y-%m-%d")


async def load_runtime_record_setting_groups() -> list[str]:
    """
    加载运行时记录setting群组
    :return: list[str]
    """
    return [str(group_id) for group_id in await orm_load_record_setting_groups()]


async def is_group_record_enabled(group_id: int | str) -> bool:
    """
    处理 is_group_record_enabled 的业务逻辑
    :param group_id: 群号
    :return: bool
    """
    normalized_group_id = _normalize_group_id(group_id)
    orm_result = await orm_is_group_record_enabled(normalized_group_id)
    if orm_result is None:
        return True
    return orm_result


async def enable_group_record(group_id: int | str) -> bool:
    """
    记录enable群
    :param group_id: 群号
    :return: bool
    """
    normalized_group_id = _normalize_group_id(group_id)
    return bool(await orm_enable_group_record(normalized_group_id))


async def disable_group_record(group_id: int | str) -> bool:
    """
    记录disable群
    :param group_id: 群号
    :return: bool
    """
    normalized_group_id = _normalize_group_id(group_id)
    return bool(await orm_disable_group_record(normalized_group_id))


async def load_daily_message_stats(
    group_id: int | str,
    day: datetime.date | str | None = None,
) -> dict[str, int]:
    """
    加载每日消息stats
    :param group_id: 群号
    :param day: day 参数
    :return: dict[str, int]
    """
    normalized_group_id = _normalize_group_id(group_id)
    stat_date = _normalize_date(day)
    return dict(await orm_load_daily_message_stats(normalized_group_id, stat_date))


async def load_history_message_stats(group_id: int | str) -> dict[str, int]:
    """
    加载历史消息stats
    :param group_id: 群号
    :return: dict[str, int]
    """
    normalized_group_id = _normalize_group_id(group_id)
    return dict(await orm_load_history_message_stats(normalized_group_id))
