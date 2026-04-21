from __future__ import annotations

import json
from typing import Any

from nonebot import logger

from ..core.config import plugin_config
from ..statistics import models
from ..statistics.orm_bootstrap import ensure_dashboard_orm_support

OPLOG_ACTION_LABELS = {
    "send_message": "发送群消息",
    "whole_ban": "全员禁言",
    "mute_member": "禁言成员",
    "kick_member": "踢出成员",
    "special_title": "设置头衔",
    "feature_switch": "功能开关",
    "broadcast": "广播消息",
    "mark_read": "标记已读",
    "bot_connect": "Bot连接",
    "bot_disconnect": "Bot断开",
    "plugin_startup": "插件启动",
    "plugin_shutdown": "插件停机",
    "message_record": "消息入库",
    "ai_approval": "AI审批",
    "plugin_error": "插件错误",
}

OPLOG_LEVEL_MAP = {
    "send_message": "INFO",
    "whole_ban": "WARNING",
    "mute_member": "WARNING",
    "kick_member": "WARNING",
    "special_title": "INFO",
    "feature_switch": "INFO",
    "broadcast": "WARNING",
    "mark_read": "DEBUG",
    "bot_connect": "SUCCESS",
    "bot_disconnect": "WARNING",
    "plugin_startup": "SUCCESS",
    "plugin_shutdown": "WARNING",
    "message_record": "DEBUG",
    "ai_approval": "INFO",
    "plugin_error": "ERROR",
}


def _is_oplog_available() -> bool:
    """
    处理 _is_oplog_available 的业务逻辑
    :return: bool
    """
    if models.ORM_MODELS_AVAILABLE and models.DashboardOplogRecord is not None:
        return True
    ensure_dashboard_orm_support()
    return bool(models.ORM_MODELS_AVAILABLE and models.DashboardOplogRecord is not None)


async def record_oplog(
    *,
    action: str,
    group_id: str | int | None = None,
    user_id: str | int | None = None,
    detail: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    记录操作日志
    :param action: action 参数
    :param group_id: 群号
    :param user_id: 用户号
    :param detail: detail 参数
    :param extra: extra 参数
    :return: dict[str, Any]
    """
    if not _is_oplog_available():
        return {}

    level = OPLOG_LEVEL_MAP.get(action, "INFO")
    action_label = OPLOG_ACTION_LABELS.get(action, action)
    message = f"{action_label}: {detail}" if detail else action_label

    try:
        record = await models.DashboardOplogRecord.create(
            action=action,
            action_label=action_label,
            level=level,
            group_id=str(group_id) if group_id is not None else None,
            user_id=str(user_id) if user_id is not None else None,
            detail=detail,
            message=message,
            extra_json=json.dumps(extra or {}, ensure_ascii=False),
        )
        logger.debug(f"dashboard oplog recorded: {action} group={group_id} user={user_id} detail={detail}")
        return {
            "id": record.id,
            "action": action,
            "action_label": action_label,
            "level": level,
            "group_id": str(group_id) if group_id is not None else None,
            "user_id": str(user_id) if user_id is not None else None,
            "detail": detail,
            "message": message,
        }
    except Exception as err:
        logger.warning(f"dashboard oplog write failed: {type(err).__name__}: {err}")
        return {}


def _record_to_dict(record: Any) -> dict[str, Any]:
    """
    记录todict
    :param record: record 参数
    :return: dict[str, Any]
    """
    extra_data = {}
    if hasattr(record, "extra_json") and record.extra_json:
        try:
            extra_data = json.loads(record.extra_json)
        except (json.JSONDecodeError, TypeError):
            extra_data = {}

    return {
        "id": f"oplog-{record.id}",
        "source": "dashboard_oplog",
        "level": str(record.level),
        "timestamp": record.created_at.isoformat() if record.created_at else None,
        "group_id": str(record.group_id) if record.group_id else None,
        "user_id": str(record.user_id) if record.user_id else None,
        "action": str(record.action),
        "action_label": str(record.action_label),
        "message": str(record.message),
        "detail": str(record.detail),
        "extra": extra_data,
    }


async def load_oplog_entries(
    *,
    limit: int = 600,
    action: str = "",
    group_id: str = "",
    level: str = "",
    keyword: str = "",
) -> list[dict[str, Any]]:
    """
    加载操作日志entries
    :param limit: 数量限制
    :param action: action 参数
    :param group_id: 群号
    :param level: level 参数
    :param keyword: 关键字
    :return: list[dict[str, Any]]
    """
    if not _is_oplog_available():
        return []

    query = models.DashboardOplogRecord.all()

    normalized_action = str(action or "").strip().lower()
    normalized_group_id = str(group_id or "").strip()
    normalized_level = str(level or "").strip().upper()
    normalized_keyword = str(keyword or "").strip().lower()

    if normalized_action:
        query = query.filter(action=normalized_action)
    if normalized_group_id:
        query = query.filter(group_id=normalized_group_id)
    if normalized_level:
        query = query.filter(level=normalized_level)
    if normalized_keyword:
        query = query.filter(message__icontains=normalized_keyword)

    query = query.order_by("-created_at")

    if limit > 0:
        query = query.limit(limit)

    records = await query
    return [_record_to_dict(record) for record in records]


async def build_oplog_payload(
    *,
    page: int = 1,
    page_size: int = 50,
    action: str = "",
    group_id: str = "",
    level: str = "",
    keyword: str = "",
) -> dict[str, Any]:
    """
    构建操作日志payload
    :param page: 页码
    :param page_size: 分页大小
    :param action: action 参数
    :param group_id: 群号
    :param level: level 参数
    :param keyword: 关键字
    :return: dict[str, Any]
    """
    if not _is_oplog_available():
        return {
            "items": [],
            "pagination": {"page": 1, "page_size": page_size, "total": 0, "total_pages": 1, "has_prev": False, "has_next": False},
            "filters": {"action": action or None, "group_id": group_id or None, "level": level or None, "keyword": keyword or None},
            "action_options": [],
            "level_totals": {},
            "enabled": False,
        }

    normalized_page = max(int(page), 1)
    normalized_page_size = max(1, min(int(page_size), 200))

    query = models.DashboardOplogRecord.all()

    normalized_action = str(action or "").strip().lower()
    normalized_group_id = str(group_id or "").strip()
    normalized_level = str(level or "").strip().upper()
    normalized_keyword = str(keyword or "").strip().lower()

    if normalized_action:
        query = query.filter(action=normalized_action)
    if normalized_group_id:
        query = query.filter(group_id=normalized_group_id)
    if normalized_level:
        query = query.filter(level=normalized_level)
    if normalized_keyword:
        query = query.filter(message__icontains=normalized_keyword)

    total = await query.count()
    total_pages = max(1, (total + normalized_page_size - 1) // normalized_page_size) if total else 1
    start = (normalized_page - 1) * normalized_page_size

    records = await query.order_by("-created_at").offset(start).limit(normalized_page_size)
    items = [_record_to_dict(record) for record in records]

    action_counts: dict[str, int] = {}
    for act_key in OPLOG_ACTION_LABELS:
        count = await models.DashboardOplogRecord.filter(action=act_key).count()
        if count > 0:
            action_counts[act_key] = count

    level_counts: dict[str, int] = {}
    for lv in ("ERROR", "WARNING", "INFO", "DEBUG", "SUCCESS"):
        count = await models.DashboardOplogRecord.filter(level=lv).count()
        if count > 0:
            level_counts[lv] = count

    return {
        "items": items,
        "pagination": {
            "page": normalized_page,
            "page_size": normalized_page_size,
            "total": total,
            "total_pages": total_pages,
            "has_prev": normalized_page > 1,
            "has_next": normalized_page < total_pages,
        },
        "filters": {
            "action": action or None,
            "group_id": group_id or None,
            "level": level or None,
            "keyword": keyword or None,
        },
        "action_options": [
            {"key": act, "label": OPLOG_ACTION_LABELS.get(act, act), "count": action_counts.get(act, 0)}
            for act in OPLOG_ACTION_LABELS
        ],
        "level_totals": level_counts,
        "enabled": True,
    }


async def build_oplog_overview_payload() -> dict[str, Any]:
    """
    构建操作日志overviewpayload
    :return: dict[str, Any]
    """
    if not _is_oplog_available():
        return {
            "total": 0,
            "enabled": False,
            "action_counts": {},
            "level_totals": {},
            "latest": [],
        }

    total = await models.DashboardOplogRecord.all().count()

    action_counts: dict[str, int] = {}
    for act_key in OPLOG_ACTION_LABELS:
        count = await models.DashboardOplogRecord.filter(action=act_key).count()
        if count > 0:
            action_counts[act_key] = count

    level_counts: dict[str, int] = {}
    for lv in ("ERROR", "WARNING", "INFO", "DEBUG", "SUCCESS"):
        count = await models.DashboardOplogRecord.filter(level=lv).count()
        if count > 0:
            level_counts[lv] = count

    recent_records = await models.DashboardOplogRecord.all().order_by("-created_at").limit(10)
    latest = [_record_to_dict(record) for record in recent_records]

    return {
        "total": total,
        "enabled": True,
        "action_counts": action_counts,
        "level_totals": level_counts,
        "latest": latest,
    }
