# python3
# -*- coding: utf-8 -*-

from typing import Optional

from nonebot import logger

from .approval_text import (
    APPROVAL_NOTICE_DISABLED,
    APPROVAL_NOTICE_ENABLED,
    format_approval_term_added,
    format_approval_term_deleted,
    format_group_admin_added,
    format_group_admin_delete_missing,
    format_group_admin_deleted,
    format_group_admin_exists,
    format_group_admin_unconfigured,
    format_term_exists,
)
from ..statistics.config_orm_store import (
    orm_load_approval_terms, orm_add_approval_term, orm_delete_approval_term,
    orm_load_deputy_admins, orm_add_deputy_admin, orm_delete_deputy_admin,
    orm_get_global_config, orm_set_global_config,
)


async def _load_group_admin_snapshot() -> dict:
    """
    加载群管理员snapshot
    :return: dict
    """
    orm_data = await orm_load_deputy_admins() or {}
    result = {gid: list(uids) for gid, uids in orm_data.items()}
    su_val = await orm_get_global_config("approval_su_notice", "True")
    result["su"] = su_val if su_val else "True"
    return result


def g_admin() -> dict:
    """
    处理 g_admin 的业务逻辑
    :return: dict
    """
    result = _run_async_or_none(_load_group_admin_snapshot)
    if result is None:
        raise RuntimeError("g_admin() cannot be used inside a running event loop; use g_admin_async() instead.")
    return result


def _run_async_or_none(async_fn, *args):
    """
    执行asyncornone
    :param async_fn: async_fn 参数
    :param args: 可变位置参数
    :return: None
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            return None
    except RuntimeError:
        loop = None

    if loop is None:
        return asyncio.run(async_fn(*args))

    return loop.run_until_complete(async_fn(*args))


async def g_admin_async() -> dict:
    """
    处理 g_admin_async 的业务逻辑
    :return: dict
    """
    return await _load_group_admin_snapshot()


async def g_admin_add(gid: str, qq: int) -> Optional[bool]:
    """
    添加g管理员
    :param gid: 群号
    :param qq: QQ 号
    :return: Optional[bool]
    """
    orm_created = await orm_add_deputy_admin(gid, qq)
    if orm_created is None:
        return None
    if not orm_created:
        logger.info(format_group_admin_exists(gid, qq))
        return False
    logger.info(format_group_admin_added(gid, qq))
    return True


async def g_admin_del(gid: str, qq: int) -> Optional[bool]:
    """
    处理 g_admin_del 的业务逻辑
    :param gid: 群号
    :param qq: QQ 号
    :return: Optional[bool]
    """
    orm_deleted = await orm_delete_deputy_admin(gid, qq)
    if orm_deleted is None:
        return None
    if not orm_deleted:
        admins = await g_admin_async()
        if gid not in admins:
            logger.info(format_group_admin_unconfigured(gid))
            return None
        logger.info(format_group_admin_delete_missing(gid, qq))
        return False
    logger.info(format_group_admin_deleted(gid, qq))
    return True


async def su_on_off() -> Optional[bool]:
    """
    处理 su_on_off 的业务逻辑
    :return: Optional[bool]
    """
    orm_admins = await orm_load_deputy_admins()
    if orm_admins is None:
        return None
    current = await orm_get_global_config("approval_su_notice", "True")

    enabled = current == "False"
    next_value = "True" if enabled else "False"
    await orm_set_global_config("approval_su_notice", next_value)

    logger.info(APPROVAL_NOTICE_ENABLED if enabled else APPROVAL_NOTICE_DISABLED)
    return enabled


async def write(gid: str, answer: str) -> Optional[bool]:
    """
    写入
    :param gid: 群号
    :param answer: answer 参数
    :return: Optional[bool]
    """
    orm_created = await orm_add_approval_term(gid, answer)
    if orm_created is None:
        return None
    if not orm_created:
        logger.info(format_term_exists(gid, answer))
        return False
    logger.info(format_approval_term_added(gid, answer))
    return True


async def delete(gid: str, answer: str) -> Optional[bool]:
    """
    删除
    :param gid: 群号
    :param answer: answer 参数
    :return: Optional[bool]
    """
    orm_deleted = await orm_delete_approval_term(gid, answer)
    if orm_deleted is None:
        return None
    if not orm_deleted:
        terms = await orm_load_approval_terms() or {}
        if gid not in terms:
            logger.info(f"群 {gid} 从未配置过审批词条")
            return None
        logger.info(f"删除失败：群 {gid} 中不存在审批词条 {answer}")
        return False
    logger.info(format_approval_term_deleted(gid, answer))
    return True
