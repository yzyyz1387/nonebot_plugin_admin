# python3
# -*- coding: utf-8 -*-

import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import ActionFailed, Bot, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER

request_m = on_command("请求", priority=2, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@request_m.handle()
async def _(bot: Bot, event: MessageEvent):
    msg = str(event.message)
    flags = re.findall(re.compile(r"\d+"), msg)
    if not flags:
        await bot.send(event, "请提供请求 flag")
        return
    flag = flags[0]
    if "同意" in msg and "拒绝" in msg:
        await bot.send(event, "请使用同意或拒绝")
    elif "同意" in msg:
        try:
            await bot.set_group_add_request(flag=flag, sub_type="add", approve=True, reason=" ")
            await bot.send(event, "已同意")
        except ActionFailed:
            try:
                await bot.set_group_add_request(flag=flag, sub_type="invite", approve=True, reason=" ")
                await bot.send(event, "已同意")
            except ActionFailed:
                await bot.send(event, "错误：请求不存在")
    elif "拒绝" in msg:
        try:
            await bot.set_group_add_request(flag=flag, sub_type="add", approve=False, reason="管理员拒绝")
            await bot.send(event, "已拒绝")
        except ActionFailed:
            try:
                await bot.set_group_add_request(flag=flag, sub_type="invite", approve=False, reason="管理员拒绝")
                await bot.send(event, "已拒绝")
            except ActionFailed:
                await bot.send(event, "错误：请求不存在")
