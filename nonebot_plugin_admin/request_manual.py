# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/6/25 21:37
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : request_manual.py
# @Software: PyCharm
import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    ActionFailed)
from nonebot.typing import T_State

request_m = on_command('请求', priority=1, block=True)


@request_m.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.message)
    flag = re.findall(re.compile(r'\d+'), msg)[0]
    if '同意' in msg and '拒绝' in msg:
        await bot.send(event, '请使用同意或拒绝')
    elif '同意' in msg:
        try:
            await bot.set_group_add_request(
                flag=flag,
                sub_type='add',
                approve=True,
                reason=' ',
            )
            await bot.send(event, '已同意')
        except ActionFailed:
            try:
                await bot.set_group_add_request(
                    flag=flag,
                    sub_type='invite',
                    approve=True,
                    reason=' ',
                )
                await bot.send(event, '已同意')
            except ActionFailed:
                await bot.send(event, '错误：请求不存在')
    elif '拒绝' in msg:
        try:
            await bot.set_group_add_request(
                flag=flag,
                sub_type='add',
                approve=False,
                reason='管理员拒绝',
            )
            await bot.send(event, '已拒绝')
        except ActionFailed:
            try:
                await bot.set_group_add_request(
                    flag=flag,
                    sub_type='invite',
                    approve=False,
                    reason='管理员拒绝',
                )
                await bot.send(event, '已拒绝')
            except ActionFailed:
                await bot.send(event, '错误：请求不存在')
