# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/16 22:03
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : group_request.py
# @Software: PyCharm
import re

from nonebot import on_command, on_request, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GroupRequestEvent, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from . import approve
from .approve import g_admin
from .config import global_config
from .group_request_verify import verify
from .path import *
from .utils import json_load

su = global_config.superusers

# 查看所有审批词条
super_sp = on_command('所有词条', priority=2, aliases={'/susp', '/su审批'}, block=True, permission=SUPERUSER)
@super_sp.handle()
async def _(matcher: Matcher):
    answers = json_load(config_admin)
    rely = ''
    for i in answers:
        rely += i + ' : ' + str(answers[i]) + '\n'
    await matcher.finish(rely)

# 按群号添加词条
super_sp_add = on_command('指定词条+', priority=2, aliases={'/susp+', '/su审批+'}, block=True, permission=SUPERUSER)
@super_sp_add.handle()
async def _(matcher: Matcher, event: MessageEvent):
    msg = str(event.get_message()).split()
    logger.info(str(len(msg)), msg)
    if len(msg) == 3:
        gid = msg[1]
        answer = msg[2]
        sp_write = await approve.write(gid, answer)
        if gid.isdigit():
            if sp_write:

                await matcher.finish(f"群{gid}添加入群审批词条：{answer}")
            else:
                await matcher.finish(f"{answer} 已存在于群{gid}的词条中")
        else:
            await matcher.finish('输入有误 /susp+ [群号] [词条]')
    else:
        await matcher.finish('输入有误 /susp+ [群号] [词条]')

# 按群号删除词条
super_sp_de = on_command('指定词条-', priority=2, aliases={'/susp-', '/su审批-'}, block=True, permission=SUPERUSER)
@super_sp_de.handle()
async def _(matcher: Matcher, event: MessageEvent):
    msg = str(event.get_message()).split()
    if len(msg) == 3:
        gid = msg[1]
        answer = msg[2]
        if gid.isdigit():
            sp_delete = await approve.delete(gid, answer)
            if sp_delete:
                await matcher.finish(f"群{gid}删除入群审批词条：{answer}")
            elif not sp_delete:
                await matcher.finish(f"群{gid}不存在此词条")
            elif sp_delete is None:
                await matcher.finish(f"群{gid}从未配置过词条")
        else:
            await matcher.finish('输入有误 /susp- [群号] [词条]')
    else:
        await matcher.finish('输入有误 /susp- [群号] [词条]')

check = on_command('查看词条', priority=2, aliases={'/sp', '/审批'}, block=True,
                   permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
@check.handle()
async def _(matcher: Matcher, event: GroupMessageEvent):
    """
    /sp 查看本群词条
    """
    a_config = json_load(config_admin)
    gid = str(event.group_id)
    if gid in a_config:
        this_config = a_config[gid]
        await matcher.finish(f"当前群审批词条：{this_config}")
    await matcher.finish('当前群从未配置过审批词条')

config = on_command('词条+', priority=2, aliases={'/sp+', '/审批+'}, block=True,
                    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
@config.handle()
async def _(matcher: Matcher, event: GroupMessageEvent, state: T_State):
    """
    /sp+ 增加本群词条
    """
    msg = str(state['_prefix']['command_arg'])
    sp_write = await approve.write(str(event.group_id), msg)
    gid = str(event.group_id)
    if sp_write:
        await matcher.finish(f"群{gid}添加词条：{msg}")
    await matcher.finish(f"{msg} 已存在于群{gid}的词条中")

config_ = on_command('词条-', priority=2, aliases={'/sp-', '/审批-'}, block=True,
                     permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
@config_.handle()
async def _(matcher: Matcher, event: GroupMessageEvent, state: T_State):
    """
    /sp- 删除本群某词条
    """
    msg = str(state['_prefix']['command_arg'])
    gid = str(event.group_id)
    sp_delete = await approve.delete(gid, msg)
    if sp_delete:
        await matcher.finish(f"群{gid}删除入群审批词条：{msg}")
    elif not sp_delete:
        await matcher.finish("当前群不存在此词条")
    elif sp_delete is None:
        await matcher.finish("当前群从未配置过词条")

# 加群审批
group_req = on_request(priority=2, block=True)
@group_req.handle()
async def gr_(bot: Bot, matcher: Matcher, event: GroupRequestEvent):
    gid = str(event.group_id)
    flag = event.flag
    logger.info('flag:', str(flag))
    sub_type = event.sub_type
    if sub_type == 'add':
        comment = event.comment
        word = re.findall(re.compile('答案：(.*)'), comment)
        word = word[0] if word else comment
        compared = await verify(word, gid)
        uid = event.user_id
        if compared:
            logger.info(f"同意{uid}加入群 {gid},验证消息为 “{word}”")
            await bot.set_group_add_request(flag=flag, sub_type=sub_type, approve=True, reason=' ')
            admins = g_admin()
            if admins['su'] == 'True':
                for q in su:
                    await bot.send_msg(user_id=int(q), message=f"同意{uid}加入群 {gid},验证消息为 “{word}”")
            if gid in admins:
                for q in admins[gid]:
                    await bot.send_msg(message_type='private', user_id=q, group_id=int(gid),
                                       message=f"同意{uid}加入群 {gid},验证消息为 “{word}”")

        elif compared is False:
            logger.info(f"拒绝{uid}加入群 {gid},验证消息为 “{word}”")
            await bot.set_group_add_request(flag=flag, sub_type=sub_type, approve=False,
                                            reason='答案未通过群管验证，可修改答案后再次申请')
            admins = json_load(config_group_admin)
            if admins['su'] == 'True':
                for q in su:
                    await bot.send_msg(user_id=int(q), message=f"拒绝{uid}加入群 {gid},验证消息为 “{word}”")
            if gid in admins:
                for q in admins[gid]:
                    await bot.send_msg(message_type='private', user_id=q, group_id=int(gid),
                                       message=f"拒绝{uid}加入群 {gid},验证消息为 “{word}”")
        elif compared is None:
            await matcher.finish()
