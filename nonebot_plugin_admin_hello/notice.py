# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/16 22:02
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : notice.py
# @Software: PyCharm

from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from nonebot.params import State
from . import approve
from .utils import At, check_func_status

# 查看当前群分管
gad = on_command('分管', aliases={"/gad", "/分群管理"}, priority=1, block=True,
                 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@gad.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    admins = await approve.g_admin()
    try:
        rely = str(admins[gid])
        logger.info(f"用户{event.user_id}查询群 {event.group_id} 分管成功")
        await gad.send(f"本群分管：{rely}")
    except KeyError:
        logger.info(f"用户{event.user_id}查询群 {event.group_id} 分管失败")
        await gad.send(f"查询不到呢，使用 分管+@xx 来添加分管")


# 查看所有分管
su_g_admin = on_command('所有分管', aliases={"/sugad", "/su分群管理"}, priority=1, block=True, permission=SUPERUSER)


@su_g_admin.handle()
async def _(bot: Bot, event: MessageEvent):
    admins = await approve.g_admin()
    admins = str(admins)
    logger.info("超级用户查询所有分管成功")
    await su_g_admin.send(admins)


# 添加分群管理员
g_admin = on_command('分管+', aliases={"/gad+", "分群管理+"}, priority=1, block=True,
                     permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@g_admin.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    msg = str(event.get_message())
    sb = At(event.json())
    gid = str(event.group_id)
    if sb and "all" not in sb:
        for qq in sb:
            g_admin_handle = await approve.g_admin_add(gid, int(qq))
            if g_admin_handle:
                await g_admin.send(f"{qq}已成为本群分群管理：将接收加群处理结果")
            else:
                await g_admin.send(f"用户{qq}已存在")
    else:
        sb = str(state['_prefix']['command_arg']).split(" ")
        for qq in sb:
            g_admin_handle = await approve.g_admin_add(gid, int(qq))
            if g_admin_handle:
                await g_admin.send(f"{qq}已成为本群分群管理：将接收加群处理结果")
            else:
                await g_admin.send(f"用户{qq}已存在")


# 开启superuser接收处理结果
su_gad = g_admin = on_command('接收', priority=1, block=True, permission=SUPERUSER)


@su_gad.handle()
async def _(bot: Bot, event: MessageEvent):
    status = await approve.su_on_off()
    if status:
        await su_gad.finish("已开启超管消息接收")
    else:
        await su_gad.finish("已关闭超管消息接收")


# 删除分群管理
g_admin_ = on_command('分管-', aliases={"/gad-", "分群管理-"}, priority=1, block=True,
                      permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@g_admin_.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    msg = str(event.get_message())
    sb = At(event.json())
    gid = str(event.group_id)
    status = await check_func_status("requests", str(gid))
    if status:
        if sb and "all" not in sb:
            for qq in sb:
                g_admin_del_handle = await approve.g_admin_del(gid, int(qq))
                if g_admin_del_handle:
                    await g_admin_.send(f"{qq}删除成功")
                elif not g_admin_del_handle:
                    await g_admin_.send(f'{qq}还不是分群管理')
                elif g_admin_del_handle is None:
                    await g_admin_.send(f"群{gid}未添加过分群管理\n使用/gadmin+ [用户（可@ 可qq）]来添加分群管理")
        else:
            sb = str(state['_prefix']['command_arg']).split(" ")
            for qq in sb:
                g_admin_del_handle = await approve.g_admin_del(gid, int(qq))
                if g_admin_del_handle:
                    await g_admin_.send(f"{qq}删除成功")
                elif not g_admin_del_handle:
                    await g_admin_.send(f'{qq}还不是分群管理')
                elif g_admin_del_handle is None:
                    await g_admin_.send(f"群{gid}未添加过分群管理\n使用/gadmin+ [用户（可@ 可qq）]来添加分群管理")
    else:
        await gad.send("请先发送【开关加群审批】开启加群处理")