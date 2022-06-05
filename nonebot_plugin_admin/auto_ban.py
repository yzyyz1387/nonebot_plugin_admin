# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/29 0:43
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : auto_ban.py
# @Software: PyCharm
from nonebot import logger, on_message, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from nonebot.matcher import Matcher
from .path import *
from .utils import init, banSb, load, check_func_status
from .config import plugin_config
from os import path
from json import dumps as to_json
from aiofiles import open as a_open
from httpx import AsyncClient
import re

cb_notice = plugin_config.callback_notice
cron_update = plugin_config.cron_update
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
    for p in paths_:
        if not path.exists(p):
            await init()
            break
    gid = event.group_id
    level = await load(limit_level)
    status = await check_func_status('auto_ban', str(gid))
    if not status:
        await f_word.finish()
    if str(gid) in level:
        if level[str(gid)] == 'easy':
            limit_path = limit_word_path_easy
        else:
            limit_path = limit_word_path
        rules = [re.sub(r'\t+', '\t', rule).split('\t') for rule in open(limit_path, 'r', encoding='utf-8').read().split('\n')]
        msg = re.sub(r'\s', '', str(event.get_message()))
        logger.info(f"收到消息: \"{msg}\"")
        for rule in rules:
            if rule[0] and re.search(rule[0], msg):
                logger.info(f"敏感词触发: \"{rule[0]}\"")
                matcher.stop_propagation()
                delete, ban = True, True
                if len(rule) > 1:
                    delete = rule[1].find('$撤回') != -1
                    ban = rule[1].find('$禁言') != -1
                if delete:
                    try:
                        await bot.delete_msg(message_id=event.message_id)
                        logger.info('消息已撤回')
                    except ActionFailed:
                        logger.info('消息撤回失败')
                uid = event.get_user_id()
                if ban:
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
    elif cb_notice:
        await f_word.send('本群未配置检测级别，指令如下：\n1.简单违禁词:简单级别\n2.严格违禁词：严格级别\n3.群管初始化：一键配置所有群聊为简单级别\n若重复出现此信息推荐发送【简单违禁词】')

set_level_easy = on_command("简单违禁词", priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
@set_level_easy.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    level = await load(limit_level)
    status = await check_func_status("auto_ban", gid)
    if status:
        if gid not in level or level[gid] != "easy":
            level.update({gid: "easy"})
            async with a_open(limit_level, 'w') as f:
                await f.write(str(to_json(level)))
            await set_level_easy.finish("设置成功")
        else:
            await set_level_easy.finish("本群已经是简单检测了")
    else:
        if cb_notice:
            await set_level_easy.finish("本群未开启此功能，发送【开关违禁词】开启")


set_level_rigorous = on_command("严格违禁词", priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
@set_level_rigorous.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    level = await load(limit_level)
    status = await check_func_status("auto_ban", str(gid))
    if status:
        if gid not in level or level[gid] != 'rigorous':
            level.update({gid: "rigorous"})
            async with a_open(limit_level, 'w') as f:
                await f.write(str(to_json(level)))
            await set_level_rigorous.finish("设置成功")
        else:
            await set_level_rigorous.finish("本群已经是严格检测了")
    else:
        if cb_notice:
            await set_level_easy.finish("本群未开启此功能，发送【开关违禁词】开启")

if cron_update:
    scheduler = require("nonebot_plugin_apscheduler").scheduler
    # 每周一更新违禁词库
    scheduler.add_job(auto_upload_f_words, 'cron', day_of_week='mon', hour=0, minute=0, second=0, id='auto_upload_f_words')
    async def auto_upload_f_words():
        logger.info("自动更新严格违禁词库...")
        async with AsyncClient() as client:
            try:
                r = (await client.get(url="https://fastly.jsdelivr.net/gh/yzyyz1387/nwafu/f_words/f_word_s")).text
            except Exception as err:
                logger.error(f"自动更新严格违禁词库失败：{err}")
                return True
        async with a_open(limit_word_path, "w", encoding='utf-8') as f:
            await f.write(r)
        logger.info("正在更新简单违禁词库")
        async with AsyncClient() as client:
            try:
                r = (await client.get(url="https://fastly.jsdelivr.net/gh/yzyyz1387/nwafu/f_words/f_word_easy")).text
            except Exception as err:
                logger.error(f"自动更新简单违禁词库失败：{err}")
                return True
        async with a_open(limit_word_path_easy, "w", encoding='utf-8') as f:
            await f.write(r)
        logger.info("更新完成")

    update_f_words = on_command("更新违禁词库", priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
    @update_f_words.handle()
    async def _(bot: Bot):
        upload_ = await auto_upload_f_words()
        await update_f_words.finish("更新时出现错误" if upload_ else "更新成功")
