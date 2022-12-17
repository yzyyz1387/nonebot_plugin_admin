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
from nonebot.params import CommandArg, ArgStr, Arg
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
async def _(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher, args: Message = CommandArg()):
    if args:
        state['b_args'] = args
        await broadcast(str(event.user_id), args, bot, matcher)


@on_broadcast.got('b_args', prompt='请输入要广播的内容')
async def _(
        bot: Bot,
        event: MessageEvent,
        state: T_State,
        matcher: Matcher,
        b_args: Message = Arg("b_args")):
    uid = str(event.user_id)
    for i in ["取消", "算了", "退出"]:
        if i in str(b_args):
            await on_broadcast.finish("已取消广播")
        else:
            await broadcast(uid, b_args, bot, matcher)


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
        r += f"{g['group_name']}: {g['group_id']} \n"
    await all_group_list.send(r)


@all_group_list.got("gid", prompt="你现在可以直接告诉我群号，我可以帮你添加到广播排除列表,发送【取消】取消")
async def _(
        bot: Bot,
        event: MessageEvent,
        state: T_State,
        matcher: Matcher,
        gid: str = ArgStr("gid")):
    """
    添加群号到广播排除列表
    """
    for i in ["取消", "算了", "退出"]:
        if i in gid:
            await matcher.finish("已取消添加")
    await add_avoid_group(event, gid, matcher)


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
    await matcher.send(f"已添加{groups}到广播排除列表, 发送【排除列表】可查看已排除的群")


avoided_group_list = on_command('排除列表', priority=1, block=True, permission=SUPERUSER)


@avoided_group_list.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    """
    获取广播排除列表
    """
    uid = str(event.user_id)
    _config = json_load(broadcast_avoid_path)
    try:
        history_group = _config[uid]
    except KeyError:
        history_group = []
    r = "【排除列表】"
    for g in history_group:
        g_name = (await bot.get_group_info(group_id=int(g)))['group_name']
        r += f"{g_name}: {g} \n"
    await avoided_group_list.send(r)


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


async def broadcast(uid: str, args: Message, bot: Bot, matcher: Matcher):
    b_config = json_load(broadcast_avoid_path)
    if uid in b_config:
        groups = await bot.get_group_list()
        group_list = [g["group_id"] for g in groups]
        for g in group_list:
            if str(g) not in b_config[uid]:
                try:
                    logger.debug(f"正在向群{g}广播{args}")
                    await bot.send_group_msg(group_id=g, message="广播：")
                    await bot.send_group_msg(group_id=g, message=args)
                except Exception as e:
                    logger.error(f"广播时发生错误{e}")
            else:
                logger.debug(f"群{g}已在广播排除列表中")
        await matcher.finish("广播完成")
# FIXME 适用于 su 在复习考研时发癫向所有群广播消息 暂时未写入README
