# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/6/25 17:52
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : func_hook.py
# @Software: PyCharm
from nonebot import logger
from nonebot.matcher import Matcher
from nonebot.message import run_preprocessor, IgnoredException
from .utils import check_func_status
from nonebot.typing import T_State
from typing import Optional
from .path import *
from nonebot.adapters.onebot.v11 import (
    Bot,
    ActionFailed,
    MessageEvent,
    GroupMessageEvent,
    GroupRequestEvent,
    PokeNotifyEvent,
    PrivateMessageEvent,
    Message,
    Event,
)
from .config import plugin_config, global_config

cb_notice = plugin_config.callback_notice
su = global_config.superusers


@run_preprocessor
async def _(matcher: Matcher, bot: Bot, state: T_State, event: Event):
    which_module = str(matcher.module_name).split(".")[-1]
    # logger.info(f"{which_module}插件开始hook处理")
    if isinstance(event, GroupMessageEvent):
        gid = event.group_id
        try:
            if "开关" not in event.get_message():
                if which_module in admin_funcs:
                    status = await check_func_status(which_module, str(gid))
                    if not status and which_module not in ['auto_ban',
                                                           'img_check']:  # 违禁词检测和图片检测日志太多了，不用logger记录或者发消息记录
                        logger.info(
                            f"{admin_funcs[which_module][0]}功能处于关闭状态，若要启用请发送【开关{admin_funcs[which_module][0]}】开启")
                        if cb_notice:
                            await bot.send_group_msg(group_id=gid,
                                                     message=f"功能处于关闭状态，发送【开关{admin_funcs[which_module][0]}】开启")
                        raise IgnoredException("未开启此功能...")
                    elif not status and which_module in ['auto_ban',
                                                           'img_check']:
                        logger.info(
                            f"{admin_funcs[which_module][0]}功能处于关闭状态，若要启用请发送【开关{admin_funcs[which_module][0]}】开启")
                        raise IgnoredException("未开启此功能...")
            else:
                pass
        except ActionFailed:
            pass
        except FileNotFoundError:
            pass
    elif isinstance(event, GroupRequestEvent):
        gid = event.group_id
        try:
            if which_module == 'request':
                logger.info(event.flag)
                status = await check_func_status(which_module, str(gid))
                if not status:
                    re_msg = f"群{gid}收到{event.user_id}的加群请求，flag为：{event.flag}，但审批处于关闭状态\n发送【请求同意/拒绝 " \
                             f"flag】来处理次请求，例：\n请求同意{event.flag}\n发送【开关{admin_funcs[which_module][0]}】开启，或人工审批 "
                    logger.info(re_msg)
                    if cb_notice:
                        try:
                            for qq in su:
                                await bot.send_msg(user_id=qq,
                                                   message=re_msg)
                        except ActionFailed:
                            logger.info("发送消息失败,可能superuser之一不是好友")
                            pass

                    raise IgnoredException("未开启此功能...")
        except ActionFailed:
            pass
        except FileNotFoundError:
            pass
