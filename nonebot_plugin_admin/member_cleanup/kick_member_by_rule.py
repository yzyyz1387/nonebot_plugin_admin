# python3
# -*- coding: utf-8 -*-

import datetime
from pathlib import Path

from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import ArgStr
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from ..core.exact_command import exact_command
from .member_cleanup_flow import (
    build_category_prompt,
    build_cleanup_preview,
    build_zero_level_notice,
    execute_member_cleanup,
    extract_last_sent_times,
    filter_members_by_last_sent,
    filter_members_by_level,
    get_member_levels,
    parse_cleanup_date,
    should_abort_for_remaining,
    should_cancel,
)
from .member_cleanup_lock import clear_cleanup_lock, ensure_cleanup_lock, get_cleanup_lock_path
from .member_cleanup_text import (
    CLEANUP_CANCELLED_TEXT,
    CLEANUP_CATEGORY_PROMPT,
    CLEANUP_CONFIRM_PROMPT,
    CLEANUP_DATE_FUTURE_TEXT,
    CLEANUP_DATE_INVALID_TEXT,
    CLEANUP_EXECUTING_TEXT,
    CLEANUP_EXECUTING_WITH_RANDOM_TEXT,
    CLEANUP_FAIL_TEXT,
    CLEANUP_INVALID_CATEGORY_TEXT,
    CLEANUP_LOCK_EXISTS_TEXT,
    CLEANUP_NO_MEMBER_TEXT,
    CLEANUP_NO_TASK_TEXT,
    CLEANUP_QUERYING_TEXT,
    CLEANUP_REMAINING_TOO_LOW_TEXT,
    CLEANUP_SUCCESS_TEXT,
    CLEANUP_UNLOCK_SUCCESS_TEXT,
)
from ..core.path import kick_lock_path


async def finish_matcher(matcher: Matcher, state: T_State, arg: str):
    """
    处理 finish_matcher 的业务逻辑
    :param matcher: Matcher 实例
    :param state: 状态字典
    :param arg: 参数值
    :return: None
    """
    if should_cancel(arg):
        clear_cleanup_lock(state["this_lock"])
        await matcher.finish(CLEANUP_CANCELLED_TEXT)


kick_by_rule = on_command("成员清理", priority=2, rule=exact_command("成员清理"), block=True, permission=SUPERUSER | GROUP_OWNER)


@kick_by_rule.got("k_category", prompt=CLEANUP_CATEGORY_PROMPT)
async def _(
    event: GroupMessageEvent,
    matcher: Matcher,
    state: T_State,
    k_category=ArgStr(),
):
    this_lock: Path = get_cleanup_lock_path(kick_lock_path, event.group_id)
    state["this_lock"] = this_lock
    if not ensure_cleanup_lock(this_lock):
        await kick_by_rule.finish(CLEANUP_LOCK_EXISTS_TEXT)

    category = str(k_category)
    await finish_matcher(matcher, state, category)

    prompt = build_category_prompt(category)
    if prompt:
        await kick_by_rule.send(prompt)
    else:
        await kick_by_rule.reject(CLEANUP_INVALID_CATEGORY_TEXT)


@kick_by_rule.got("kick_condition", prompt="请输入:")
async def _(
    bot: Bot,
    event: GroupMessageEvent,
    matcher: Matcher,
    state: T_State,
    kick_condition=ArgStr(),
):
    await kick_by_rule.send(CLEANUP_QUERYING_TEXT)
    kick_condition = str(kick_condition)
    await finish_matcher(matcher, state, kick_condition)

    member_list = await bot.get_group_member_list(group_id=event.group_id)
    category = str(state["k_category"])
    qq_list = [member["user_id"] for member in member_list]

    if category == "1":
        level_map = await get_member_levels(bot, qq_list)
        kick_list, zero_level_list = filter_members_by_level(level_map, int(kick_condition))
        zero_level_notice = build_zero_level_notice(zero_level_list)
        if zero_level_notice:
            await kick_by_rule.send(zero_level_notice)
        preview_source = level_map
    elif category == "2":
        last_sent_map = extract_last_sent_times(member_list)
        logger.debug(f"last_send_list: {last_sent_map}")
        try:
            input_time = parse_cleanup_date(kick_condition)
            if input_time > datetime.datetime.now():
                await kick_by_rule.reject(CLEANUP_DATE_FUTURE_TEXT)
            kick_list = filter_members_by_last_sent(last_sent_map, input_time)
        except ValueError:
            await kick_by_rule.reject(CLEANUP_DATE_INVALID_TEXT)
        preview_source = last_sent_map
    else:
        await kick_by_rule.reject(CLEANUP_INVALID_CATEGORY_TEXT)

    if not kick_list:
        clear_cleanup_lock(state["this_lock"])
        await kick_by_rule.finish(CLEANUP_NO_MEMBER_TEXT)

    state["kick_list"] = kick_list
    logger.debug(f"kick_list: {kick_list}")
    if should_abort_for_remaining(len(member_list), len(kick_list)):
        clear_cleanup_lock(state["this_lock"])
        await kick_by_rule.finish(CLEANUP_REMAINING_TOO_LOW_TEXT)

    await kick_by_rule.send(build_cleanup_preview(kick_list, category, preview_source))


@kick_by_rule.got("confirm", prompt=CLEANUP_CONFIRM_PROMPT)
async def _(matcher: Matcher, state: T_State):
    confirm = str(state["confirm"])
    if confirm == "1":
        await kick_by_rule.send(CLEANUP_EXECUTING_TEXT)
    else:
        await finish_matcher(matcher, state, "取消")


@kick_by_rule.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    kick_list = state["kick_list"]
    if not kick_list:
        clear_cleanup_lock(state["this_lock"])
        await kick_by_rule.send(CLEANUP_NO_MEMBER_TEXT)
        return

    await kick_by_rule.send(CLEANUP_EXECUTING_WITH_RANDOM_TEXT)
    success, fail = await execute_member_cleanup(
        bot,
        event.group_id,
        event.user_id,
        kick_list,
    )
    if success:
        await kick_by_rule.send(CLEANUP_SUCCESS_TEXT.format(success=success))
    if fail:
        await kick_by_rule.send(CLEANUP_FAIL_TEXT.format(fail=fail))

    clear_cleanup_lock(state["this_lock"])


delete_lock_manually = on_command("清理解锁", priority=2, rule=exact_command("清理解锁"), block=True, permission=SUPERUSER | GROUP_OWNER)


@delete_lock_manually.handle()
async def _(event: GroupMessageEvent):
    this_lock: Path = get_cleanup_lock_path(kick_lock_path, event.group_id)
    if this_lock.exists():
        clear_cleanup_lock(this_lock)
        await delete_lock_manually.finish(CLEANUP_UNLOCK_SUCCESS_TEXT)
    else:
        await delete_lock_manually.finish(CLEANUP_NO_TASK_TEXT)
