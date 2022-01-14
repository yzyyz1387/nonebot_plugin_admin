# python3
# -*- coding: utf-8 -*-
# @Time    : 2021/12/23 0:52
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : __init__.py.py
# @Software: PyCharm
import nonebot
from nonebot import on_command, on_request, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GroupRequestEvent, MessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER, PRIVATE_FRIEND
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from nonebot.params import State
import json
import random
import re
from .group_request_verify import verify
import os
from os.path import dirname
from . import approve

su = nonebot.get_driver().config.superusers
config_path = dirname(__file__) + "/config/"
config_json = config_path + "admin.json"
config_group = config_path + "group_admin.json"

admin_init = on_command("群管初始化", priority=1, block=True)


@admin_init.handle()
async def init(bot: Bot, event: MessageEvent):
    """
    初始化配置文件
    :return:
    """
    if not os.path.exists(config_path):
        os.mkdir(config_path)
        logger.info("创建 config 文件夹")
    if not os.path.exists(config_json):
        with open(config_json, 'w', encoding='utf-8') as c:
            c.write('{"1008611":["This_is_an_example"]}')
            c.close()
            logger.info("创建admin.json")
    if not os.path.exists(config_group):
        with open(config_group, 'w', encoding='utf-8') as c:
            c.write('{"su":"True"}')
            c.close()
            logger.info("创建group_admin.json")
    logger.info("Admin 插件 初始化")


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


# 查看当前群分管
gad = on_command('分管', aliases={"/gad", "/分群管理"}, priority=1, block=True,
                 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@gad.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    admins = await approve.gadmin()
    rely = str(admins[gid])
    await gad.send(f"本群分管：{rely}")


# 查看所有分管
su_g_admin = on_command('所有分管', aliases={"/sugad", "/su分群管理"}, priority=1, block=True, permission=SUPERUSER)


@su_g_admin.handle()
async def _(bot: Bot, event: MessageEvent):
    admins = await approve.gadmin()
    admins = str(admins)
    await su_g_admin.send(admins)


# 添加分群管理员
g_admin = on_command('分管+', aliases={"/gad+", "分群管理+"}, priority=1, block=True,
                     permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@g_admin.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State = State()):
    msg = str(event.get_message())
    sb = At(event.json())
    gid = str(event.group_id)
    if sb and "all" not in sb:
        for qq in sb:
            g_admin_handle = await approve.gadmin_add(gid, int(qq))
            if g_admin_handle:
                await g_admin.send(f"{qq}已成为本群分群管理：将接收加群处理结果")
            else:
                await g_admin.send(f"用户{qq}已存在")
    else:
        sb = str(state['_prefix']['command_arg']).split(" ")
        for qq in sb:
            g_admin_handle = await approve.gadmin_add(gid, int(qq))
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
async def _(bot: Bot, event: GroupMessageEvent, state: T_State = State()):
    msg = str(event.get_message())
    sb = At(event.json())
    gid = str(event.group_id)
    if sb and "all" not in sb:
        for qq in sb:
            g_admin_del_handle = await approve.gadmin_del(gid, int(qq))
            if g_admin_del_handle:
                await g_admin_.send(f"{qq}删除成功")
            elif not g_admin_del_handle:
                await g_admin_.send(f'{qq}还不是分群管理')
            elif g_admin_del_handle is None:
                await g_admin_.send(f"群{gid}未添加过分群管理\n使用/gadmin+ [用户（可@ 可qq）]来添加分群管理")
    else:
        sb = str(state['_prefix']['command_arg']).split(" ")
        for qq in sb:
            g_admin_del_handle = await approve.gadmin_del(gid, int(qq))
            if g_admin_del_handle:
                await g_admin_.send(f"{qq}删除成功")
            elif not g_admin_del_handle:
                await g_admin_.send(f'{qq}还不是分群管理')
            elif g_admin_del_handle is None:
                await g_admin_.send(f"群{gid}未添加过分群管理\n使用/gadmin+ [用户（可@ 可qq）]来添加分群管理")


# 查看所有审批词条
super_sp = on_command('所有词条', aliases={"/susp", "/su审批"}, priority=1, block=True, permission=SUPERUSER)


@super_sp.handle()
async def _(bot: Bot, event: MessageEvent):
    answers = await approve.load()
    rely = ""
    for i in answers:
        rely += i + " : " + str(answers[i]) + "\n"
    await super_sp.send(rely)


# 按群号添加词条
super_sp_add = on_command('指定词条+', aliases={"/susp+", "/su审批+"}, priority=1, block=True, permission=SUPERUSER)


@super_sp_add.handle()
async def _(bot: Bot, event: MessageEvent):
    msg = str(event.get_message()).split()
    print(msg)
    logger.info(str(len(msg)), msg)
    if len(msg) == 3:
        gid = msg[1]
        answer = msg[2]
        sp_write = await approve.write(gid, answer)
        if gid.isdigit():
            if sp_write:

                await super_sp_add.send(f"群{gid}添加入群审批词条：{answer}")
            else:
                await super_sp_add.send(f'{answer} 已存在于群{gid}的词条中')
        else:
            await super_sp_de.finish('输入有误 /susp+ [群号] [词条]')
    else:
        await super_sp_de.finish('输入有误 /susp+ [群号] [词条]')


# 按群号删除词条
super_sp_de = on_command('指定词条-', aliases={"/susp-", "/su审批-"}, priority=1, block=True, permission=SUPERUSER)


@super_sp_de.handle()
async def _(bot: Bot, event: MessageEvent):
    msg = str(event.get_message()).split()
    if len(msg) == 3:
        gid = msg[1]
        answer = msg[2]
        if gid.isdigit():
            sp_delete = await approve.delete(gid, answer)
            if sp_delete:
                await super_sp_de.send(f"群{gid}删除入群审批词条：{answer}")
            elif not sp_delete:
                await super_sp_de.send(f'群{gid}不存在此词条')
            elif sp_delete is None:
                await super_sp_de.send(f'群{gid}从未配置过词条')
        else:
            await super_sp_de.finish('输入有误 /susp- [群号] [词条]')
    else:
        await super_sp_de.finish('输入有误 /susp- [群号] [词条]')


check = on_command('查看词条', aliases={"/sp", "/审批"}, priority=1, block=True,
                   permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@check.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    /sp 查看本群词条
    """
    config = await approve.load()
    gid = str(event.group_id)
    if gid in config:
        this_config = config[gid]
        await check.send(f"当前群审批词条：{this_config}")
    else:
        await check.send("当前群从未配置过审批词条")


config = on_command('词条+', aliases={'/sp+', '/审批+'}, priority=1, block=True,
                    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@config.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State = State()):
    """
    /sp+ 增加本群词条
    """
    msg = str(state['_prefix']['command_arg'])
    sp_write = await approve.write(str(event.group_id), msg)
    if sp_write:
        await config.send(f"群{event.group_id}添加词条：{msg}")
    else:
        await config.send(f"{msg} 已存在于群{event.group_id}的词条中")


config_ = on_command('词条-', aliases={'/sp-', '/审批-'}, priority=1, block=True,
                     permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@config_.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State = State()):
    """
    /sp- 删除本群某词条
    """
    msg = str(state['_prefix']['command_arg'])
    sp_delete = await approve.delete(str(event.group_id), msg)
    if sp_delete:
        await config_.send(f"群{event.group_id}删除入群审批词条：{msg}")
    elif not sp_delete:
        await config_.send('当前群不存在此词条')
    elif sp_delete is None:
        await config_.send(f'当前群从未配置过词条')


# 加群审批
group_req = on_request(priority=1, block=True)


@group_req.handle()
async def gr_(bot: Bot, event: GroupRequestEvent):
    raw = json.loads(event.json())
    gid = str(event.group_id)
    flag = raw['flag']
    logger.info('flag:', str(flag))
    sub_type = raw['sub_type']
    if sub_type == 'add':
        comment = raw['comment']
        word = re.findall(re.compile('答案：(.*)'), comment)[0]
        compared = await verify(word, gid)
        uid = event.user_id
        if compared:
            logger.info(f'同意{uid}加入群 {gid},验证消息为 “{word}”')
            await bot.set_group_add_request(
                flag=flag,
                sub_type=sub_type,
                approve=True,
                reason=" ",
            )
            with open(config_group, mode='r') as f:
                admins_ = f.read()
                admins = json.loads(admins_)
                f.close()
            if admins['su'] == "True":
                for q in su:
                    await bot.send_msg(user_id=int(q), message=f'同意{uid}加入群 {gid},验证消息为 “{word}”')
            if gid in admins:
                for q in admins[gid]:
                    await bot.send_msg(message_type="private", user_id=q, group_id=int(gid),
                                       message=f'同意{uid}加入群 {gid},验证消息为 “{word}”')

        elif not compared:
            logger.info(f'拒绝{uid}加入群 {gid},验证消息为 “{word}”')
            await bot.set_group_add_request(
                flag=flag,
                sub_type=sub_type,
                approve=False,
                reason="答案未通过群管验证，可修改答案后再次申请",
            )
            with open(config_group, mode='r') as f:
                admins_ = f.read()
                admins = json.loads(admins_)
                f.close()
            if admins['su'] == "True":
                for q in su:
                    await bot.send_msg(user_id=int(q), message=f'拒绝{uid}加入群 {gid},验证消息为 “{word}”')
            if gid in admins:
                for q in admins[gid]:
                    await bot.send_msg(message_type="private", user_id=q, group_id=int(gid),
                                       message=f'拒绝{uid}加入群 {gid},验证消息为 “{word}”')
        elif compared is None:
            await group_req.finish()


async def banSb(gid: int, ban_list: list, **time: int):
    """
    构造禁言
    :param qq: qq
    :param gid: 群号
    :param time: 时间（s)
    :param ban_list: at列表
    :return:禁言操作
    """
    if 'all' in ban_list:
        yield nonebot.get_bot().set_group_whole_ban(
            group_id=gid,
            enable=True
        )
    else:
        if not time:
            time = random.randint(1, 2591999)
        for qq in ban_list:
            yield nonebot.get_bot().set_group_ban(
                group_id=gid,
                user_id=qq,
                duration=time,
            )


ban = on_command('禁', priority=1, block=True, permission=SUPERUSER|GROUP_ADMIN | GROUP_OWNER)


@ban.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    /禁 @user 禁言
    """
    msg = str(event.get_message())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb) + 1:
            time = int(msg.split()[-1:][0])
            baning = banSb(gid, ban_list=sb, time=time)
            async for baned in baning:
                if baned:
                    try:
                        await baned
                    except ActionFailed:
                        await ban.finish("权限不足")
                    else:
                        logger.info("禁言操作成功")
        else:
            baning = banSb(gid, ban_list=sb)
            async for baned in baning:
                if baned:
                    try:
                        await baned
                    except ActionFailed:
                        await ban.finish("权限不足")
                    else:
                        logger.info("禁言操作成功")
                await ban.send(f"该用户已被禁言随机时长")
    else:
        pass


unban = on_command("解", priority=1, block=True, permission=SUPERUSER|GROUP_ADMIN | GROUP_OWNER)


@unban.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    /解 @user 解禁
    """
    msg = str(event.get_message())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb):
            baning = banSb(gid, ban_list=sb, time=0)
            async for baned in baning:
                if baned:
                    try:
                        await baned
                    except ActionFailed:
                        await ban.finish("权限不足")
                    else:
                        logger.info("解禁操作成功")


ban_all = on_command("/all", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


@ban_all.handle()
async def _(bot: Bot, event: GroupMessageEvent):
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


change = on_command('改', permission=SUPERUSER|GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


@change.handle()
async def _(bot: Bot, event: GroupMessageEvent):
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


title = on_command('头衔', permission=SUPERUSER | GROUP_OWNER, priority=1, block=True)


@title.handle()
async def _(bot: Bot, event: GroupMessageEvent):
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


title_ = on_command('删头衔', permission=SUPERUSER|GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


@title_.handle()
async def _(bot: Bot, event: GroupMessageEvent):
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


kick = on_command('踢', permission=SUPERUSER|GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


@kick.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    /踢 @user 踢出某人
    """
    msg = str(event.get_message())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb) + 1 and 'all' not in sb:
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


kick_ = on_command('黑', permission=SUPERUSER|GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


@kick_.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    黑 @user 踢出并拉黑某人
    """
    msg = str(event.get_message())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb) + 1 and 'all' not in sb:
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


set_g_admin = on_command("管理员+", permission=SUPERUSER | GROUP_OWNER, block=True)


@set_g_admin.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    管理员+ @user 添加群管理员
    """
    msg = str(event.get_message())
    logger.info(msg)
    logger.info(msg.split())
    sb = At(event.json())
    logger.info(sb)
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb) + 1 and 'all' not in sb:
            try:
                for qq in sb:
                    await bot.set_group_admin(
                        group_id=gid,
                        user_id=int(qq),
                        enable=True
                    )
            except ActionFailed:
                await set_g_admin.finish("权限不足")
            else:
                logger.info(f"设置管理员操作成功")
                await set_g_admin.finish("设置管理员操作成功")
        else:
            await set_g_admin.finish("指令不正确 或 不能含有@全体成员")


unset_g_admin = on_command("管理员-", permission=SUPERUSER | GROUP_OWNER, block=True)


@unset_g_admin.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    管理员+ @user 添加群管理员
    """
    msg = str(event.get_message())
    logger.info(msg)
    logger.info(msg.split())
    sb = At(event.json())
    logger.info(sb)
    gid = event.group_id
    if sb:
        if len(msg.split()) == len(sb) + 1 and 'all' not in sb:
            try:
                for qq in sb:
                    await bot.set_group_admin(
                        group_id=gid,
                        user_id=int(qq),
                        enable=True
                    )
            except ActionFailed:
                await unset_g_admin.finish("权限不足")
            else:
                logger.info(f"取消管理员操作成功")
                await unset_g_admin.finish("取消管理员操作成功")
        else:
            await unset_g_admin.finish("指令不正确 或 不能含有@全体成员")


__usage__ = """
【初始化】：
  群管初始化 ：初始化插件

【群管】：
权限：permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER
  禁言:
    禁 @某人 时间（s）[1,2591999]
    禁 @某人 缺省时间则随机
    禁 @某人 0 可解禁
    解 @某人
  全群禁言（好像没用？）
    /all 
    /all 解
  改名片
    改 @某人 名片
  改头衔
    头衔 @某人 头衔
    删头衔
  踢出：
    踢 @某人
  踢出并拉黑：
   黑 @某人
   
【管理员】permission=SUPERUSER | GROUP_OWNER
  管理员+ @xxx 设置某人为管理员
  管医院- @xxx 取消某人管理员
  
【加群自动审批】：
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  查看词条 ： 查看本群审批词条   或/审批
  词条+ [词条] ：增加审批词条 或/审批+
  词条- [词条] ：删除审批词条 或/审批-

【superuser】：
  所有词条 ：  查看所有审批词条   或/su审批
  指定词条+ [群号] [词条] ：增加指定群审批词条 或/su审批+
  指定词条- [群号] [词条] ：删除指定群审批词条 或/su审批-
  自动审批处理结果将发送给superuser

【分群管理员设置】*分管：可以接受加群处理结果消息的用户
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  分管+ [user] ：user可用@或qq 添加分群管理员
  分管- [user] ：删除分群管理员
  查看分管 ：查看本群分群管理员

群内或私聊 permission=SUPERUSER
  所有分管 ：查看所有分群管理员
  群管接收 ：打开或关闭超管消息接收（关闭则审批结果不会发送给superusers）
"""
__help_plugin_name__ = "简易群管"

__permission__ = 1
__help__version__ = '0.2.0'
