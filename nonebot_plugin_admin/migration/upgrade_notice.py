from __future__ import annotations

import datetime

import nonebot
from nonebot import logger

from ..core.config import plugin_config
from ..dashboard.dashboard_web import build_dashboard_runtime_url, normalize_dashboard_base_path
from ..statistics.config_orm_store import orm_get_global_config, orm_set_global_config
from .migrate import has_isolated_legacy_backup, has_legacy_migration_targets

_LEGACY_UPGRADE_NOTICE_KEY = "legacy_text_upgrade_notice_sent_at"


def _load_superusers() -> list[str]:
    """
    加载superusers
    :return: list[str]
    """
    driver = nonebot.get_driver()
    superusers = getattr(driver.config, "superusers", set()) or set()
    return [str(user_id).strip() for user_id in superusers if str(user_id).strip()]


def _needs_legacy_upgrade_notice() -> bool:
    """
    处理 _needs_legacy_upgrade_notice 的业务逻辑
    :return: bool
    """
    return has_legacy_migration_targets() or has_isolated_legacy_backup()


async def _notice_already_sent() -> bool:
    """
    处理 _notice_already_sent 的业务逻辑
    :return: bool
    """
    if not plugin_config.statistics_orm_enabled:
        return False
    value = await orm_get_global_config(_LEGACY_UPGRADE_NOTICE_KEY, "")
    return bool(str(value).strip())


async def _mark_notice_sent() -> None:
    """
    处理 _mark_notice_sent 的业务逻辑
    :return: None
    """
    if not plugin_config.statistics_orm_enabled:
        return
    await orm_set_global_config(
        _LEGACY_UPGRADE_NOTICE_KEY,
        datetime.datetime.now().isoformat(timespec="seconds"),
    )


def build_legacy_upgrade_notice_message() -> str:
    """
    构建旧版upgrade通知消息
    :return: str
    """
    driver = nonebot.get_driver()
    db_url = str(getattr(driver.config, "tortoise_orm_db_url", "") or "").strip()
    dashboard_url = build_dashboard_runtime_url(
        normalize_dashboard_base_path(plugin_config.dashboard_base_path)
    )

    lines = [
        "检测到当前实例可能是从旧版文本存储时代升级而来。",
        "建议尽快把持久化和后台能力切到数据库方案：",
        "1. 配置 tortoise_orm_db_url：这是数据库地址，审批、开关、统计、词料、违规记录等数据会集中存到这里。",
        f"   当前数据库地址：{db_url or '未配置'}",
        f"2. 设置 statistics_orm_enabled=true：启用 ORM 作为运行时主存储。当前状态：{'已开启' if plugin_config.statistics_orm_enabled else '未开启'}",
        f"3. 设置 dashboard_enabled=true，并建议同时设置 dashboard_frontend_enabled=true：开启后台 API 和网页管理界面。当前状态：{'已开启' if plugin_config.dashboard_enabled else '未开启'}",
        "4. 配置 dashboard_api_token：这是后台 API 的访问令牌，用于保护管理接口；访问受保护接口时需要在请求头里携带 X-Admin-Token。",
        f"   Token 状态：{'已配置' if plugin_config.dashboard_api_token.strip() else '未配置'}",
        f"{'后台地址' if plugin_config.dashboard_enabled else '开启后后台地址'}：{dashboard_url}",
        "推荐配置示例：",
        "tortoise_orm_db_url=sqlite:///data/admin3-statistics.db",
        "statistics_orm_enabled=true",
        "dashboard_enabled=true",
        "dashboard_frontend_enabled=true",
        "dashboard_api_token=<请替换为随机长字符串>",
    ]
    return "\n".join(lines)


async def notify_legacy_text_upgrade(bot: nonebot.adapters.Bot) -> bool:
    """
    通知旧版文本upgrade
    :param bot: Bot 实例
    :return: bool
    """
    if not _needs_legacy_upgrade_notice():
        return False
    if await _notice_already_sent():
        return False

    superusers = _load_superusers()
    if not superusers:
        return False

    message = build_legacy_upgrade_notice_message()
    sent = False
    for user_id in superusers:
        try:
            await bot.send_msg(user_id=int(user_id), message=message)
            sent = True
        except Exception as err:
            logger.warning(
                f"Legacy upgrade notice failed for superuser {user_id}: {type(err).__name__}: {err}"
            )

    if sent:
        await _mark_notice_sent()
    return sent
