# python3
# -*- coding: utf-8 -*-

from typing import Optional

from nonebot import logger

from ..statistics.config_orm_store import (
    orm_load_broadcast_exclusions,
    orm_add_broadcast_exclusion,
    orm_remove_broadcast_exclusion,
)

async def load_exclusions() -> dict:
    """
    加载exclusions
    :return: dict
    """
    return await orm_load_broadcast_exclusions() or {}


async def add_exclusion(user_id: str, group_id: str) -> bool:
    """
    添加exclusion
    :param user_id: 用户号
    :param group_id: 群号
    :return: bool
    """
    orm_created = await orm_add_broadcast_exclusion(user_id, group_id)
    if orm_created is None:
        return False
    if orm_created:
        logger.info(f"广播排除添加：用户 {user_id} 排除群 {group_id}")
    return orm_created


async def remove_exclusion(user_id: str, group_id: str) -> Optional[bool]:
    """
    移除exclusion
    :param user_id: 用户号
    :param group_id: 群号
    :return: Optional[bool]
    """
    orm_deleted = await orm_remove_broadcast_exclusion(user_id, group_id)
    if orm_deleted is None:
        return None
    if orm_deleted:
        logger.info(f"广播排除移除：用户 {user_id} 群 {group_id}")
    return orm_deleted


async def load_broadcast_config(superusers) -> dict:
    """
    加载broadcast配置
    :param superusers: 超管列表
    :return: dict
    """
    data = dict(await load_exclusions())
    for su in superusers:
        if su not in data:
            data[su] = []
    return data


async def get_excluded_groups(user_id: str, superusers) -> list[str]:
    """
    获取excluded群组
    :param user_id: 用户号
    :param superusers: 超管列表
    :return: list[str]
    """
    data = await load_broadcast_config(superusers)
    groups = data.get(user_id, [])
    for su in superusers:
        if user_id == su:
            groups = data.get(su, [])
    return groups


async def add_excluded_groups(user_id: str, group_ids: list[str], valid_group_ids: list[str], superusers) -> tuple[int, int, int]:
    """
    添加excluded群组
    :param user_id: 用户号
    :param group_ids: 群号列表
    :param valid_group_ids: 标识列表
    :param superusers: 超管列表
    :return: tuple[int, int, int]
    """
    added = 0
    existed = 0
    invalid = 0
    for gid in group_ids:
        if gid not in valid_group_ids:
            invalid += 1
        else:
            orm_created = await orm_add_broadcast_exclusion(user_id, gid)
            if orm_created:
                added += 1
            else:
                existed += 1
    return added, existed, invalid


async def remove_excluded_groups(user_id: str, group_ids: list[str], superusers) -> tuple[int, int]:
    """
    移除excluded群组
    :param user_id: 用户号
    :param group_ids: 群号列表
    :param superusers: 超管列表
    :return: tuple[int, int]
    """
    removed = 0
    missing = 0
    for gid in group_ids:
        orm_deleted = await orm_remove_broadcast_exclusion(user_id, gid)
        if orm_deleted:
            removed += 1
        else:
            missing += 1
    return removed, missing
