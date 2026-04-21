# python3
# -*- coding: utf-8 -*-

from nonebot import logger, on_command, on_request
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GroupRequestEvent, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from . import approval_command_flow
from . import approval_request_flow
from ..core.exact_command import exact_command
from ..core.config import global_config

su = global_config.superusers

SUPER_SP_ALIASES = {"/susp", "/su审批"}
CHECK_ALIASES = {"/sp", "/审批"}

super_sp = on_command(
    "所有词条",
    priority=2,
    aliases=SUPER_SP_ALIASES,
    rule=exact_command("所有词条", SUPER_SP_ALIASES),
    block=True,
    permission=SUPERUSER,
)


@super_sp.handle()
async def _(matcher: Matcher):
    await approval_command_flow.handle_super_list_terms(matcher)


super_sp_add = on_command("指定词条+", priority=2, aliases={"/susp+", "/su审批+", "指定词条加"}, block=True, permission=SUPERUSER)


@super_sp_add.handle()
async def _(matcher: Matcher, event: MessageEvent):
    await approval_command_flow.handle_super_add_term(matcher, event)


super_sp_de = on_command("指定词条-", priority=2, aliases={"/susp-", "/su审批-", "指定词条减"}, block=True, permission=SUPERUSER)


@super_sp_de.handle()
async def _(matcher: Matcher, event: MessageEvent):
    await approval_command_flow.handle_super_delete_term(matcher, event)


check = on_command(
    "查看词条",
    priority=2,
    aliases=CHECK_ALIASES,
    rule=exact_command("查看词条", CHECK_ALIASES),
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@check.handle()
async def _(matcher: Matcher, event: GroupMessageEvent):
    await approval_command_flow.handle_check_terms(matcher, event)


add_appr_term = on_command(
    "词条+",
    priority=2,
    aliases={"/sp+", "/审批+", "审批词条加", "词条加"},
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@add_appr_term.handle()
async def _(matcher: Matcher, event: GroupMessageEvent, state: T_State):
    await approval_command_flow.handle_add_term(matcher, event, state)


del_appr_term = on_command(
    "词条-",
    priority=2,
    aliases={"/sp-", "/审批-", "审批词条减", "词条减"},
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@del_appr_term.handle()
async def _(matcher: Matcher, event: GroupMessageEvent, state: T_State):
    await approval_command_flow.handle_delete_term(matcher, event, state)


edit_appr_bk = on_command(
    "词条拒绝",
    priority=2,
    aliases={"/spx", "/审批拒绝", "拒绝词条"},
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@edit_appr_bk.handle()
async def _(matcher: Matcher, event: GroupMessageEvent, state: T_State):
    await approval_command_flow.handle_edit_blacklist(matcher, event, state)


group_req = on_request(priority=2, block=True)


@group_req.handle()
async def gr_(bot: Bot, matcher: Matcher, event: GroupRequestEvent):
    """
    处理 gr_ 的业务逻辑
    :param bot: Bot 实例
    :param matcher: Matcher 实例
    :param event: 事件对象
    :return: None
    """
    logger.info("flag: %s", str(event.flag))
    handled = await approval_request_flow.handle_group_request(bot, event, su)
    if not handled:
        await matcher.finish()
