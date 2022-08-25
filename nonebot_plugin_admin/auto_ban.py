# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/29 0:43
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : auto_ban.py
# @Software: PyCharm
import re

from nonebot import logger, on_message
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.matcher import Matcher

from .path import *
from .utils import banSb, get_user_violation, sd

f_word = on_message(priority=2, block=False)


@f_word.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    """
    违禁词禁言
    :param bot:
    :param event:
    :return:
    """
    rules = [re.sub(r'\t+', '\t', rule).split('\t') for rule in
             open(limit_word_path, 'r', encoding='utf-8').read().split('\n')]
    msg = re.sub(r'\s', '', str(event.get_message()))
    gid = event.group_id
    logger.info(f"{gid}收到{event.user_id}的消息: \"{msg}\"")
    for rule in rules:
        if rule[0] and re.search(rule[0], msg):  # TODO: 分群配置
            matcher.stop_propagation()  # block
            level = (await get_user_violation(gid, event.user_id, 'Porn', event.raw_message))
            ts: list = time_scop_map[level]
            logger.info(f"敏感词触发: \"{rule[0]}\"")
            delete, ban = True, True  # 默认禁言&撤回
            if len(rule) > 1:
                delete = rule[1].find('$撤回') != -1
                ban = rule[1].find('$禁言') != -1
            if delete:
                try:
                    await bot.delete_msg(message_id=event.message_id)
                    logger.info('消息已撤回')
                except ActionFailed:
                    logger.info('消息撤回失败')
            if ban:
                baning = banSb(gid, ban_list=[event.get_user_id()], scope=ts)
                async for baned in baning:
                    if baned:
                        try:
                            await baned
                            await sd(f_word,
                                     f"你发送了违禁词,现在进行处罚,如有异议请联系管理员\n你的违禁级别为{level}级", True)
                            logger.info(f"禁言成功，用户: {uid}")
                        except ActionFailed:
                            logger.info('禁言失败，权限不足')
            break
