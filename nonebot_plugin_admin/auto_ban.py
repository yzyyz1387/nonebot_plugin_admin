# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/29 0:43
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : auto_ban.py
# @Software: PyCharm
import json
import os
import aiofiles
import re
from nonebot import logger, on_message, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from nonebot.matcher import Matcher
from .path import *
from .utils import init, banSb, auto_upload_f_words, load, check_func_status

paths_ = [config_path, limit_word_path, limit_word_path_easy, limit_level]


f_word = on_message(priority=0, block=False)

@f_word.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    """
    违禁词禁言
    :param bot:
    :param event:
    :return:
    """
    for path_ in paths_:
        if not os.path.exists(path_):
            await init()
    gid = event.group_id
    level = (await load(limit_level))
    status = await check_func_status('auto_ban', str(gid))
    if status:
        if str(gid) in level:
            if level[str(gid)] == 'easy':
                limit_path = limit_word_path_easy
            else:
                limit_path = limit_word_path
            f_words = open(limit_path, 'r', encoding='utf-8').read().split('\n')
            msg = re.sub(r'\s', '', str(event.get_message()))
            logger.info(f"收到消息: \"{msg}\"")
            for words in f_words:
                if words and re.search(words, msg):
                    uid = event.get_user_id()
                    logger.info(f"敏感词触发: \"{words}\"")
                    matcher.stop_propagation()
                    try:
                        await bot.delete_msg(message_id=event.message_id)
                        logger.info('消息已撤回')
                    except ActionFailed:
                        logger.info('消息撤回失败')
                    baning = banSb(gid, ban_list=[uid])
                    async for baned in baning:
                        if baned:
                            try:
                                await baned
                            except ActionFailed:
                                logger.info('禁言失败，权限不足')
                                await f_word.send('禁言失败，权限不足')
                            else:
                                logger.info(f"禁言成功，用户: {uid}")
                                await f_word.send('你发送了违禁词,现在进行处罚,如有异议请联系管理员', at_sender=True)
                    break
        else:
            await f_word.finish('本群未配置检测级别，指令如下：\n1.简单违禁词:简单级别\n2.严格违禁词：严格级别\n3.群管初始化：一键配置所有群聊为简单级别\n若重复出现此信息推荐发送【简单违禁词】')
    else:
        pass


set_level_easy = on_command("简单违禁词", priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)

@set_level_easy.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    level = (await load(limit_level))
    status = await check_func_status("auto_ban", gid)
    if status:
        if gid not in level or level[gid] != "easy":
            level.update({gid: "easy"})
            async with aiofiles.open(limit_level, mode='w') as c:
                await c.write(str(json.dumps(level)))
            await set_level_easy.send("完成")
        else:
            await set_level_easy.send("本群已经是简单检测了")
    else:
        await set_level_easy.send("本群未开启此功能，发送【开关违禁词】开启")


set_level_rigorous = on_command("严格违禁词", priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)

@set_level_rigorous.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    level = (await load(limit_level))
    status = await check_func_status("auto_ban", str(gid))
    if status:
        if gid not in level or level[gid] != 'rigorous':
            level.update({gid: "rigorous"})
            async with aiofiles.open(limit_level, mode='w') as c:
                await c.write(str(json.dumps(level)))
            await set_level_rigorous.send("完成")
        else:
            await set_level_rigorous.send("本群已经是严格检测了")
    else:
        await set_level_easy.send("本群未开启此功能，发送【开关违禁词】开启")


update_f_words = on_command("更新违禁词库", priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)

@update_f_words.handle()
async def _(bot: Bot):
    upload_ = await auto_upload_f_words()
    if upload_:
        await update_f_words.send("更新时出现错误")
    else:
        await update_f_words.send("done!")

