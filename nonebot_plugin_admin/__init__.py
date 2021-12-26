# python3
# -*- coding: utf-8 -*-
# @Time    : 2021/12/23 0:52
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : __init__.py.py
# @Software: PyCharm
from typing import Optional,Union, List
import nonebot
from nonebot import get_driver, on_command,on_request, logger
from nonebot.adapters.cqhttp import Bot, GroupMessageEvent,GroupRequestEvent,MessageEvent
from nonebot.adapters.cqhttp.exception import ActionFailed
from nonebot.adapters.cqhttp.permission import GROUP_ADMIN, GROUP_OWNER, PRIVATE_FRIEND
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
import json
import random
import re
from .group_request_verify import verify
import os
from os.path import dirname
from . import approve

su = nonebot.get_driver().config.superusers
config_path=dirname(__file__)+"/config/"
config_json=config_path+"admin.json"

def init():
    """
    初始化配置文件
    :return:
    """
    if os.path.exists(config_path) == False:
        os.mkdir(config_path)
    if os.path.exists(config_json)== False:
        with open(config_json,'w',encoding='utf-8') as c:
            c.write('{"1008611":["This is an example"]}')
            c.close()

def At(data: str):
    """
    检测at了谁
    :param data: event.json
    :return: list
    """
    try:
        qq_list = []
        data = json.loads(data)
        for msg in data["message"]:
            if msg["type"] == "at":
                if 'all' not in str(msg):
                    qq_list.append(int(msg["data"]["qq"]))
                else:
                    return ['all']
        return qq_list
    except KeyError:
        return []

susp=on_command('/susp',aliases={"/susp","/su审批"},priority=1,permission=SUPERUSER)
@susp.handle()
async def _(bot:Bot,event:MessageEvent,state:T_State):
    anwsers=await approve.load()
    rely=""
    for i in anwsers:
        rely+=i+" : "+str(anwsers[i])+"\n"
    await susp.send(rely)

susp_add=on_command('/susp+',aliases={"/susp+","/su审批+"},priority=1,permission=SUPERUSER)
@susp_add.handle()
async def _(bot:Bot,event:MessageEvent,state:T_State):
    msg=str(event.get_message()).split()
    logger.info(str(len(msg)),msg)
    if len(msg)==2:
        gid=msg[0]
        anwser=msg[1]
        sp_write = await approve.wirte(gid, anwser)
        if gid.isdigit()==True:
            if sp_write:

                await susp_add.send(f"群{gid}添加入群审批词条：{anwser}")
            else:
                await susp_add.send(f'{anwser} 已存在于群{gid}的词条中')
        else:
            await susp_de.finish('输入有误 /susp+ [群号] [词条]')


susp_de=on_command('/susp-',aliases={"/susp-","/su审批-"},priority=1,permission=SUPERUSER)
@susp_de.handle()
async def _(bot:Bot,event:MessageEvent,state:T_State):
    msg = str(event.get_message()).split()
    if len(msg) == 2:
        gid = msg[0]
        anwser = msg[1]
        if gid.isdigit()==True:
            sp_delete = await approve.delete(gid, anwser)
            if sp_delete:
                await susp_de.send(f"群{gid}删除入群审批词条：{anwser}")
            elif sp_delete==False:
                await susp_de.send(f'群{gid}不存在此词条')
            elif sp_delete==None:
                await susp_de.send(f'群{gid}从未配置过词条')
        else:
           await susp_de.finish('输入有误 /susp- [群号] [词条]')



check=on_command('/审批',aliases={"/sp","/审批"},priority=1,permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
@check.handle()
async def _(bot:Bot,event:GroupMessageEvent,state:T_State):
    """
    /sp 查看本群词条
    """
    config=await approve.load()
    gid=str(event.group_id)
    this_config= config[gid]
    await check.send(f"当前群审批词条：{this_config}")

config=on_command('/审批+',aliases={'/sp+','/审批+'},priority=1,permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
@config.handle()
async def _(bot:Bot,event:GroupMessageEvent,state:T_State):
    """
    /sp+ 增加本群词条
    """
    msg=str(event.get_message())
    sp_write=await approve.wirte(str(event.group_id),msg)
    if sp_write:
        await config.send(f"群{event.group_id}添加词条：{msg}")
    else:
        await config.send(f"{msg} 已存在于群{event.group_id}的词条中")


config_=on_command('/审批-',aliases={'/sp-','/审批-'},priority=1,permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
@config_.handle()
async def _(bot:Bot,event:GroupMessageEvent,state:T_State):
    """
    /sp- 删除本群某词条
    """
    msg=str(event.get_message())
    sp_delete=await approve.delete(str(event.group_id),msg)
    if sp_delete:
        await config_.send(f"群{event.group_id}删除入群审批词条：{msg}")
    elif sp_delete==False:
        await config_.send('当前群不存在此词条')
    elif sp_delete == None:
        await config_.send(f'当前群从未配置过词条')

#加群审批
group_req=on_request(priority=1)
@group_req.handle()
async def gr_(bot:Bot,event:GroupRequestEvent,state:T_State):
    raw=json.loads(event.json())
    gid=str(event.group_id)
    flag = raw['flag']
    logger.info('flag:',str(flag))
    sub_type = raw['sub_type']
    if sub_type =='add':
        comment=raw['comment']
        word=re.findall(re.compile('答案：(.*)'),comment)[0]
        compared=await verify(word,gid)
        uid=event.user_id
        if compared:
            logger.info(f'同意{uid}加入群 {gid},验证消息为 “{word}”')
            await bot.set_group_add_request(
                                        flag=flag,
                                        sub_type=sub_type,
                                        approve=True,
                                        reason= " ",
                                        )
            for q in su:
                await bot.send_msg(user_id=int(q),message=f'同意{uid}加入群 {gid},验证消息为 “{word}”')
        elif compared==False:
            logger.info(f'拒绝{uid}加入群 {gid},验证消息为 “{word}”')
            await bot.set_group_add_request(
                                        flag=flag,
                                        sub_type=sub_type,
                                        approve=False,
                                        reason="答案未通过群管验证，可修改答案后再次申请",
                                    )
            for q in su:
                await bot.send_msg(user_id=int(q),message=f'拒绝{uid}加入群 {gid},验证消息为 “{word}”')
        elif compared==None:
            await group_req.finish()



async def banSb(gid: int, banlist: list, time:int):
    """
    构造禁言
    :param qq: qq
    :param gid: 群号
    :param time: 时间（s)
    :param banlist: at列表
    :return:禁言操作
    """
    if 'all' in banlist:
        yield nonebot.get_bot().set_group_whole_ban(
            group_id=gid,
            enable=True
        )
    else:
        for qq in banlist:
            yield nonebot.get_bot().set_group_ban(
                group_id=gid,
                user_id=qq,
                duration=time,
            )



ban = on_command('/禁', priority=1, permission=SUPERUSER)
@ban.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    """
    /禁 @user 禁言
    """
    msg = str(event.get_message())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb) + 1:
            time = int(msg.split()[-1:][0])
            baning = banSb(gid, banlist=sb, time=time)
            async for baned in baning:
                if baned:
                    try:
                        await baned
                    except ActionFailed:
                        await ban.finish("权限不足")
                    else:
                        logger.info("操作成功")
        else:
            if 'all' not in sb:
                time = random.randint(1, 2591999)
                baning = banSb(gid, banlist=sb, time=time)
                async for baned in baning:
                    if baned:
                        try:
                            await baned
                        except ActionFailed:
                            await ban.finish("权限不足")
                        else:
                            await ban.finish(f"该用户已被随机禁{time}秒")
            else:
                await bot.set_group_whole_ban(
                    group_id=gid,
                    enable=True
                )
    else:
        pass



unban = on_command("/解", priority=1, permission=SUPERUSER)
@unban.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    """
    /解 @user 解禁
    """
    msg = str(event.get_message())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb):
            baning = banSb(gid, banlist=sb, time=0)
            async for baned in baning:
                if baned:
                    try:
                        await baned
                    except ActionFailed:
                        await ban.finish("权限不足")
                    else:
                        logger.info("操作成功")



all = on_command("/all", permission=SUPERUSER, priority=1)
@all.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    """
    （测试时没用..）
    /all 全员禁言
    /all  解 关闭全员禁言
    """
    msg = event.get_message()
    if msg and '解' in str(msg):
        enable = False
    else:
        enable = True
    try:
        await bot.set_group_whole_ban(
            group_id=event.group_id,
            enable=enable
        )
    except ActionFailed:
        await ban.finish("权限不足")
    else:
        logger.info(f"全体操作成功 {str(enable)}")



change = on_command('/改', permission=SUPERUSER, priority=1)
@change.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    """
    /改 @user xxx 改群昵称
    """
    msg = str(event.get_message())
    logger.info(msg.split())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if len(msg.split()) == 2:
            try:
                await bot.set_group_card(
                    group_id=gid,
                    user_id=int(sb[0]),
                    card=msg.split()[-1:][0]
                )
            except ActionFailed:
                await change.finish("权限不足")
            else:
                logger.info("改名片操作成功")
        else:
            await change.finish("一次仅可更改一位群员的昵称")



title = on_command('/头衔', permission=SUPERUSER, priority=1)
@title.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    """
    /头衔 @user  xxx  给某人头衔
    """
    msg = str(event.get_message())
    stitle = msg.split()[-1:][0]
    logger.info(str(msg.split()), stitle)
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb) + 1 and 'all' not in sb:
            try:
                for qq in sb:
                    await bot.set_group_special_title(
                        group_id=gid,
                        user_id=int(qq),
                        special_title=stitle,
                        duration=-1,
                    )
            except ActionFailed:
                await title.finish("权限不足")
            else:
                logger.info(f"改头衔操作成功{stitle}")
        else:
            await title.finish("未填写头衔名称 或 不能含有@全体成员")



title_ = on_command('/删头衔', permission=SUPERUSER, priority=1)
@title_.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    """
    /删头衔 @user 删除头衔
    """
    msg = str(event.get_message())
    stitle = msg.split()[-1:][0]
    logger.info(str(msg.split()), stitle)
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb) + 1 and 'all' not in sb:
            try:
                for qq in sb:
                    await bot.set_group_special_title(
                        group_id=gid,
                        user_id=int(qq),
                        special_title="",
                        duration=-1,
                    )
            except ActionFailed:
                await title_.finish("权限不足")
            else:
                logger.info(f"改头衔操作成功{stitle}")
        else:
            await title_.finish("未填写头衔名称 或 不能含有@全体成员")



kick = on_command('/踢', permission=SUPERUSER, priority=1)
@kick.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    """
    /题 @user 踢出某人
    """
    msg = str(event.get_message())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb) and 'all' not in sb:
            try:
                for qq in sb:
                    await bot.set_group_kick(
                        group_id=gid,
                        user_id=int(qq),
                        reject_add_request=False
                    )
            except ActionFailed:
                await kick.finish("权限不足")
            else:
                logger.info(f"踢人操作成功")
        else:
            await kick.finish("不能含有@全体成员")



kick_ = on_command('/踢黑', permission=SUPERUSER, priority=1)
@kick_.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    """
    /黑 @user 踢出并拉黑某人
    """
    msg = str(event.get_message())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb) and 'all' not in sb:
            try:
                for qq in sb:
                    await bot.set_group_kick(
                        group_id=gid,
                        user_id=int(qq),
                        reject_add_request=True
                    )
            except ActionFailed:
                await kick_.finish("权限不足")
            else:
                logger.info(f"踢人并拉黑操作成功")
        else:
            await kick_.finish("不能含有@全体成员")


__usage__ = """
【superuser】：
  /susp  查看所有审批词条   或/su审批
  /susp+ [群号] [词条]增加指定群审批词条 或/sp审批+
  /susp- [群号] [词条]删除指定群审批词条 或/sp审批-
  自动审批处理结果将发送给superuser
  
【加群自动审批】：
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  /审批  查看本群审批词条   或/sp
  /审批+ [词条]增加审批词条 或/sp+
  /审批- [词条]删除审批词条 或/sp-
  
【群管】：
权限：permission=SUPERUSER
  禁言:
    /禁 @某人 时间（s）[1,2591999]
    /禁 @某人 缺省时间则随机
    /禁 @某人 0 可解禁
    /解 @某人
  全群禁言（好像没用？）
    /all 
    /all 解
  改名片
    /改 @某人 名片
  改头衔（又没用？）
    /头衔 @某人 头衔
    /删头衔
  踢出：
    /踢 @某人
  提出并拉黑：
   /黑 @某人
"""
__help_plugin_name__ = "简易群管"

__permission__ = 1
__help__version__ = '0.1.5'