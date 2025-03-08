# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/29 0:43
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : auto_ban.py
# @Software: PyCharm
from nonebot import logger, on_message, on_command
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.adapters import Message
from nonebot.params import CommandArg

from .config import plugin_config
from .message import *
from .path import *
from .utils import mute_sb, get_user_violation, sd, del_txt_line, add_txt_line, get_txt_line
from typing import Tuple

cb_notice = plugin_config.callback_notice

del_custom_limit_words = on_command('删除违禁词', priority=2, aliases={'移除违禁词', '去除违禁词'}, block=True,
                                    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@del_custom_limit_words.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    await del_txt_line(limit_word_path, matcher, args, '违禁词')


# TODO: 支持配置是否撤回&禁言
add_custom_limit_words = on_command('添加违禁词', priority=2, aliases={'增加违禁词', '新增违禁词'}, block=True,
                                    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@add_custom_limit_words.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    await add_txt_line(limit_word_path, matcher, args, '违禁词')


get_custom_limit_words = on_command('查看违禁词', priority=2, aliases={'查看违禁词', '查询违禁词', '违禁词列表'},
                                    block=True, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@get_custom_limit_words.handle()
async def _(matcher: Matcher):
    if cb_notice:
        await get_txt_line(limit_word_path, matcher, '违禁词')


def check_msg(text: str, gid: int) -> Tuple[bool, bool, str]:
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
        except Exception:
            if text.find(rule[0]) == -1: continue
        return delete, ban, rule[0]
    return False, False, None


# priority等级要比del_custom_limit_words低 否则在删除违禁词时会触发一次无效的检测
f_word = on_message(priority=3, block=False)


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
    if not rule:
        return

    matcher.stop_propagation()  # block
    logger.info(f"敏感词触发: \"{rule}\"")
    if delete:
        try:
            await bot.delete_msg(message_id=event.message_id)
            logger.info('消息已撤回')
        except ActionFailed:
            logger.info('消息撤回失败')
    if ban:
        level = await get_user_violation(gid, uid, f"敏感词: {rule}", event.raw_message)
        mute_lst = mute_sb(bot, gid, lst=[uid], scope=time_scop_map[level])
        async for mute in mute_lst:
            if not mute:
                continue
            
            try:
                await mute
                await sd(matcher, f"触发违禁词,当前处罚级别为{level}级", at=True)
                logger.info(f"禁言成功，用户: {uid}")
            except ActionFailed:
                logger.info('禁言失败，权限不足')
