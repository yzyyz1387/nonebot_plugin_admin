# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/12/17 18:07
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : broadcast.py
# @Software: PyCharm
import asyncio

from nonebot import logger, on_command, get_bot
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, ActionFailed
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, ArgStr, Arg
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from .config import global_config
from .path import broadcast_avoid_path, config_path
from .utils import json_load, json_upload, sd, fi

try:
    su = global_config.superusers
except AttributeError:
    su = []
    logger.error("请配置超级用户")
if not config_path.exists():
    config_path.mkdir()
if broadcast_avoid_path.exists():
    broadcast_config = json_load(broadcast_avoid_path)
else:
    broadcast_config = {}
    if su:
        for su_ in su:
            broadcast_config.update({str(su_): []})
            json_upload(broadcast_avoid_path, broadcast_config)

on_broadcast = on_command('广播', aliases={'告诉所有人', '告诉大家', '告诉全世界'}, priority=1, block=True,
                          permission=SUPERUSER)


@on_broadcast.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher, args: Message = CommandArg()):
    if args:
        state['b_args'] = args
        await broadcast(str(event.user_id), args, bot, matcher)


@on_broadcast.got('b_args', prompt='请输入要广播的内容，发送【取消】取消')
async def _(
        bot: Bot,
        event: MessageEvent,
        state: T_State,
        matcher: Matcher,
        b_args: Message = Arg("b_args")):
    uid = str(event.user_id)
    for i in ["取消", "算了", "退出"]:
        if i in str(b_args):
            await fi(matcher, "已取消广播")
        else:
            await broadcast(uid, b_args, bot, matcher)


add_broadcast_avoid = on_command('广播排除', priority=1, block=True, permission=SUPERUSER)


@add_broadcast_avoid.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher, args: Message = CommandArg()):
    """
    添加广播排除群
    """
    if args:
        if "+" in str(args):
            await add_avoid_group(event, args, matcher, state)
        elif "-" in str(args):
            await del_avoid_group(event, args, matcher)
    else:
        await fi(matcher, "请发送【广播排除+12345 / 广播排除-123456】\n多个群用空格分隔，查看所有群号请发送【群列表】")


all_group_list = on_command('群列表', priority=1, block=True, permission=SUPERUSER)


@all_group_list.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher):
    """
    获取所有群号
    """
    groups = await bot.get_group_list()
    r = ""
    g_list = []
    for g in groups:
        g_list.append(str(g["group_id"]))
        r += f"{g['group_name']}: {g['group_id']} \n"
    state['g_list'] = g_list
    await sd(matcher, f"共【{len(g_list)}】个群\n{r}")


@all_group_list.got("gid",
                    prompt="你现在可以直接告诉我群号，我可以帮你添加到广播排除列表\n多个用【空格】分隔\n只保留本群其他全部排除请回复【0】\n发送【取消】取消")
async def _(
        bot: Bot,
        event: MessageEvent,
        state: T_State,
        matcher: Matcher,
        gid: str = ArgStr("gid")):
    """
    添加群号到广播排除列表
    """
    g_list = state['g_list']
    for i in ["取消", "算了", "退出"]:
        if i in gid:
            await fi(matcher, "已取消添加")
    if gid == "0":
        if isinstance(event, GroupMessageEvent):
            g_list.remove(str(event.group_id))
            g_avoid = " ".join(g_list)
            await add_avoid_group(event, g_avoid, matcher, state)
        else:
            await fi(matcher, "当前不在群聊中")
    else:
        await add_avoid_group(event, gid, matcher, state)


async def add_avoid_group(event: MessageEvent, bot: Bot, args, matcher: Matcher, state: T_State):
    uid = str(event.user_id)
    args = str(args).replace("+", "").strip()
    groups = str(args).split(" ")
    groups_bot = await bot.get_group_list()
    g_list = []
    for g in groups_bot:
        g_list.append(str(g["group_id"]))
    r = ""
    try:
        history_group = broadcast_config[uid]
    except KeyError:
        history_group = []
    for g in groups:
        if g in g_list:
            if g in history_group:
                r += f"{g} 已存在,跳过\n"
                continue
            else:
                r += f"{g} 添加到广播排除列表成功\n"
                history_group.append(str(g))
        else:
            r += f"我不在群 {g} 捏,跳过\n"
            continue
    broadcast_config.update({uid: history_group})
    json_upload(broadcast_avoid_path, broadcast_config)
    await sd(matcher, f"{r}\n 发送【排除列表】可查看已排除的群")


avoided_group_list = on_command('排除列表', priority=1, block=True, permission=SUPERUSER)


@avoided_group_list.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher):
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
    await sd(matcher, f"共【{len(history_group)}】个群\n{r}")


async def del_avoid_group(event: MessageEvent, args, matcher: Matcher):
    args = str(args).replace("-", "").strip()
    uid = str(event.user_id)
    groups = str(args).split(" ")
    try:
        history_group = broadcast_config[uid]
        for g in groups:
            if g in history_group:
                history_group.remove(g)
            else:
                groups.remove(g)
        broadcast_config.update({uid: history_group})
        json_upload(broadcast_avoid_path, broadcast_config)
        r = '\n'.join(groups)
        await sd(matcher, f"已从广播排除列表中删除\n{r}")
    except KeyError:
        await fi(matcher, "广播排除列表为空")


async def broadcast(uid: str, args: Message, bot: Bot, matcher: Matcher):
    b_config = json_load(broadcast_avoid_path)
    if uid in b_config:
        groups = await bot.get_group_list()
        group_list = [g["group_id"] for g in groups]
        success = 0
        failed = 0
        excluded = 0
        for g in group_list:
            if str(g) not in b_config[uid]:
                try:
                    success += 1
                    logger.debug(f"正在向群{g}广播{args}")
                    await bot.send_group_msg(group_id=g, message="广播：")
                    await bot.send_group_msg(group_id=g, message=args)
                except ActionFailed as e:
                    failed += 1
                    logger.error(f"广播时发生错误{e}")
            else:
                excluded += 1
                logger.debug(f"群{g}已在广播排除列表中")
        await asyncio.sleep(1)
        await fi(matcher, f"广播完成\n成功：{success}\n失败：{failed}\n排除：{excluded}")


broad_cast_help = on_command('广播帮助', priority=1, block=True)


@broad_cast_help.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher):
    """
    广播帮助
    """
    r = "【广播帮助】\n" \
        "发送【广播】/【广播+[消息]】可广播消息\n" \
        "发送【群列表】可查看能广播到的所有群\n" \
        "发送【排除列表】可查看已排除的群\n" \
        "发送【广播排除+】可添加群到广播排除列表\n" \
        "发送【广播排除-】可从广播排除列表删除群\n" \
        "发送【广播帮助】可查看广播帮助"
    await sd(matcher, r)
# FIXME 适用于 su 在复习考研时发癫向所有群广播消息 暂时未写入README
