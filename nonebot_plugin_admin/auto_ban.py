# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/29 0:43
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : auto_ban.py
# @Software: PyCharm
import os
import json
import aiofiles
from pathlib import Path
from nonebot import logger, on_message, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from .utils import init, banSb
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER

config_path = Path() / "config"
limit_word_path = config_path / "违禁词.txt"
limit_word_path_easy = config_path / "违禁词_简单.txt"
limit_level = config_path / "违禁词监控等级.json"

f_word = on_message(priority=1, block=False)


@f_word.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    违禁词禁言
    :param bot:
    :param event:
    :return:
    """
    await init()
    gid = event.group_id
    uid = [event.get_user_id()]
    eid = event.message_id
    msg = str(event.get_message()).replace(" ", "")
    level = (await load_level())
    if str(gid) in level:
        if level[str(gid)] == 'easy':
            limit_path = limit_word_path_easy
        else:
            limit_path = limit_word_path
        f_words = open(limit_path, 'r', encoding='utf-8').read().split('\n')
        for words in f_words:
            if words and words in msg:
                logger.info(f"敏感词触发:\"{words}\"")
                try:
                    await bot.delete_msg(message_id=eid)
                    logger.info('检测到违禁词，撤回')
                except ActionFailed:
                    logger.info('检测到违禁词，但权限不足，撤回失败')
                baning = banSb(gid, ban_list=uid)
                async for baned in baning:
                    if baned:
                        try:
                            await baned
                        except ActionFailed:
                            await f_word.finish("检测到违禁词，但权限不足")
                            logger.info('检测到违禁词，但权限不足，禁言失败')
                        else:
                            await bot.send(event=event, message="发送了违禁词,现对你进行处罚,有异议请联系管理员", at_sender=True)
                            logger.info(f"检测到违禁词，禁言操作成功，用户: {uid[0]}")
                break
    else:
        await f_word.send("本群未配置检测级别，指令如下：\n1.简单违禁:简单级别\n2.严格违禁词：严格级别\n3.群管初始化：一键配置所有群聊为简单级别")


async def load_level() -> dict:
    async with aiofiles.open(limit_level, mode='r') as c:
        level_ = await c.read()
        level = json.loads(level_)
        return level


set_level_easy = on_command("简单违禁词", priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@set_level_easy.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    level = await load_level()
    if gid not in level or level[gid] != "easy":
        data = level.update({gid: "easy"})
        async with aiofiles.open(limit_level, mode='w') as c:
            await c.write(str(json.dumps(data)))
        await set_level_easy.send("完成")
    else:
        await set_level_easy.send("本群已经是简单检测了")


set_level_rigorous = on_command("严格违禁词", priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@set_level_rigorous.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    level = await load_level()
    if gid not in level or level[gid] != 'rigorous':
        data = level.update({gid: "rigorous"})
        async with aiofiles.open(limit_level, mode='w') as c:
            await c.write(str(json.dumps(data)))
        await set_level_rigorous.send("完成")
    else:
        await set_level_rigorous.send("本群已经是严格检测了")
