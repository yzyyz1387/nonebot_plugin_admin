# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/12/17 18:07
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : broadcast.py
# @Software: PyCharm
from nonebot import get_driver
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot import logger, on_command
from nonebot.permission import SUPERUSER
from nonebot.params import CommandArg, ArgStr
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, MessageEvent

from .config import global_config
from .path import broadcast_avoid_path
from .utils import json_load, json_upload

try:
    su = global_config.superusers
except AttributeError:
    su = []
    logger.error("请配置超级用户")

if broadcast_avoid_path.exists():
    broadcast_config = json_load(broadcast_avoid_path)
else:
    broadcast_config = {}
    if su:
        for su_ in su:
            broadcast_config.update({str(su_): []})
            json_upload(broadcast_avoid_path, broadcast_config)

on_broadcast = on_command('广播', aliases={'告诉所有人', '告诉大家'}, priority=1, block=True, permission=SUPERUSER)


@on_broadcast.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, args: Message = CommandArg()):
    if args:
        state['args'] = args


@on_broadcast.got('args', prompt='请输入要广播的内容')
async def _(
        bot: Bot,
        event: MessageEvent,
        state: T_State,
        args: str = ArgStr("args")):
    uid = str(event.user_id)
    for i in ["取消", "算了", "退出"]:
        if i in args:
            await on_broadcast.finish("已取消广播")
    else:
        if uid in broadcast_config:
            groups = await bot.get_group_list()
            group_list = [g["group_id"] for g in groups]
            for g in group_list:
                if g not in broadcast_config[uid]:
                    try:
                        await bot.send_group_msg(group_id=g, message=args)
                    except Exception as e:
                        logger.error(f"广播时发生错误{e}")


add_broadcast_avoid = on_command('广播排除', priority=1, block=True, permission=SUPERUSER)


@add_broadcast_avoid.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher, args: Message = CommandArg()):
    """
    添加广播排除群
    """
    uid = str(event.user_id)
    if args:
        if "+" in args:
            await add_avoid_group(event, args, matcher)
        elif "-" in args:
            await del_avoid_group(event, args, matcher)
    else:
        await add_broadcast_avoid.finish("请输入要添加的群号,用空格分隔，查看所有群号请发送【群列表】")


all_group_list = on_command('群列表', priority=1, block=True, permission=SUPERUSER)


@all_group_list.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    """
    获取所有群号
    """
    groups = await bot.get_group_list()
    r = ""
    for g in groups:
        r += f"{g['grop_name']: g['group_id']} \n"
    await all_group_list.finish(r)


@all_group_list.got("gid", prompt="你现在可以直接告诉我群号，我可以帮你添加到广播排除列表,发送【取消】取消")
async def _(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher, args: str = ArgStr("gid")):
    """
    添加群号到广播排除列表
    """
    if args:
        for i in ["取消", "算了", "退出"]:
            if i in args:
                await matcher.finish("已取消添加")
        await add_avoid_group(event, args, matcher)


async def add_avoid_group(event: MessageEvent, args, matcher: Matcher):
    uid = str(event.user_id)
    groups = str(args).split(" ")
    try:
        history_group = broadcast_config[uid]
    except KeyError:
        history_group = []
    for g in groups:
        history_group.append(str(g))
    broadcast_config.update({uid: history_group})
    json_upload(broadcast_avoid_path, broadcast_config)
    await matcher.send("已添加{groups}到广播排除列表")


async def del_avoid_group(event: MessageEvent, args, matcher: Matcher):
    uid = str(event.user_id)
    groups = str(args).split(" ")
    try:
        history_group = broadcast_config[uid]
        for g in groups:
            if g in history_group:
                history_group.remove(g)
        broadcast_config.update({uid: history_group})
        json_upload(broadcast_avoid_path, broadcast_config)
        await matcher.send(f"已从广播排除列表中删除{groups}")
    except KeyError:
        await matcher.finish("广播排除列表为空")


# FIXME 适用于 su 在复习考研时发癫向所有群广播消息 暂时未写入README
