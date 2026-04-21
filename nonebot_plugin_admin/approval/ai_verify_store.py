# python3
# -*- coding: utf-8 -*-

from typing import Dict

from ..statistics.config_orm_store import orm_load_ai_verify_config, orm_save_ai_verify_config

async def load_config() -> Dict:
    """
    加载配置
    :return: Dict
    """
    return await orm_load_ai_verify_config() or {}


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
