# python3
# -*- coding: utf-8 -*-

from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import Arg, ArgStr, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from ..core.config import global_config
from ..core.exact_command import exact_command
from ..core.utils import fi, sd
from .broadcast_flow import (
    execute_broadcast,
    get_excluded_group_list_message,
    get_group_list_message,
    is_cancel_input,
    is_confirm_input,
    normalize_group_tokens,
    prepare_broadcast_preview,
)
from .broadcast_store import add_excluded_groups, get_excluded_groups, remove_excluded_groups
from .broadcast_text import (
    BROADCAST_AVOID_USAGE_TEXT,
    BROADCAST_CANCELLED_TEXT,
    BROADCAST_CONFIRM_INVALID_TEXT,
    BROADCAST_CONFIRM_PROMPT,
    BROADCAST_GROUP_LIST_PROMPT,
    BROADCAST_INPUT_PROMPT,
    BROADCAST_LIST_CANCELLED_TEXT,
    BROADCAST_NOT_IN_GROUP_TEXT,
    BROADCAST_NO_TARGET_TEXT,
    format_add_excluded_result,
    format_broadcast_result,
    format_remove_excluded_result,
)

su = global_config.superusers

on_broadcast = on_command(
    "广播",
    priority=2,
    aliases={"告诉所有人", "告诉大家", "告诉全世界"},
    block=True,
    permission=SUPERUSER,
)


@on_broadcast.handle()
async def _(state: T_State, args: Message = CommandArg()):
    if args:
        state["broadcast_message"] = args


@on_broadcast.got("broadcast_message", prompt=BROADCAST_INPUT_PROMPT)
async def _(bot: Bot, matcher: Matcher, event: MessageEvent, state: T_State, broadcast_message: Message = Arg("broadcast_message")):
    if is_cancel_input(str(broadcast_message)):
        await fi(matcher, BROADCAST_CANCELLED_TEXT)

    preview = await prepare_broadcast_preview(bot, str(event.user_id), broadcast_message, su)
    if not preview["target_groups"]:
        await fi(matcher, BROADCAST_NO_TARGET_TEXT)

    state["broadcast_message"] = broadcast_message
    state["target_group_ids"] = [str(group["group_id"]) for group in preview["target_groups"]]
    state["excluded_count"] = len(preview["excluded_groups"])
    await sd(matcher, preview["text"])


@on_broadcast.got("confirm", prompt=BROADCAST_CONFIRM_PROMPT)
async def _(matcher: Matcher, confirm: str = ArgStr("confirm")):
    if is_cancel_input(confirm):
        await fi(matcher, BROADCAST_CANCELLED_TEXT)
    if not is_confirm_input(confirm):
        await matcher.reject(BROADCAST_CONFIRM_INVALID_TEXT)


@on_broadcast.handle()
async def _(bot: Bot, matcher: Matcher, state: T_State):
    target_ids = set(state.get("target_group_ids", []))
    message: Message = state["broadcast_message"]
    groups = await bot.get_group_list()
    target_groups = [group for group in groups if str(group["group_id"]) in target_ids]
    success, failed = await execute_broadcast(bot, target_groups, message)
    await fi(matcher, format_broadcast_result(success, failed, int(state.get("excluded_count", 0))))


add_broadcast_avoid = on_command("广播排除", priority=2, block=True, permission=SUPERUSER)


@add_broadcast_avoid.handle()
async def _(bot: Bot, matcher: Matcher, event: MessageEvent, args: Message = CommandArg()):
    raw_args = str(args).strip()
    if not raw_args:
        await fi(matcher, BROADCAST_AVOID_USAGE_TEXT)

    groups = await bot.get_group_list()
    valid_group_ids = [str(group["group_id"]) for group in groups]
    user_id = str(event.user_id)

    if raw_args.startswith("+"):
        added, existed, invalid = await add_excluded_groups(
            user_id,
            normalize_group_tokens(raw_args[1:]),
            valid_group_ids,
            su,
        )
        await sd(matcher, format_add_excluded_result(added, existed, invalid))
        return

    if raw_args.startswith("-"):
        removed, missing = await remove_excluded_groups(user_id, normalize_group_tokens(raw_args[1:]), su)
        await fi(matcher, format_remove_excluded_result(removed, missing))
        return

    await fi(matcher, BROADCAST_AVOID_USAGE_TEXT)


avoided_group_list = on_command("排除列表", priority=2, rule=exact_command("排除列表"), block=True, permission=SUPERUSER)


@avoided_group_list.handle()
async def _(bot: Bot, matcher: Matcher, event: MessageEvent):
    excluded_group_ids = await get_excluded_groups(str(event.user_id), su)
    await fi(matcher, await get_excluded_group_list_message(bot, excluded_group_ids))


all_group_list = on_command("群列表", priority=2, rule=exact_command("群列表"), block=True, permission=SUPERUSER)


@all_group_list.handle()
async def _(matcher: Matcher, state: T_State, bot: Bot):
    message, group_ids = await get_group_list_message(bot)
    state["group_catalog_ids"] = group_ids
    await sd(matcher, message)


@all_group_list.got("gid", prompt=BROADCAST_GROUP_LIST_PROMPT)
async def _(bot: Bot, matcher: Matcher, event: MessageEvent, state: T_State, gid: str = ArgStr("gid")):
    if is_cancel_input(gid):
        await fi(matcher, BROADCAST_LIST_CANCELLED_TEXT)

    if gid.strip() == "0":
        if not isinstance(event, GroupMessageEvent):
            await fi(matcher, BROADCAST_NOT_IN_GROUP_TEXT)
        target_group_ids = [group_id for group_id in state["group_catalog_ids"] if group_id != str(event.group_id)]
    else:
        target_group_ids = normalize_group_tokens(gid)

    groups = await bot.get_group_list()
    valid_group_ids = [str(group["group_id"]) for group in groups]
    added, existed, invalid = await add_excluded_groups(str(event.user_id), target_group_ids, valid_group_ids, su)
    await fi(matcher, format_add_excluded_result(added, existed, invalid))


broad_cast_help = on_command("广播帮助", priority=2, rule=exact_command("广播帮助"), block=True)


@broad_cast_help.handle()
async def _(matcher: Matcher):
    await sd(
        matcher,
        "\n".join(
            [
                "广播帮助",
                "发送【广播】或【广播 [消息]】开始广播流程。",
                "广播前会先生成预览，只有发送“确认”才会真正发出。",
                "发送【群列表】查看机器人当前所在群，并可继续添加排除群。",
                "发送【排除列表】查看当前广播排除列表。",
                "发送【广播排除+ 群号】添加排除群。",
                "发送【广播排除- 群号】移除排除群。",
            ]
        ),
    )
