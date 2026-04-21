# python3
# -*- coding: utf-8 -*-

from typing import Optional

from nonebot import logger, on_command, on_message
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Depends
from nonebot.permission import SUPERUSER

from ..core.config import plugin_config
from ..core.exact_command import exact_command
from ..core.message import Bot, GroupMessageEvent, msg_raw
from ..core.path import time_scop_map
from ..core.utils import get_user_violation, mute_sb, sd
from ..statistics.config_orm_store import orm_add_content_guard_rule, orm_delete_content_guard_rule
from .text_guard_flow import check_runtime_text_message, load_runtime_limit_rules

cb_notice = plugin_config.callback_notice


def _split_rule_args(args: Message) -> list[str]:
    """
    处理 _split_rule_args 的业务逻辑
    :param args: 命令参数
    :return: list[str]
    """
    return [item.strip() for item in str(args).split(" ") if item.strip()]


def _parse_rule_entry(entry: str) -> tuple[str, str]:
    """
    解析规则entry
    :param entry: entry 参数
    :return: tuple[str, str]
    """
    pattern, _, options = entry.partition("\t")
    return pattern.strip(), options.strip()


def _format_rule_entry(pattern: str, options: str = "") -> str:
    """
    格式化规则entry
    :param pattern: pattern 参数
    :param options: options 参数
    :return: str
    """
    if options:
        return f"{pattern}\t{options}"
    return pattern


async def _load_rule_entries() -> list[str]:
    """
    加载规则entries
    :return: list[str]
    """
    return [
        _format_rule_entry(rule[0], rule[1] if len(rule) > 1 else "")
        for rule in await load_runtime_limit_rules()
        if rule and rule[0]
    ]


del_custom_limit_words = on_command(
    "删除违禁词",
    priority=2,
    aliases={"移除违禁词", "去除违禁词"},
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@del_custom_limit_words.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    if not args:
        await matcher.finish("请输入删除内容,多个以空格分隔，例：\n删除违禁词 内容1 内容2")

    existing_rules = set(await _load_rule_entries())
    success_del: list[str] = []
    already_del: list[str] = []
    failed_del: list[str] = []

    for entry in _split_rule_args(args):
        if entry not in existing_rules:
            already_del.append(entry)
            continue

        pattern, options = _parse_rule_entry(entry)
        deleted = await orm_delete_content_guard_rule(pattern, options)
        if deleted:
            success_del.append(entry)
            existing_rules.discard(entry)
        else:
            failed_del.append(entry)

    if success_del:
        await matcher.send(f"{str(success_del)}删除成功")
    if already_del:
        await matcher.send(f"{str(already_del)}还不是违禁词")
    if failed_del:
        await matcher.send(f"{str(failed_del)}删除失败")
    await matcher.finish()


add_custom_limit_words = on_command(
    "添加违禁词",
    priority=2,
    aliases={"增加违禁词", "新增违禁词"},
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@add_custom_limit_words.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    if not args:
        await matcher.finish("请输入添加内容,多个以空格分隔，例：\n添加违禁词 内容1 内容2")

    existing_rules = set(await _load_rule_entries())
    already_add: list[str] = []
    success_add: list[str] = []
    failed_add: list[str] = []

    for entry in _split_rule_args(args):
        if entry in existing_rules:
            already_add.append(entry)
            continue

        pattern, options = _parse_rule_entry(entry)
        added = await orm_add_content_guard_rule(pattern, options)
        if added:
            success_add.append(entry)
            existing_rules.add(entry)
        else:
            failed_add.append(entry)

    if already_add:
        await matcher.send(f"{str(already_add)}已存在")
    if success_add:
        await matcher.send(f"{str(success_add)}添加成功")
    if failed_add:
        await matcher.send(f"{str(failed_add)}添加失败")


get_custom_limit_words = on_command(
    "查看违禁词",
    priority=2,
    aliases={"查询违禁词", "违禁词列表"},
    rule=exact_command("查看违禁词", {"查询违禁词", "违禁词列表"}),
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@get_custom_limit_words.handle()
async def _(matcher: Matcher):
    if cb_notice:
        rules = await _load_rule_entries()
        if not rules:
            await matcher.finish("该群没有违禁词")
        try:
            await matcher.finish("\n".join(rules))
        except ActionFailed:
            await matcher.finish("内容太长，无法发送")



async def check_msg(text: str, gid: int) -> tuple[bool, bool, Optional[str]]:
    """
    检查msg
    :param text: 文本内容
    :param gid: 群号
    :return: tuple[bool, bool, Optional[str]]
    """
    return await check_runtime_text_message(text, gid)


f_word = on_message(priority=3, block=False)


@f_word.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, text: str = Depends(msg_raw)):
    gid = event.group_id
    uid = [event.user_id]
    delete, ban, matched = await check_msg(text, gid)
    if not matched:
        return

    level = await get_user_violation(gid, event.user_id, "Text", matched)
    logger.info(f"检测到违禁词: {matched}，用户: {event.user_id}，等级: {level}")

    if delete:
        try:
            await bot.delete_msg(message_id=event.message_id)
            logger.info("违禁词消息撤回成功")
        except ActionFailed:
            logger.info("违禁词消息撤回失败，权限不足")

    if ban:
        baning = mute_sb(bot, gid, lst=uid, scope=time_scop_map[level])
        async for baned in baning:
            if baned:
                try:
                    await baned
                    await sd(matcher, f"检测到违禁词：{matched}\n已执行处罚")
                except ActionFailed:
                    logger.info("违禁词禁言失败，权限不足")
    elif cb_notice:
        await sd(matcher, f"检测到违禁词：{matched}")
