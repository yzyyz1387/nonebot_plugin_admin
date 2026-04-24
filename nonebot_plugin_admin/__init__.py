# python3
# -*- coding: utf-8 -*-

import inspect

import nonebot
from nonebot import logger

from .approval import ai_group_verify as _approval_ai_group_verify
from .approval import notice as _approval_notice
from .approval import request_manual as _approval_request_manual
from .approval import requests as _approval_requests
from .basic_group_admin import admin as _basic_group_admin
from .broadcasting import broadcast as _broadcasting
from .content_guard import auto_ban as _content_guard_auto_ban
from .content_guard import img_check as _content_guard_img_check
from .core import func_hook as _core_func_hook
from .core import menu_items as _core_menu_items
from .core import menu_command as _core_menu_command
from .core import db_command as _core_db_command
from .core import switcher, utils
from .core.config import Config
from .dashboard import dashboard_web as _dashboard_web
from .dashboard.dashboard_command import dashboard_url_cmd as _dashboard_url_cmd
from .dashboard.dashboard_oplog_service import record_oplog
from .event_notice import group_recall as _event_notice_group_recall
from .event_notice import particular_e_notice as _event_notice_particular_notice
from .member_cleanup import kick_member_by_rule as _member_cleanup_kick_rule
from .migration import notify_legacy_text_upgrade, run_migration_check
from .statistics.orm_bootstrap import ensure_statistics_orm_support as _ensure_statistics_orm_support

_ensure_statistics_orm_support()

from .statistics import group_msg as _statistics_group_msg
from .statistics import word_analyze as _statistics_word_analyze
from .statistics import wordcloud as _statistics_wordcloud


def build_plugin_metadata():
    """
    构建pluginmetadata
    :return: None
    """
    metadata_kwargs = {
        "name": "不简易群管",
        "description": "NoneBot2 群管理插件",
        "usage": "包含基础群管、加群审批、内容检测、统计分析、广播、事件提醒等功能。",
        "type": "application",
        "homepage": "https://github.com/yzyyz1387/nonebot_plugin_admin",
        "config": Config,
        "supported_adapters": None,
    }
    metadata_cls = nonebot.plugin.PluginMetadata
    try:
        parameters = inspect.signature(metadata_cls).parameters
        filtered_kwargs = {key: value for key, value in metadata_kwargs.items() if key in parameters}
    except (TypeError, ValueError):
        filtered_kwargs = metadata_kwargs
    return metadata_cls(**filtered_kwargs)


driver = nonebot.get_driver()
_dashboard_web.register_dashboard_routes()


@driver.on_bot_connect
async def _(bot: nonebot.adapters.Bot):
    bot_id = str(getattr(bot, "self_id", "unknown"))
    await record_oplog(
        action="bot_connect",
        detail=f"Bot [{bot_id}] 已连接",
        extra={"bot_id": bot_id},
    )
    await utils.init()
    await switcher.switcher_integrity_check(bot)
    await run_migration_check()
    await notify_legacy_text_upgrade(bot)


@driver.on_bot_disconnect
async def _(bot: nonebot.adapters.Bot):
    bot_id = str(getattr(bot, "self_id", "unknown"))
    await record_oplog(
        action="bot_disconnect",
        detail=f"Bot [{bot_id}] 已断开连接",
        extra={"bot_id": bot_id},
    )


@driver.on_startup
async def _():
    await record_oplog(
        action="plugin_startup",
        detail="Admin 插件已启动",
    )


@driver.on_shutdown
async def _():
    await record_oplog(
        action="plugin_shutdown",
        detail="Admin 插件收到停止信号，正在执行停机清理",
    )
    cleared = utils.clear_all_cleanup_locks()
    logger.info(f"Admin 插件停机清理完成，共清理 {cleared} 个成员清理锁文件")


__plugin_meta__ = build_plugin_metadata()


__usage__ = """
【初始化】
  群管初始化

【群管菜单】
  群管菜单

【基础群管】
  禁 / 解 / 改 / 踢 / 黑 / 管理员+ / 管理员- / 头衔 / 删头衔 / 撤回 / 加精 / 取消精华

【加群审批】
  查看词条 / 词条+ / 词条- / 词条拒绝
  所有词条 / 指定词条+ / 指定词条-
  分管 / 分管+ / 分管- / 所有分管 / 接收
  请求同意xxx / 请求拒绝xxx
  开关AI审批 / ai拒绝prompt

【统计分析】
  记录本群 / 停止记录本群 / 群词云 / 更新mask
  今日榜首 / 今日发言排行 / 昨日发言排行 / 排行 / 发言数 / 今日发言数
  早安晚安推送

【广播】
  广播 / 群列表 / 排除列表 / 广播排除 / 广播帮助
  广播发送前会先预览，二次确认后才会真正发送

【事件提醒】
  事件通知 / 防撤回

【成员清理】
  成员清理 / 清理解锁

【Dashboard】
  面板地址 / 获取面板 / dashboard地址
"""

__help_plugin_name__ = "简易群管"
__permission__ = 1
__help__version__ = "0.2.0"
