from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from nonebot import logger


@dataclass
class GroupMessageConfig:
    group_ids: list[str] = field(default_factory=list)
    morning_enabled: bool = True
    night_enabled: bool = True
    mode: int = 2
    morning_sentences: list[str] = field(default_factory=list)
    night_sentences: list[str] = field(default_factory=list)
    morning_hour: str = "7"
    morning_minute: str = "0"
    night_hour: str = "22"
    night_minute: str = "0"


def _parse_bool(value: Any, default: bool) -> bool:
    """
    解析bool
    :param value: 值
    :param default: default 参数
    :return: bool
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", ""}:
            return False
    return default


def _parse_group_ids(value: Any) -> list[str]:
    """
    解析群ids
    :param value: 值
    :return: list[str]
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            try:
                loaded = json.loads(stripped)
                if isinstance(loaded, list):
                    return [str(item) for item in loaded if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in stripped.split(",") if item.strip()]
    return [str(value)]


def _parse_mode(value: Any) -> int:
    """
    解析mode
    :param value: 值
    :return: int
    """
    try:
        mode = int(value)
    except (TypeError, ValueError):
        return 2
    return 1 if mode == 1 else 2


def _parse_time(value: Any, default: str) -> tuple[str, str]:
    """
    解析time
    :param value: 值
    :param default: default 参数
    :return: tuple[str, str]
    """
    raw = str(value).strip() if value is not None else default
    parts = raw.split()
    if len(parts) != 2:
        parts = default.split()
    hour, minute = parts[0], parts[1]
    try:
        hour_int = max(0, min(23, int(hour)))
        minute_int = max(0, min(59, int(minute)))
        return str(hour_int), str(minute_int)
    except ValueError:
        default_hour, default_minute = default.split()
        return default_hour, default_minute


def _parse_sentences(value: Any) -> list[str]:
    """
    解析sentences
    :param value: 值
    :return: list[str]
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            try:
                loaded = json.loads(stripped)
                if isinstance(loaded, list):
                    return [str(item) for item in loaded if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [stripped]
    return [str(value)]


def load_group_message_config(driver_config) -> GroupMessageConfig:
    """
    加载群消息配置
    :param driver_config: driver_config 参数
    :return: GroupMessageConfig
    """
    group_ids = _parse_group_ids(getattr(driver_config, "send_group_id", None))
    if not group_ids:
        logger.error("请配置 send_group_id")

    morning_hour, morning_minute = _parse_time(getattr(driver_config, "send_time_morning", None), "7 0")
    night_hour, night_minute = _parse_time(getattr(driver_config, "send_time_night", None), "22 0")

    return GroupMessageConfig(
        group_ids=group_ids,
        morning_enabled=_parse_bool(getattr(driver_config, "send_switch_morning", None), True),
        night_enabled=_parse_bool(getattr(driver_config, "send_switch_night", None), True),
        mode=_parse_mode(getattr(driver_config, "send_mode", None)),
        morning_sentences=_parse_sentences(getattr(driver_config, "send_sentence_morning", None)),
        night_sentences=_parse_sentences(getattr(driver_config, "send_sentence_night", None)),
        morning_hour=morning_hour,
        morning_minute=morning_minute,
        night_hour=night_hour,
        night_minute=night_minute,
    )
