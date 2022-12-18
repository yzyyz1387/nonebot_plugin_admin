# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/12/19 0:23
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : particular_e_notice.py
# @Software: PyCharm
from datetime import datetime

from nonebot import get_bot
from nonebot.adapters.onebot.v11 import (
    Bot, Event, PokeNotifyEvent,
    HonorNotifyEvent,
    GroupUploadNoticeEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupAdminNoticeEvent,
    LuckyKingNotifyEvent,
    MessageSegment
)
from nonebot.matcher import Matcher
from nonebot.plugin import on_notice
from nonebot.rule import Rule
from nonebot.typing import T_State

from .utils import fi

self_bot = get_bot()
bot_id = self_bot.self_id


# 获取戳一戳状态
async def _is_poke(bot: Bot, event: Event, state: T_State) -> bool:
    return isinstance(event, PokeNotifyEvent) and event.is_tome()


# 获取群荣誉变更
async def _is_honor(bot: Bot, event: Event, state: T_State) -> bool:
    return isinstance(event, HonorNotifyEvent)


# 获取文件上传
async def _is_checker(bot: Bot, event: Event, state: T_State) -> bool:
    return isinstance(event, GroupUploadNoticeEvent)


# 群成员减少
async def _is_user_decrease(bot: Bot, event: Event, state: T_State) -> bool:
    return isinstance(event, GroupDecreaseNoticeEvent)


# 群成员增加
async def _is_user_increase(bot: Bot, event: Event, state: T_State) -> bool:
    return isinstance(event, GroupIncreaseNoticeEvent)


# 管理员变动
async def _is_admin_change(bot: Bot, event: Event, state: T_State) -> bool:
    return isinstance(event, GroupAdminNoticeEvent)


# 红包运气王
async def _is_red_packet(bot: Bot, event: Event, state: T_State) -> bool:
    return isinstance(event, LuckyKingNotifyEvent)


poke = on_notice(Rule(_is_poke), priority=50, block=True)
honor = on_notice(Rule(_is_honor), priority=50, block=True)
upload_files = on_notice(Rule(_is_checker), priority=50, block=True)
user_decrease = on_notice(Rule(_is_user_decrease), priority=50, block=True)
user_increase = on_notice(Rule(_is_user_increase), priority=50, block=True)
admin_change = on_notice(Rule(_is_admin_change), priority=50, block=True)
red_packet = on_notice(Rule(_is_red_packet), priority=50, block=True)


@poke.handle()
async def _(bot: Bot, event: Event, state: T_State):
    # TODO 在本地做记录 不太想写文本，因为dev分支已经用了数据库，后再在写
    ...


@honor.handle()
async def _(bot: Bot, event: HonorNotifyEvent, state: T_State, matcher: Matcher):
    reply = honor_judgement(event.honor_type, event)
    await fi(matcher, reply)


@upload_files.handle()
async def _(bot: Bot, event: GroupUploadNoticeEvent, state: T_State, matcher: Matcher):
    # TODO 在本地做记录
    ...


@user_decrease.handle()
async def _(bot: Bot, event: GroupDecreaseNoticeEvent, state: T_State, matcher: Matcher):
    op = await bot.get_group_member_info(group_id=event.group_id, user_id=event.operator_id)
    casualty = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
    casualty_name = casualty["card"] if casualty["card"] else casualty["nickname"]
    op_name = op['card'] if op.get('card') else op['nickname']
    e_time = datetime.fromtimestamp(event.time).strftime("%Y-%m-%d %H:%M:%S")
    avatar = f"https://q4.qlogo.cn/headimg_dl?dst_uin={event.user_id}&spec=640"
    farewell_words = "感谢/o给/n送上的飞机，谢谢/o"
    farewell_self_words = "/n永远离开了我们/n"
    # TODO 为以后自定义欢送词做准备
    if event.operator_id != event.user_id:
        reply = f"🛫成员离开\n {farewell_words.replace('/o', f' {op_name} ').replace('/n', f' {casualty_name} ')}" \
                f" \n {e_time}\n {MessageSegment.image(avatar)}"
    else:
        reply = f"🛫成员离开\n {farewell_self_words.replace('/n', f' {casualty_name} ')}"
    await fi(matcher, reply)


@user_increase.handle()
async def _(bot: Bot, event: GroupIncreaseNoticeEvent, state: T_State, matcher: Matcher):
    avatar = f"https://q4.qlogo.cn/headimg_dl?dst_uin={event.user_id}&spec=640"
    new_be = (await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id))['nickname']
    wel_words = "欢迎/n加入我们"
    # TODO 为以后自定义欢迎词做准备
    reply = f"✨ 成员加入\n {wel_words.replace('/n', new_be)}\n {MessageSegment.image(avatar)}"
    await fi(matcher, reply)


@admin_change.handle()
async def _(bot: Bot, event: GroupAdminNoticeEvent, state: T_State, matcher: Matcher):
    reply = ""
    sub_type = event.sub_type
    uid = event.user_id
    user = await bot.get_group_member_info(group_id=event.group_id, user_id=uid)
    u_name = user['card'] if user.get('card') else user['nickname']
    cong_words = "恭喜/n成为管理"
    re_words = "Ops! /n不再具有绿帽子"
    if uid == bot_id:
        if sub_type == "set":
            reply = f"🚔 管理员变动\n{cong_words.replace('/n', '我')}"
        if sub_type == "unset":
            reply = f"🚔 管理员变动\n{re_words.replace('/n', '我')}"
    else:
        if sub_type == "set":
            reply = f"🚔 管理员变动\n{cong_words.replace('/n', f' {u_name} ')}"
        if sub_type == "unset":
            reply = f"🚔  管理员变动\n{re_words.replace('/n', f' {u_name} ')}"
    await fi(matcher, reply)


@red_packet.handle()
async def _(bot: Bot, event: LuckyKingNotifyEvent, state: T_State, matcher: Matcher):
    # TODO 也许做点本记录（运气王）
    ...


def honor_judgement(honor_type, user_id):
    reply = ""
    honor_map = {"performer": ["🔥", "群聊之火"], "emotion": ["🤣", "快乐源泉"]}
    # 龙王
    if honor_type == "talkative":
        if user_id == bot_id:
            reply = f"💦 新龙王诞生，原来是我自己~"
        else:
            reply = f"💦 恭喜{MessageSegment.at(user_id)}荣获龙王标识~"
    for key, value in honor_map.items():
        if honor_type == key:
            reply = f"{value[0]} 恭喜{MessageSegment.at(user_id)}荣获【{value[1]}】标识~"
    return reply
