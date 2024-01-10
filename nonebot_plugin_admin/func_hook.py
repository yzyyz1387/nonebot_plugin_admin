# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/6/25 17:52
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : func_hook.py
# @Software: PyCharm
import nonebot
from nonebot import logger
from nonebot.adapters.onebot.v11 import (
    Bot,
    ActionFailed,
    GroupMessageEvent,
    GroupRequestEvent,
    Event,
    HonorNotifyEvent,
    GroupUploadNoticeEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupAdminNoticeEvent,
    LuckyKingNotifyEvent,
    GroupRecallNoticeEvent
)
from nonebot.matcher import Matcher
from nonebot.message import run_preprocessor, IgnoredException
from nonebot.typing import T_State

from .switcher import switcher_integrity_check
from .config import plugin_config, global_config
from .path import *
from .utils import json_load

cb_notice = plugin_config.callback_notice
su = global_config.superusers
admin_path = Path(__file__).parts[-2]


@run_preprocessor
async def _(matcher: Matcher, bot: Bot, state: T_State, event: Event):
    module = str(matcher.module_name).split('.')
    if len(module) < 2 or module[-2] != admin_path: return  # 位置与文件路径有关
    which_module = module[-1]
    # logger.info(f"{which_module}插件开始hook处理")
    if isinstance(event, (
            GroupMessageEvent,
            HonorNotifyEvent,
            GroupUploadNoticeEvent,
            GroupDecreaseNoticeEvent,
            GroupIncreaseNoticeEvent,
            GroupAdminNoticeEvent,
            LuckyKingNotifyEvent,
            GroupRecallNoticeEvent
            )
                  ):
        gid = event.group_id
        try:
            if which_module in admin_funcs:
                status = await check_func_status(which_module, str(gid))
                if not status and which_module not in ['auto_ban',
                                                       'img_check',
                                                       'particular_e_notice',
                                                       'word_analyze',
                                                       'group_recall']:  # 违禁词检测和图片检测日志太多了，不用logger记录或者发消息记录
                    if cb_notice:
                        await bot.send_group_msg(group_id=gid,
                                                 message=f"功能处于关闭状态，发送【开关{admin_funcs[which_module][0]}】开启")
                    raise IgnoredException('未开启此功能...')
                elif not status and which_module in ['auto_ban',
                                                     'img_check',
                                                     'particular_e_notice',
                                                     'word_analyze',
                                                     'group_recall']:
                    raise IgnoredException('未开启此功能...')
        except ActionFailed:
            pass
        except FileNotFoundError:
            pass
    elif isinstance(event, GroupRequestEvent):
        gid = event.group_id
        try:
            if which_module == 'requests':
                logger.info(event.flag)
                if event.sub_type == 'add':
                    status = await check_func_status(which_module, str(gid))
                    if status is False:
                        re_msg = f"群{gid}收到{event.user_id}的加群请求，flag为：{event.flag}，但审批处于关闭状态\n发送【请求同意/拒绝 " \
                                 f"flag】来处理次请求，例：\n请求同意{event.flag}\n发送【开关{admin_funcs[which_module][0]}】开启，或人工审批 "
                        logger.info(re_msg)
                        if cb_notice:
                            try:
                                for qq in su:
                                    await bot.send_msg(user_id=qq, message=re_msg)
                            except ActionFailed:
                                logger.info('发送消息失败,可能superuser之一不是好友')
                        raise IgnoredException('未开启此功能...')
                else:
                    pass
        except ActionFailed:
            pass
        except FileNotFoundError:
            pass


async def check_func_status(func_name: str, gid: str) -> bool:
    """
    检查某个群的某个功能是否开启
    :param func_name: 功能名
    :param gid: 群号
    :return: bool
    """
    funcs_status = json_load(switcher_path)
    if funcs_status is None:
        raise FileNotFoundError(switcher_path)
    try:
        return bool(funcs_status[gid][func_name])
    except KeyError:  # 新加入的群
        logger.info(
            f"本群({gid})尚未初始化！将自动初始化：关闭所有开关且设置过滤级别为简单。\n\n请重新发送指令继续之前的操作")
        if cb_notice:
            # await nonebot.get_bot().send_group_msg(group_id = gid, message = '本群尚未初始化，将自动初始化：开启所有开关且设置过滤级别为简单。\n\n'
            #                                                              '请重新发送指令继续之前的操作')
            logger.info('错误发生在 utils.py line 398')
        bots = nonebot.get_bots()
        for bot in bots.values():
            await switcher_integrity_check(bot)
        return False  # 直接返回 false
