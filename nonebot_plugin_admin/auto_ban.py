# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/29 0:43
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : auto_ban.py
# @Software: PyCharm
import os
from pathlib import Path

from nonebot import logger, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed

from .utils import init, banSb

config_path = Path() / "config"
limit_word_path = config_path / "违禁词.txt"

f_word = on_message(priority=1)


@f_word.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    违禁词禁言
    :param bot:
    :param event:
    :return:
    """
    if not os.path.exists(limit_word_path):
        await init()
    gid = event.group_id
    uid = [event.get_user_id]
    eid = event.message_id
    msg = str(event.get_message()).replace(" ", "")
    f_words = open(limit_word_path, 'r', encoding='utf-8').read().split('\n')
    for words in f_words:
        if words and words in msg:
            logger.info(f"敏感词触发{words}")
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
