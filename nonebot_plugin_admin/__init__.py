# python3
# -*- coding: utf-8 -*-
# @Time    : 2021/12/23 0:52
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : __init__.py.py
# @Software: PyCharm

from nonebot import logger
from nonebot import get_driver, on_command, logger
import nonebot
from nonebot.matcher import Matcher
from nonebot.adapters.cqhttp import Bot, Event, GroupMessageEvent
from nonebot.adapters.cqhttp.exception import ActionFailed
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from typing import Union, List
import json
import random

su = nonebot.get_driver().config.superusers


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


# 禁言
ban = on_command('/禁', priority=1, permission=SUPERUSER)


@ban.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
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


# 解禁
unban = on_command("/解", priority=1, permission=SUPERUSER)


@unban.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
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


# 全群禁言（测试时没用..）
all = on_command("/all", permission=SUPERUSER, priority=1)


@all.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
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


# 改
change = on_command('/改', permission=SUPERUSER, priority=1)


@change.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
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


# 头衔
title = on_command('/头衔', permission=SUPERUSER, priority=1)


@title.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
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


# 踢
kick = on_command('/踢', permission=SUPERUSER, priority=1)


@kick.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
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


# 踢 黑
kick_ = on_command('/踢黑', permission=SUPERUSER, priority=1)


@kick_.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
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
简易群管：
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


"""
__help_plugin_name__ = "简易群管"

__permission__ = 1
__help__version__ = '0.1.5'