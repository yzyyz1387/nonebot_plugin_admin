# python3
# -*- coding: utf-8 -*-

from typing import Dict

from ..core.path import AI_APPROVAL_SWITCH_KEY, build_default_switchers
from ..statistics.config_orm_store import (
    orm_load_ai_verify_config,
    orm_load_switcher,
    orm_save_ai_verify_config,
    orm_save_switcher_group,
)


async def _save_ai_approval_switch(gid: str, enabled: bool) -> None:
    """
    保存AI审批统一开关
    :param gid: 群号
    :param enabled: 开关状态
    :return: None
    """
    switcher_snapshot = await orm_load_switcher() or {}
    group_switches = dict(build_default_switchers())
    group_switches.update(switcher_snapshot.get(str(gid), {}))
    group_switches[AI_APPROVAL_SWITCH_KEY] = bool(enabled)
    await orm_save_switcher_group(str(gid), group_switches)


async def load_config() -> Dict:
    """
    加载配置
    :return: Dict
    """
    config = await orm_load_ai_verify_config() or {}
    switcher_snapshot = await orm_load_switcher() or {}
    for gid, switches in switcher_snapshot.items():
        if AI_APPROVAL_SWITCH_KEY not in switches:
            continue
        normalized_gid = str(gid)
        enabled = bool(switches[AI_APPROVAL_SWITCH_KEY])
        if normalized_gid not in config and not enabled:
            continue
        group_config = config.setdefault(normalized_gid, {"enabled": False, "prompt": ""})
        group_config["enabled"] = enabled
    return config


async def save_config(data: Dict):
    """
    保存配置
    :param data: 数据对象
    :return: None
    """
    for gid, cfg in data.items():
        enabled = cfg.get("enabled", False)
        prompt = cfg.get("prompt", "")
        await orm_save_ai_verify_config(gid, enabled, prompt)
        await _save_ai_approval_switch(gid, enabled)
