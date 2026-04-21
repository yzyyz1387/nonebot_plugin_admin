# python3
# -*- coding: utf-8 -*-

from nonebot import on_command
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from ..core.exact_command import exact_command
from ..core.func_hook import check_func_status
from ..core.message import GroupMessageEvent, msg_at
from . import group_admin_command_flow

GAD_ALIASES = {"/gad", "/分群管理"}
SU_GAD_ALIASES = {"/sugad", "/su分群管理"}

gad = on_command(
    "分管",
    priority=2,
    aliases=GAD_ALIASES,
    rule=exact_command("分管", GAD_ALIASES),
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@gad.handle()
async def _(matcher: Matcher, event: GroupMessageEvent):
    gid = str(event.group_id)
    await group_admin_command_flow.handle_list_group_admins(matcher, gid)


su_g_admin = on_command(
    "所有分管",
    priority=2,
    aliases=SU_GAD_ALIASES,
    rule=exact_command("所有分管", SU_GAD_ALIASES),
    block=True,
    permission=SUPERUSER,
)


@su_g_admin.handle()
async def _(matcher: Matcher):
    await group_admin_command_flow.handle_list_all_group_admins(matcher)


g_admin = on_command(
    "分管+",
    priority=2,
    aliases={"/gad+", "分群管理+", "分管加", "分群管理加"},
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@g_admin.handle()
async def _(matcher: Matcher, event: GroupMessageEvent, state: T_State, sb: list = Depends(msg_at)):
    gid = str(event.group_id)
    await group_admin_command_flow.handle_add_group_admins(matcher, gid, state, sb)


su_gad = on_command("接收", priority=2, rule=exact_command("接收"), block=True, permission=SUPERUSER)


@su_gad.handle()
async def _(matcher: Matcher):
    await group_admin_command_flow.handle_toggle_superuser_receive(matcher)


g_admin_ = on_command(
    "分管-",
    priority=2,
    aliases={"/gad-", "分群管理-", "分管减", "分群管理减"},
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@g_admin_.handle()
async def _(matcher: Matcher, event: GroupMessageEvent, state: T_State, sb: list = Depends(msg_at)):
    gid = str(event.group_id)
    await group_admin_command_flow.handle_remove_group_admins(
        matcher,
        gid,
        state,
        sb,
        check_func_status,
    )
