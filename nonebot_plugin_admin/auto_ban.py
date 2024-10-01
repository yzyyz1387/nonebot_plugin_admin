# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/29 0:43
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : auto_ban.py
# @Software: PyCharm
import re

from nonebot import logger, on_message
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.internal.params import Depends
from nonebot.matcher import Matcher

from .message import msg_raw
from .path import *
from .utils import banSb, get_user_violation, sd

def check_msg(text: str, gid: int) -> [bool, bool, str]:
    rules = [re.sub(r'\t+', '\t', i).split('\t') for i in limit_word_path.read_text(encoding='utf-8').split('\n')]
    for rule in rules:
        if not rule[0]: continue
        delete, ban = True, True  # 默认禁言&撤回
        if len(rule) > 1:
            delete, ban = rule[1].find('$撤回') != -1, rule[1].find('$禁言') != -1
            rf = re.search(r'\$(仅限|排除)(([0-9]{6,},?)+)', rule[1])
            if rf:
                chk = rf.groups()
                lst = chk[1].split(',')
                if chk[0] == '仅限':
                    if str(gid) not in lst: continue
                else:
                    if str(gid) in lst: continue
        try:
            if not re.search(rule[0], text): continue
        except:
            if text.find(rule[0]) == -1: continue
        return delete, ban, rule[0]
    return False, False, None

f_word = on_message(priority=1)
@f_word.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, msg: str = Depends(msg_raw)) -> None:
    """
    违禁词禁言
    :param bot:
    :param event:
    :return:
    """
    gid = event.group_id
    uid = event.user_id
    logger.info(f"{gid}收到{uid}的消息: \"{msg}\"")
    delete, ban, rule = check_msg(msg, gid)
    if rule:
        matcher.stop_propagation()  # block
        logger.info(f"敏感词触发: \"{rule}\"")
        if delete:
            try:
                await bot.delete_msg(message_id=event.message_id)
                logger.info('消息已撤回')
            except ActionFailed:
                logger.info('消息撤回失败')
        if ban:
            level = (await get_user_violation(gid, uid, 'Porn', event.raw_message))
            ts: list = time_scop_map[level]
            baning = banSb(bot, gid, ban_list=[uid], scope=ts)
            async for baned in baning:
                if baned:
                    try:
                        await baned
                        await sd(matcher, f"触发违禁词,当前处罚级别为{level}级", at=True)
                        logger.info(f"禁言成功，用户: {uid}")
                    except ActionFailed:
                        logger.info('禁言失败，权限不足')
