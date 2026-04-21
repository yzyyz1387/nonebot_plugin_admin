# python3
# -*- coding: utf-8 -*-

import datetime

from nonebot import logger, on_command, on_message
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Depends
from nonebot.permission import SUPERUSER

from ..core.exact_command import exact_command
from ..core.message import msg_at, msg_text_no_url
from .statistics_query_flow import build_member_count_messages, build_ranking_message, build_top_speaker_message
from .statistics_record_flow import handle_disable_group_recording, handle_enable_group_recording, record_group_message
from .statistics_read_service import (
    daily_message_stats_exists_snapshot,
    load_daily_message_stats_snapshot,
    load_history_message_stats_snapshot,
)
from .stop_words_flow import (
    handle_add_group_stop_words,
    handle_delete_group_stop_words,
    handle_list_group_stop_words,
)

word_start = on_command(
    "记录本群",
    priority=2,
    rule=exact_command("记录本群"),
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@word_start.handle()
async def _(matcher: Matcher, event: GroupMessageEvent):
    gid = str(event.group_id)
    enabled, message = await handle_enable_group_recording(gid)
    if enabled:
        logger.info(f"恢复群 {gid} 的消息内容记录")
    else:
        logger.info(f"群 {gid} 已处于记录状态")
    await matcher.finish(message)


word_stop = on_command(
    "停止记录本群",
    priority=2,
    rule=exact_command("停止记录本群"),
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@word_stop.handle()
async def _(matcher: Matcher, event: GroupMessageEvent):
    gid = str(event.group_id)
    disabled, message = await handle_disable_group_recording(gid)
    if disabled:
        logger.info(f"停止记录群 {gid} 的消息内容")
    else:
        logger.info(f"群 {gid} 已处于停止记录状态")
    await matcher.finish(message)


word = on_message(priority=3, block=False)


@word.handle()
async def _(event: GroupMessageEvent, msg: str = Depends(msg_text_no_url)):
    plain_text = msg
    raw_text = str(event.raw_message or "")
    await record_group_message(
        event.group_id,
        event.user_id,
        plain_text,
        message_id=getattr(event, "message_id", None),
        created_at=getattr(event, "time", None),
        raw_message=raw_text,
    )


stop_words_add = on_command(
    "添加停用词",
    priority=2,
    aliases={"增加停用词", "新增停用词"},
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@stop_words_add.handle()
async def _(event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    await handle_add_group_stop_words(event.group_id, matcher, args)


stop_words_del = on_command(
    "删除停用词",
    priority=2,
    aliases={"移除停用词", "去除停用词"},
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@stop_words_del.handle()
async def _(event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    await handle_delete_group_stop_words(event.group_id, matcher, args)


stop_words_list = on_command(
    "停用词列表",
    priority=2,
    aliases={"查看停用词", "查询停用词"},
    rule=exact_command("停用词列表", {"查看停用词", "查询停用词"}),
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@stop_words_list.handle()
async def _(event: GroupMessageEvent, matcher: Matcher):
    await handle_list_group_stop_words(event.group_id, matcher)


TODAY_TOP_ALIASES = {"今天谁话多", "今儿谁话多", "今天谁屁话最多"}
TODAY_RANK_ALIASES = {"今日排行榜", "今日发言排行榜", "今日排行"}
YESTERDAY_RANK_ALIASES = {"昨日排行榜", "昨日发言排行榜", "昨日排行"}
HISTORY_RANK_ALIASES = {"谁话多", "谁屁话最多", "排行榜"}

who_speak_most_today = on_command(
    "今日榜首",
    priority=2,
    aliases=TODAY_TOP_ALIASES,
    rule=exact_command("今日榜首", TODAY_TOP_ALIASES),
    block=True,
)


@who_speak_most_today.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent):
    gid = str(event.group_id)
    today = datetime.date.today().strftime("%Y-%m-%d")
    if not await daily_message_stats_exists_snapshot(gid, today):
        await matcher.finish("今天还没有人发言")
    message = await build_top_speaker_message(bot, gid, await load_daily_message_stats_snapshot(gid, today))
    await matcher.finish(message or "今天还没有人发言")


speak_top = on_command(
    "今日发言排行",
    priority=2,
    aliases=TODAY_RANK_ALIASES,
    rule=exact_command("今日发言排行", TODAY_RANK_ALIASES),
    block=True,
)


@speak_top.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent):
    gid = str(event.group_id)
    today = datetime.date.today().strftime("%Y-%m-%d")
    if not await daily_message_stats_exists_snapshot(gid, today):
        await matcher.finish("今天还没有人发言")
    message = await build_ranking_message(bot, gid, await load_daily_message_stats_snapshot(gid, today))
    await matcher.finish(message or "今天还没有人发言")


speak_top_yesterday = on_command(
    "昨日发言排行",
    priority=2,
    aliases=YESTERDAY_RANK_ALIASES,
    rule=exact_command("昨日发言排行", YESTERDAY_RANK_ALIASES),
    block=True,
)


@speak_top_yesterday.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent):
    gid = str(event.group_id)
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    if not await daily_message_stats_exists_snapshot(gid, yesterday):
        await matcher.finish("昨天没有消息记录")
    message = await build_ranking_message(bot, gid, await load_daily_message_stats_snapshot(gid, yesterday))
    await matcher.finish(message or "昨天没有消息记录")


who_speak_most = on_command(
    "排行",
    priority=2,
    aliases=HISTORY_RANK_ALIASES,
    rule=exact_command("排行", HISTORY_RANK_ALIASES),
    block=True,
)


@who_speak_most.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent):
    gid = str(event.group_id)
    message = await build_ranking_message(bot, gid, await load_history_message_stats_snapshot(gid))
    await matcher.finish(message or "还没有历史发言记录")


get_speak_num = on_command("发言数", priority=2, aliases={"发言", "发言量"}, block=True)


@get_speak_num.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, at_list: list = Depends(msg_at)):
    gid = str(event.group_id)
    if not at_list:
        await matcher.finish("请艾特需要查询的成员")
    messages = await build_member_count_messages(bot, gid, await load_history_message_stats_snapshot(gid), at_list, today=False)
    await matcher.finish("\n".join(messages))


get_speak_num_today = on_command("今日发言数", priority=2, aliases={"今日发言", "今日发言量"}, block=True)


@get_speak_num_today.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, at_list: list = Depends(msg_at)):
    gid = str(event.group_id)
    today = datetime.date.today().strftime("%Y-%m-%d")
    if not at_list:
        await matcher.finish("请艾特需要查询的成员")
    messages = await build_member_count_messages(bot, gid, await load_daily_message_stats_snapshot(gid, today), at_list, today=True)
    await matcher.finish("\n".join(messages))
