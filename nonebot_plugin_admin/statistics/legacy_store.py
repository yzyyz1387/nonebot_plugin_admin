from __future__ import annotations

from typing import Any, Iterable

from ..core import path as admin_path
from ..core.utils import json_load_or_default

RECORD_STATE_VERSION = 2
RECORD_STATE_MODE = "disabled_groups"


def _normalize_group_id(group_id: int | str) -> str:
    """
    规范化群id
    :param group_id: 群号
    :return: str
    """
    return str(group_id)


def _normalize_group_ids(group_ids: Iterable[int | str]) -> list[str]:
    """
    规范化群ids
    :param group_ids: 群号列表
    :return: list[str]
    """
    normalized: list[str] = []
    seen: set[str] = set()
    for group_id in group_ids:
        normalized_group_id = _normalize_group_id(group_id).strip()
        if not normalized_group_id or normalized_group_id in seen:
            continue
        seen.add(normalized_group_id)
        normalized.append(normalized_group_id)
    return normalized


def _default_record_state() -> dict[str, Any]:
    """
    处理 _default_record_state 的业务逻辑
    :return: dict[str, Any]
    """
    return {
        "version": RECORD_STATE_VERSION,
        "mode": RECORD_STATE_MODE,
        "disabled_groups": [],
    }


def load_legacy_record_enabled_groups() -> list[str]:
    """
    加载旧版记录enabled群组
    :return: list[str]
    """
    if not admin_path.word_path.exists():
        return []
    return _normalize_group_ids(admin_path.word_path.read_text(encoding="utf-8").splitlines())


def load_record_enabled_groups() -> list[str]:
    """
    加载记录enabled群组
    :return: list[str]
    """
    return load_legacy_record_enabled_groups()


def load_record_disabled_groups() -> list[str]:
    """
    加载记录disabled群组
    :return: list[str]
    """
    state = json_load_or_default(admin_path.statistics_record_state_path, _default_record_state())
    if not isinstance(state, dict):
        return []
    if state.get("mode") != RECORD_STATE_MODE:
        return []
    disabled_groups = state.get("disabled_groups", [])
    if not isinstance(disabled_groups, list):
        return []
    return _normalize_group_ids(disabled_groups)
