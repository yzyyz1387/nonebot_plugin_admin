from nonebot import logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent
from nonebot.matcher import Matcher
from nonebot.typing import T_State

from . import approval_blacklist_store
from . import approval_store
from .approval_text import (
    ADD_TERM_EMPTY,
    BLACKLIST_TERM_EMPTY,
    BLACKLIST_USAGE,
    DELETE_TERM_EMPTY,
    GROUP_TERMS_EMPTY,
    NO_APPROVAL_TERMS_CONFIGURED,
    SUPER_ADD_USAGE,
    SUPER_DELETE_USAGE,
    format_approval_term_added,
    format_approval_term_deleted,
    format_blacklist_added,
    format_blacklist_removed,
    format_group_term_missing,
    format_group_term_unconfigured,
    format_group_terms,
    format_term_added,
    format_term_exists,
)
from ..statistics.config_orm_store import orm_load_approval_terms


async def handle_super_list_terms(matcher: Matcher):
    """
    处理superlist词条
    :param matcher: Matcher 实例
    :return: None
    """
    answers = await orm_load_approval_terms() or {}
    lines = [f"{gid} : {terms}" for gid, terms in answers.items()]
    await matcher.finish("\n".join(lines) if lines else NO_APPROVAL_TERMS_CONFIGURED)


async def handle_super_add_term(matcher: Matcher, event: MessageEvent):
    """
    处理superadd词条
    :param matcher: Matcher 实例
    :param event: 事件对象
    :return: None
    """
    parts = str(event.get_message()).split()
    logger.info(str(len(parts)), parts)
    if len(parts) != 3:
        await matcher.finish(SUPER_ADD_USAGE)

    gid, answer = parts[1], parts[2]
    if not gid.isdigit():
        await matcher.finish(SUPER_ADD_USAGE)

    added = await approval_store.write(gid, answer)
    if added:
        await matcher.finish(format_approval_term_added(gid, answer))
    await matcher.finish(format_term_exists(gid, answer))


async def handle_super_delete_term(matcher: Matcher, event: MessageEvent):
    """
    处理superdelete词条
    :param matcher: Matcher 实例
    :param event: 事件对象
    :return: None
    """
    parts = str(event.get_message()).split()
    if len(parts) != 3:
        await matcher.finish(SUPER_DELETE_USAGE)

    gid, answer = parts[1], parts[2]
    if not gid.isdigit():
        await matcher.finish(SUPER_DELETE_USAGE)

    deleted = await approval_store.delete(gid, answer)
    if deleted:
        await matcher.finish(format_approval_term_deleted(gid, answer))
    if deleted is False:
        await matcher.finish(format_group_term_missing(gid))
    await matcher.finish(format_group_term_unconfigured(gid))


async def handle_check_terms(matcher: Matcher, event: GroupMessageEvent):
    """
    处理check词条
    :param matcher: Matcher 实例
    :param event: 事件对象
    :return: None
    """
    answers = await orm_load_approval_terms() or {}
    gid = str(event.group_id)
    if gid in answers:
        await matcher.finish(format_group_terms(gid, answers[gid]))
    await matcher.finish(GROUP_TERMS_EMPTY)


async def handle_add_term(matcher: Matcher, event: GroupMessageEvent, state: T_State):
    """
    处理add词条
    :param matcher: Matcher 实例
    :param event: 事件对象
    :param state: 状态字典
    :return: None
    """
    msg = str(state["_prefix"]["command_arg"]).strip()
    gid = str(event.group_id)
    if not msg:
        await matcher.finish(ADD_TERM_EMPTY)

    added = await approval_store.write(gid, msg)
    if added:
        await matcher.finish(format_term_added(gid, msg))
    await matcher.finish(format_term_exists(gid, msg))


async def handle_delete_term(matcher: Matcher, event: GroupMessageEvent, state: T_State):
    """
    处理delete词条
    :param matcher: Matcher 实例
    :param event: 事件对象
    :param state: 状态字典
    :return: None
    """
    msg = str(state["_prefix"]["command_arg"]).strip()
    gid = str(event.group_id)
    if not msg:
        await matcher.finish(DELETE_TERM_EMPTY)

    deleted = await approval_store.delete(gid, msg)
    if deleted:
        await matcher.finish(format_approval_term_deleted(gid, msg))
    if deleted is False:
        await matcher.finish("当前群不存在此词条")
    await matcher.finish("当前群从未配置过词条")


async def handle_edit_blacklist(matcher: Matcher, event: GroupMessageEvent, state: T_State):
    """
    处理edit黑名单
    :param matcher: Matcher 实例
    :param event: 事件对象
    :param state: 状态字典
    :return: None
    """
    msg = str(state["_prefix"]["command_arg"]).strip()
    if not msg or msg[0] not in {"+", "-"}:
        await matcher.finish(BLACKLIST_USAGE)

    gid = str(event.group_id)
    word = msg[1:].replace(" ", "")
    if not word:
        await matcher.finish(BLACKLIST_TERM_EMPTY)

    if msg[0] == "+":
        if not await approval_blacklist_store.add_blacklist_term(gid, word):
            await matcher.finish(format_term_exists(gid, word))
        await matcher.finish(format_blacklist_added(gid, word))

    if not await approval_blacklist_store.get_group_blacklist(gid):
        await matcher.finish(format_group_term_unconfigured(gid))

    removed = await approval_blacklist_store.remove_blacklist_term(gid, word)
    if removed is True:
        await matcher.finish(format_blacklist_removed(gid, word))
    if removed is False:
        await matcher.finish(format_group_term_missing(gid))
    await matcher.finish(format_group_term_unconfigured(gid))
