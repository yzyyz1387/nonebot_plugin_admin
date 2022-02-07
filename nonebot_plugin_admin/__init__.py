# python3
# -*- coding: utf-8 -*-
# @Time    : 2021/12/23 0:52
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : __init__.py.py
# @Software: PyCharm
import nonebot
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from . import approve
from .utils import At, banSb, init
from .group_request_verify import verify
from . import approve, group_request_verify, group_request, notice, utils, word_analyze, r18_pic_ban
su = nonebot.get_driver().config.superusers

admin_init =  on_command('群管初始化', priority=1, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@admin_init.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await init()

ban = on_command('禁', priority=1, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


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


unban = on_command("解", priority=1, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


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


change = on_command('改', permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


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


title_ = on_command('删头衔', permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


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


kick = on_command('踢', permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


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


kick_ = on_command('黑', permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


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


set_g_admin = on_command("管理员+", permission=SUPERUSER | GROUP_OWNER, priority=1, block=True)


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


unset_g_admin = on_command("管理员-", permission=SUPERUSER | GROUP_OWNER, priority=1, block=True)


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
  管理员- @xxx 取消某人管理员
  
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
  
【群词云统计】
该功能所用库 wordcloud 未写入依赖，请自行安装
群内发送：
  记录本群 ： 开始统计聊天记录 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  停止记录本群 ：停止统计聊天记录
  群词云 ： 发送词云图片
"""
__help_plugin_name__ = "简易群管"

__permission__ = 1
__help__version__ = '0.2.0'
