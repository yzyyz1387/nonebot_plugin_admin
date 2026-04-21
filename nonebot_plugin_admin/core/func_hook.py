# python3
# -*- coding: utf-8 -*-

import nonebot
from nonebot import logger
from nonebot.adapters.onebot.v11 import (
    ActionFailed,
    Bot,
    Event,
    GroupAdminNoticeEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupMessageEvent,
    GroupRecallNoticeEvent,
    GroupRequestEvent,
    GroupUploadNoticeEvent,
    HonorNotifyEvent,
    LuckyKingNotifyEvent,
)
from nonebot.matcher import Matcher
from nonebot.message import IgnoredException, run_preprocessor

from .config import global_config, plugin_config
from .path import admin_funcs, is_default_enabled
from .switcher import switcher_integrity_check
from ..statistics.config_orm_store import orm_load_switcher

cb_notice = plugin_config.callback_notice
su = global_config.superusers
PLUGIN_PACKAGE_PREFIX = __name__.rsplit('.', 2)[0]
SILENT_DISABLED_FUNCS = {
    'auto_ban',
    'img_check',
    'particular_e_notice',
    'word_analyze',
    'group_recall',
}


@run_preprocessor
async def _(matcher: Matcher, bot: Bot, event: Event):
    module_name = str(matcher.module_name)
    if not module_name.startswith(f'{PLUGIN_PACKAGE_PREFIX}.'):
        return

    module_parts = module_name.split('.')
    if len(module_parts) < 2:
        return

    which_module = module_parts[-1]

    if isinstance(
        event,
        (
            GroupMessageEvent,
            HonorNotifyEvent,
            GroupUploadNoticeEvent,
            GroupDecreaseNoticeEvent,
            GroupIncreaseNoticeEvent,
            GroupAdminNoticeEvent,
            LuckyKingNotifyEvent,
            GroupRecallNoticeEvent,
        ),
    ):
        gid = str(event.group_id)
        try:
            if which_module in admin_funcs:
                status = await check_func_status(which_module, gid)
                if not status:
                    logger.info(
                        f'群 {gid} 功能 {which_module} 已关闭，取消 matcher {module_name}'
                    )
                    if cb_notice and which_module not in SILENT_DISABLED_FUNCS:
                        await bot.send_group_msg(
                            group_id=event.group_id,
                            message=f'功能处于关闭状态，发送【开关{admin_funcs[which_module][0]}】开启',
                        )
                    raise IgnoredException('未开启此功能')
        except ActionFailed:
            return

    if isinstance(event, GroupRequestEvent) and which_module == 'requests':
        gid = str(event.group_id)
        if event.sub_type != 'add':
            return
        try:
            status = await check_func_status(which_module, gid)
            if status:
                return

            logger.info(event.flag)
            notify_message = (
                f'群 {gid} 收到 {event.user_id} 的加群请求，flag 为 {event.flag}，但审批功能处于关闭状态。\n'
                f'发送【请求同意{event.flag}】或【请求拒绝{event.flag}】处理本次请求，'
                f'或者发送【开关{admin_funcs[which_module][0]}】开启自动审批。'
            )
            logger.info(notify_message)
            if cb_notice:
                try:
                    for qq in su:
                        await bot.send_msg(user_id=qq, message=notify_message)
                except ActionFailed:
                    logger.info('向 superuser 发送关闭提醒失败，可能不是好友')
            raise IgnoredException('未开启此功能')
        except (ActionFailed, FileNotFoundError):
            return


async def check_func_status(func_name: str, gid: str) -> bool:
    """
    检查funcstatus
    :param func_name: 功能名
    :param gid: 群号
    :return: bool
    """
    orm_data = await orm_load_switcher()
    group_data = orm_data.get(gid, {})
    if func_name in group_data:
        return bool(group_data[func_name])

    logger.info(f'群 {gid} 功能 {func_name} 尚未初始化，正在自动补齐开关配置')
    bots = nonebot.get_bots()
    for bot in bots.values():
        await switcher_integrity_check(bot)
    refreshed_status = await orm_load_switcher()
    status = bool(refreshed_status.get(gid, {}).get(func_name, is_default_enabled(func_name)))
    logger.info(f'群 {gid} 功能 {func_name} 自动补齐后状态：{"开启" if status else "关闭"}')
    return status
