from __future__ import annotations

import asyncio
import datetime as dt
import re
from pathlib import Path
from typing import Any

from ..core import path as admin_path
from ..core.config import plugin_config
from ..core.utils import json_load_or_default
from .dashboard_oplog_service import (
    _is_oplog_available,
    build_oplog_overview_payload,
    load_oplog_entries,
)

LOG_LEVELS = ("ERROR", "WARNING", "INFO", "SUCCESS", "DEBUG")
LOG_LINE_PATTERN = re.compile(
    r"^(?P<timestamp>\S+(?:\s+\S+)?)\s+\[(?P<level>[A-Z]+)\]\s+(?P<source>[^|]+?)\s*\|\s*(?P<message>.*)$"
)


def _parse_iso_like_timestamp(raw_value: str | None) -> str | None:
    """
    解析isoliketimestamp
    :param raw_value: raw_value 参数
    :return: str | None
    """
    if not raw_value:
        return None
    value = str(raw_value).strip()
    if not value:
        return None

    normalized = value.replace("/", "-")
    for parser in (
        lambda item: dt.datetime.fromisoformat(item),
        lambda item: dt.datetime.strptime(item, "%m-%d %H:%M:%S"),
        lambda item: dt.datetime.strptime(item, "%Y-%m-%d %H:%M:%S"),
        lambda item: dt.datetime.strptime(item, "%Y-%m-%dT%H:%M:%S"),
    ):
        try:
            parsed = parser(normalized)
        except ValueError:
            continue
        if parsed.year == 1900:
            parsed = parsed.replace(year=dt.datetime.now().year)
        return parsed.isoformat(timespec="seconds")
    return value


def _tail_lines(path: Path, *, limit: int = 600) -> list[str]:
    """
    处理 _tail_lines 的业务逻辑
    :param path: 路径对象
    :param limit: 数量限制
    :return: list[str]
    """
    if not path.exists() or not path.is_file():
        return []
    target = max(limit, 1)
    with path.open("rb") as file:
        position = file.seek(0, 2)
        chunks: list[bytes] = []
        newline_count = 0
        while position > 0 and newline_count <= target:
            read_size = min(8192, position)
            position -= read_size
            file.seek(position)
            chunk = file.read(read_size)
            chunks.append(chunk)
            newline_count += chunk.count(b"\n")
    return b"".join(reversed(chunks)).decode("utf-8", errors="ignore").splitlines(keepends=True)[-target:]


def load_runtime_log_entries(limit: int = 600) -> list[dict[str, Any]]:
    """
    加载运行时日志entries
    :param limit: 数量限制
    :return: list[dict[str, Any]]
    """
    raw_path = Path(plugin_config.dashboard_log_file_path.strip()) if plugin_config.dashboard_log_file_path.strip() else None
    if raw_path is None:
        return []
    log_path = raw_path if raw_path.is_absolute() else Path.cwd() / raw_path
    entries: list[dict[str, Any]] = []

    for index, line in enumerate(_tail_lines(log_path, limit=limit), start=1):
        content = line.rstrip()
        if not content:
            continue
        matched = LOG_LINE_PATTERN.match(content)
        if matched:
            entries.append(
                {
                    "id": f"runtime-{index}",
                    "source": "runtime_log",
                    "level": matched.group("level"),
                    "timestamp": _parse_iso_like_timestamp(matched.group("timestamp")),
                    "group_id": None,
                    "module": matched.group("source").strip(),
                    "message": matched.group("message").strip(),
                    "detail": content,
                    "raw": content,
                }
            )
            continue

        detected_level = next((level for level in LOG_LEVELS if f"[{level}]" in content), "INFO")
        entries.append(
            {
                "id": f"runtime-{index}",
                "source": "runtime_log",
                "level": detected_level,
                "timestamp": None,
                "group_id": None,
                "module": "runtime",
                "message": content,
                "detail": content,
                "raw": content,
            }
        )
    return entries


async def load_plugin_error_entries() -> list[dict[str, Any]]:
    """
    加载pluginerrorentries
    :return: list[dict[str, Any]]
    """
    if _is_oplog_available():
        try:
            from ..statistics import models
            records = await models.DashboardOplogRecord.filter(action="plugin_error").order_by("-created_at").limit(600)
            entries: list[dict[str, Any]] = []
            for record in records:
                extra_data = {}
                if hasattr(record, "extra_json") and record.extra_json:
                    try:
                        import json
                        extra_data = json.loads(record.extra_json)
                    except (json.JSONDecodeError, TypeError):
                        extra_data = {}
                entries.append(
                    {
                        "id": f"oplog-{record.id}",
                        "source": "plugin_error",
                        "level": "ERROR",
                        "timestamp": record.created_at.isoformat() if record.created_at else None,
                        "group_id": str(record.group_id) if record.group_id else None,
                        "module": extra_data.get("module", ""),
                        "message": str(record.detail or ""),
                        "detail": str(record.detail or ""),
                        "raw": str(record.detail or ""),
                    }
                )
            if entries:
                return entries
        except Exception:
            pass

    entries = []
    if not admin_path.error_path.exists():
        return entries

    for error_file in sorted(admin_path.error_path.glob("*.json")):
        payload = json_load_or_default(error_file, {})
        for group_id, error_map in payload.items():
            if not isinstance(error_map, dict):
                continue
            for timestamp, detail in error_map.items():
                module_name = ""
                message = ""
                if isinstance(detail, list):
                    if detail:
                        module_name = str(detail[0])
                    if len(detail) >= 2:
                        message = str(detail[1])
                else:
                    message = str(detail)
                entries.append(
                    {
                        "id": f"plugin-{group_id}-{timestamp}",
                        "source": "plugin_error",
                        "level": "ERROR",
                        "timestamp": _parse_iso_like_timestamp(str(timestamp).replace("-", " ", 1)),
                        "group_id": str(group_id),
                        "module": module_name or error_file.stem,
                        "message": message,
                        "detail": message,
                        "raw": message,
                    }
                )
    return entries


async def build_logs_payload(
    *,
    page: int = 1,
    page_size: int = 50,
    level: str = "",
    keyword: str = "",
    source: str = "",
) -> dict[str, Any]:
    """
    构建logspayload
    :param page: 页码
    :param page_size: 分页大小
    :param level: level 参数
    :param keyword: 关键字
    :param source: source 参数
    :return: dict[str, Any]
    """
    normalized_page = max(int(page), 1)
    normalized_page_size = max(1, min(int(page_size), 200))
    normalized_level = str(level or "").strip().upper()
    normalized_keyword = str(keyword or "").strip().lower()
    normalized_source = str(source or "").strip().lower()

    include_all = not normalized_source
    runtime_task = asyncio.to_thread(load_runtime_log_entries) if include_all or normalized_source == "runtime_log" else None
    plugin_task = load_plugin_error_entries() if include_all or normalized_source == "plugin_error" else None
    oplog_task = load_oplog_entries(limit=600) if _is_oplog_available() and (include_all or normalized_source == "dashboard_oplog") else None
    runtime_items, plugin_error_items, oplog_items = await asyncio.gather(
        runtime_task or _empty_log_items(),
        plugin_task or _empty_log_items(),
        oplog_task or _empty_log_items(),
    )
    items = [*runtime_items, *plugin_error_items, *oplog_items]
    items.sort(key=lambda item: (item["timestamp"] or "", item["id"]), reverse=True)

    if normalized_level:
        items = [item for item in items if str(item["level"]).upper() == normalized_level]
    if normalized_source:
        items = [item for item in items if str(item["source"]).lower() == normalized_source]
    if normalized_keyword:
        items = [
            item
            for item in items
            if normalized_keyword in str(item["message"]).lower()
            or normalized_keyword in str(item.get("module", "")).lower()
            or normalized_keyword in str(item["group_id"] or "").lower()
            or normalized_keyword in str(item["detail"]).lower()
        ]

    total = len(items)
    total_pages = max(1, (total + normalized_page_size - 1) // normalized_page_size) if total else 1
    start = (normalized_page - 1) * normalized_page_size
    end = start + normalized_page_size

    return {
        "items": items[start:end],
        "pagination": {
            "page": normalized_page,
            "page_size": normalized_page_size,
            "total": total,
            "total_pages": total_pages,
            "has_prev": normalized_page > 1,
            "has_next": normalized_page < total_pages,
        },
        "filters": {
            "level": normalized_level or None,
            "keyword": keyword or None,
            "source": normalized_source or None,
        },
        "sources": [
            {
                "key": "runtime_log",
                "label": "运行日志",
                "enabled": bool(plugin_config.dashboard_log_file_path.strip()),
            },
            {
                "key": "plugin_error",
                "label": "插件错误",
                "enabled": True,
            },
            {
                "key": "dashboard_oplog",
                "label": "操作日志",
                "enabled": _is_oplog_available(),
            },
        ],
        "level_totals": {
            level_name: sum(1 for item in items if str(item["level"]).upper() == level_name)
            for level_name in LOG_LEVELS
        },
    }


async def build_logs_overview_payload() -> dict[str, Any]:
    """
    构建logsoverviewpayload
    :return: dict[str, Any]
    """
    runtime_task = asyncio.to_thread(load_runtime_log_entries)
    plugin_task = load_plugin_error_entries()
    oplog_task = build_oplog_overview_payload() if _is_oplog_available() else _empty_oplog_overview()
    runtime_items, plugin_items, oplog_overview = await asyncio.gather(runtime_task, plugin_task, oplog_task)
    latest_items = [*runtime_items, *plugin_items, *(oplog_overview.get("latest") or [])]
    latest_items.sort(key=lambda item: (item.get("timestamp") or "", item.get("id") or ""), reverse=True)
    return {
        "total": len(runtime_items) + len(plugin_items) + int(oplog_overview.get("total") or 0),
        "runtime_log_enabled": bool(plugin_config.dashboard_log_file_path.strip()),
        "runtime_log_file_path": plugin_config.dashboard_log_file_path.strip() or None,
        "plugin_error_total": len(plugin_items),
        "runtime_log_total": len(runtime_items),
        "oplog_total": int(oplog_overview.get("total") or 0),
        "oplog_enabled": _is_oplog_available(),
        "sources": [
            {
                "key": "runtime_log",
                "label": "运行日志",
                "enabled": bool(plugin_config.dashboard_log_file_path.strip()),
            },
            {
                "key": "plugin_error",
                "label": "插件错误",
                "enabled": True,
            },
            {
                "key": "dashboard_oplog",
                "label": "操作日志",
                "enabled": _is_oplog_available(),
            },
        ],
        "level_totals": {
            level_name: (
                sum(1 for item in [*runtime_items, *plugin_items] if str(item["level"]).upper() == level_name)
                + int((oplog_overview.get("level_totals") or {}).get(level_name, 0))
            )
            for level_name in LOG_LEVELS
        },
        "latest": latest_items[:10],
    }


async def _empty_log_items() -> list[dict[str, Any]]:
    return []


async def _empty_oplog_overview() -> dict[str, Any]:
    return {"total": 0, "level_totals": {}, "latest": []}
