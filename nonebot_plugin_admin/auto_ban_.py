# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/6/25 20:02
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : auto_ban_.py
# @Software: PyCharm
from json import dumps as to_json

from aiofiles import open as a_open
from nonebot import on_message, on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .config import plugin_config
from .path import *
from .utils import load, del_txt_line, add_txt_line, get_txt_line

cb_notice = plugin_config.callback_notice
cron_update = plugin_config.cron_update
paths_ = [config_path, limit_word_path, limit_word_path_easy, limit_level]

f_word = on_message(priority=0, block=False)

set_level_easy = on_command("简单违禁词", priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@set_level_easy.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    level = await load(limit_level)
    if gid not in level or level[gid] != "easy":
        level.update({gid: "easy"})
        async with a_open(limit_level, 'w') as f:
            await f.write(str(to_json(level)))
        await set_level_easy.finish("设置成功")
    else:
        await set_level_easy.finish("本群已经是简单检测了")


set_level_rigorous = on_command("严格违禁词", priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@set_level_rigorous.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    level = await load(limit_level)
    if gid not in level or level[gid] != 'rigorous':
        level.update({gid: "rigorous"})
        async with a_open(limit_level, 'w') as f:
            await f.write(str(to_json(level)))
        await set_level_rigorous.finish("设置成功")
    else:
        await set_level_rigorous.finish("本群已经是严格检测了")


del_custom_limit_words = on_command("删除自定义违禁词", aliases={'移除自定义违禁词', '去除自定义违禁词'}, priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@del_custom_limit_words.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    await del_txt_line(limit_word_path_custom, matcher, event, args, "自定义违禁词")


add_custom_limit_words = on_command("添加自定义违禁词", aliases={'增加自定义违禁词', '新增自定义违禁词'},  priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@add_custom_limit_words.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    await add_txt_line(limit_word_path_custom, matcher, event, args, "自定义违禁词")


get_custom_limit_words = on_command("查看自定义违禁词", aliases={"查看自定义违禁词", "查询自定义违禁词", "自定义违禁词列表"}, priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@get_custom_limit_words.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    await get_txt_line(limit_word_path_custom, matcher, event, args, "自定义违禁词")
