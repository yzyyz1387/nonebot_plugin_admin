# python3
# -*- coding: utf-8 -*-

from nonebot import logger

from .approval_text import format_blacklist_added, format_blacklist_removed
from ..statistics.config_orm_store import (
    orm_load_approval_blacklist, orm_add_blacklist_term, orm_delete_blacklist_term,
)

async def load_blacklist() -> dict:
    """
    加载黑名单
    :return: dict
    """
    return await orm_load_approval_blacklist() or {}


async def ensure_blacklist_seed(gid: str) -> dict:
    """
    确保黑名单seed
    :param gid: 群号
    :return: dict
    """
    data = await load_blacklist()
    if gid not in data:
        data[gid] = ["This_is", "an_example"]
        await orm_add_blacklist_term(gid, "This_is")
        await orm_add_blacklist_term(gid, "an_example")
    return data


async def get_group_blacklist(gid: str) -> list[str]:
    """
    获取群黑名单
    :param gid: 群号
    :return: list[str]
    """
    data = await load_blacklist()
    return list(data.get(gid, []))


async def add_blacklist_term(gid: str, word: str) -> bool:
    """
    添加黑名单词条
    :param gid: 群号
    :param word: word 参数
    :return: bool
    """
    orm_created = await orm_add_blacklist_term(gid, word)
    if orm_created is None:
        return False
    if orm_created:
        logger.info(format_blacklist_added(gid, word))
    return orm_created


async def remove_blacklist_term(gid: str, word: str):
    """
    移除黑名单词条
    :param gid: 群号
    :param word: word 参数
    :return: None
    """
    orm_deleted = await orm_delete_blacklist_term(gid, word)
    if orm_deleted is None:
        return None
    if orm_deleted:
        logger.info(format_blacklist_removed(gid, word))
    return orm_deleted
