from __future__ import annotations

import asyncio
import datetime
import importlib.util
import sys
import time
from pathlib import Path
from typing import Any

import nonebot

from ..approval import ai_verify_store, approval_blacklist_store, approval_store
from ..broadcasting import broadcast_store
from ..content_guard.image_guard_flow import build_image_guard_status_payload
from ..content_guard.text_guard_flow import GROUP_SCOPE_PATTERN, load_runtime_limit_rules, should_apply_group_scope
from ..core import path as admin_path
from ..core.config import parse_string_list, plugin_config
from ..core.path import (
    admin_funcs,
    build_default_switchers,
    get_func_display_name,
    is_default_enabled,
    should_notify_when_disabled,
)
from ..statistics.config_orm_store import (
    orm_load_switcher, orm_load_approval_terms,
    orm_load_group_violation_snapshot,
    orm_load_daily_trend,
)
from ..statistics import models as orm_models
from ..statistics.statistics_read_service import (
    load_daily_message_stats_snapshot,
    load_group_stop_words_snapshot,
    load_group_word_text_snapshot,
    load_group_wordcloud_source,
    load_history_message_stats_snapshot,
)
from ..statistics.orm_bootstrap import get_statistics_orm_bootstrap_state
from ..statistics.statistics_store import (
    is_group_record_enabled,
    load_runtime_record_setting_groups,
)
from ..statistics.wordcloud_generate_flow import build_wordcloud_items


class _AsyncTTLCache:
    def __init__(self, ttl_seconds: float):
        """
        处理 __init__ 的业务逻辑
        :param ttl_seconds: ttl_seconds 参数
        :return: None
        """
        self.ttl_seconds = ttl_seconds
        self._value: Any | None = None
        self._updated_at: float = 0.0
        self._inflight: asyncio.Task[Any] | None = None

    def _clone_value(self, value: Any) -> Any:
        """
        处理 _clone_value 的业务逻辑
        :param value: 值
        :return: Any
        """
        if isinstance(value, list):
            return list(value)
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, set):
            return set(value)
        return value

    def get(self) -> Any | None:
        """
        获取
        :return: Any | None
        """
        if self._updated_at and (time.time() - self._updated_at) < self.ttl_seconds:
            return self._clone_value(self._value)
        return None

    async def get_or_load(self, loader) -> Any:
        """
        获取orload
        :param loader: loader 参数
        :return: Any
        """
        cached = self.get()
        if cached is not None:
            return cached

        if self._inflight is not None:
            return self._clone_value(await self._inflight)

        task = asyncio.create_task(loader())
        self._inflight = task
        try:
            value = await task
            self._value = self._clone_value(value)
            self._updated_at = time.time()
            return self._clone_value(value)
        finally:
            if self._inflight is task:
                self._inflight = None


_RUNTIME_GROUP_SNAPSHOT_CACHE = _AsyncTTLCache(ttl_seconds=8.0)
_DASHBOARD_GROUP_IDS_CACHE = _AsyncTTLCache(ttl_seconds=8.0)
_DASHBOARD_GROUP_IDS_LIVE_CACHE = _AsyncTTLCache(ttl_seconds=5.0)
_GROUP_SUMMARY_CONCURRENCY = 6


def normalize_group_id(group_id: int | str) -> str:
    """
    规范化群id
    :param group_id: 群号
    :return: str
    """
    return str(group_id)


def load_dashboard_superusers() -> list[str]:
    """
    加载面板superusers
    :return: list[str]
    """
    superusers = getattr(nonebot.get_driver().config, "superusers", set()) or set()
    return [str(user_id) for user_id in superusers]


def _sort_group_ids(group_ids: set[str]) -> list[str]:
    """
    处理 _sort_group_ids 的业务逻辑
    :param group_ids: 群号列表
    :return: list[str]
    """
    return sorted(
        group_ids,
        key=lambda item: (not item.isdigit(), int(item) if item.isdigit() else item),
    )


def _normalize_member_ids(raw_user_ids: list[Any]) -> list[str]:
    """
    规范化成员ids
    :param raw_user_ids: 标识列表
    :return: list[str]
    """
    return [str(user_id) for user_id in raw_user_ids if str(user_id).strip()]


def _read_group_ids_from_path(root: Path, *, suffix: str | None = None) -> set[str]:
    """
    读取群idsfrom路径
    :param root: root 参数
    :param suffix: suffix 参数
    :return: set[str]
    """
    group_ids: set[str] = set()
    if not root.exists():
        return group_ids

    if suffix:
        for entry in root.glob(f"*{suffix}"):
            group_ids.add(entry.stem)
    else:
        for entry in root.iterdir():
            if entry.is_dir():
                group_ids.add(entry.name)
    return group_ids


async def _read_group_ids_from_orm() -> set[str]:
    """
    读取群idsfromORM
    :return: set[str]
    """
    group_ids: set[str] = set()
    model_classes = [
        orm_models.StatisticsGroupRecordSetting,
        orm_models.StatisticsGroupStopWord,
        orm_models.StatisticsDailyMessageStat,
        orm_models.StatisticsHistoryMessageStat,
        orm_models.StatisticsWordCorpus,
        orm_models.UserViolation,
        orm_models.ViolationRecord,
    ]
    for model_cls in model_classes:
        if model_cls is None:
            continue
        queryset = None
        values_query = None
        try:
            queryset = model_cls.all()
            values_list = getattr(queryset, "values_list", None)
            if callable(values_list):
                values_query = values_list("group_id", flat=True)
                distinct = getattr(values_query, "distinct", None)
                if callable(distinct):
                    values_query = distinct()
                values = await values_query
                group_ids.update(
                    str(group_id).strip()
                    for group_id in values
                    if str(group_id or "").strip()
                )
                continue
        except Exception:
            pass
        try:
            rows = await (queryset if queryset is not None else model_cls.all())
        except Exception:
            continue
        for row in rows:
            group_id = str(getattr(row, "group_id", "") or "").strip()
            if group_id:
                group_ids.add(group_id)
    return group_ids


async def _collect_runtime_group_snapshot_uncached() -> dict[str, dict[str, Any]]:
    """
    收集运行时群snapshotuncached
    :return: dict[str, dict[str, Any]]
    """
    snapshot: dict[str, dict[str, Any]] = {}
    for bot in nonebot.get_bots().values():
        try:
            group_list = await bot.get_group_list()
        except Exception:
            continue

        for group in group_list:
            group_id = str(group.get("group_id") or "").strip()
            if not group_id:
                continue
            snapshot[group_id] = {
                "group_id": group_id,
                "group_name": group.get("group_name") or f"? {group_id}",
                "member_count": group.get("member_count"),
                "max_member_count": group.get("max_member_count"),
            }
    return snapshot


async def _load_runtime_group_snapshot() -> dict[str, dict[str, Any]]:
    """
    加载运行时群snapshot
    :return: dict[str, dict[str, Any]]
    """
    return await _RUNTIME_GROUP_SNAPSHOT_CACHE.get_or_load(_collect_runtime_group_snapshot_uncached)


async def _collect_dashboard_group_ids_uncached() -> list[str]:
    """
    收集面板群idsuncached
    :return: list[str]
    """
    group_ids = set(await load_runtime_record_setting_groups())
    group_ids.update(await _read_group_ids_from_orm())
    group_ids.update(_read_group_ids_from_path(admin_path.kick_lock_path, suffix=".lock"))

    switcher_snapshot = await orm_load_switcher()
    if isinstance(switcher_snapshot, dict):
        group_ids.update(str(group_id) for group_id in switcher_snapshot.keys())

    approval_terms = await orm_load_approval_terms() or {}
    if isinstance(approval_terms, dict):
        group_ids.update(str(group_id) for group_id in approval_terms.keys())

    approval_admins = await approval_store.g_admin_async()
    if isinstance(approval_admins, dict):
        group_ids.update(str(group_id) for group_id in approval_admins.keys() if str(group_id) != "su")

    blacklist_terms = await approval_blacklist_store.load_blacklist()
    if isinstance(blacklist_terms, dict):
        group_ids.update(str(group_id) for group_id in blacklist_terms.keys())

    ai_verify_config = await ai_verify_store.load_config()
    if isinstance(ai_verify_config, dict):
        group_ids.update(str(group_id) for group_id in ai_verify_config.keys())

    for excluded_group_ids in (await broadcast_store.load_broadcast_config(load_dashboard_superusers())).values():
        group_ids.update(str(group_id) for group_id in excluded_group_ids)

    return _sort_group_ids(group_ids)


async def collect_dashboard_group_ids() -> list[str]:
    """
    收集面板群ids
    :return: list[str]
    """
    return await _DASHBOARD_GROUP_IDS_CACHE.get_or_load(_collect_dashboard_group_ids_uncached)


async def collect_runtime_group_ids() -> list[str]:
    """
    收集运行时群ids
    :return: list[str]
    """
    snapshot = await _load_runtime_group_snapshot()
    return _sort_group_ids(set(snapshot.keys()))


async def _collect_dashboard_group_ids_live_uncached() -> list[str]:
    """
    收集面板群ids实时uncached
    :return: list[str]
    """
    group_ids = set(await collect_dashboard_group_ids())
    group_ids.update(await collect_runtime_group_ids())
    return _sort_group_ids(group_ids)


async def collect_dashboard_group_ids_live() -> list[str]:
    """
    收集面板群ids实时
    :return: list[str]
    """
    return await _DASHBOARD_GROUP_IDS_LIVE_CACHE.get_or_load(_collect_dashboard_group_ids_live_uncached)


OVERVIEW_ROUTE_ITEMS = [
    {"key": "statistics", "label": "统计分析", "path": "/statistics/overview"},
    {"key": "approval", "label": "审批", "path": "/approval/overview"},
    {"key": "broadcast", "label": "广播", "path": "/broadcast/overview"},
    {"key": "basic_group_admin", "label": "基础群管", "path": "/basic-group-admin/overview"},
    {"key": "content_guard", "label": "内容审核", "path": "/content-guard/overview"},
    {"key": "member_cleanup", "label": "成员清理", "path": "/member-cleanup/overview"},
    {"key": "event_notice", "label": "事件提醒", "path": "/event-notice/overview"},
    {"key": "switcher", "label": "功能开关", "path": "/switcher/overview"},
    {"key": "runtime", "label": "运行态", "path": "/runtime/overview"},
]


GROUP_SECTION_ITEMS = [
    {"key": "statistics", "label": "统计分析", "path": "/groups/{group_id}/statistics"},
    {"key": "messages", "label": "群消息", "path": "/groups/{group_id}/messages"},
    {"key": "members", "label": "群成员", "path": "/groups/{group_id}/members"},
    {"key": "feature_switches", "label": "功能开关", "path": "/groups/{group_id}/feature-switches"},
    {"key": "approval", "label": "审批", "path": "/groups/{group_id}/approval"},
    {"key": "broadcast", "label": "广播", "path": "/groups/{group_id}/broadcast"},
    {"key": "basic_group_admin", "label": "基础群管", "path": "/groups/{group_id}/basic-group-admin"},
    {"key": "content_guard", "label": "内容审核", "path": "/groups/{group_id}/content-guard"},
    {"key": "member_cleanup", "label": "成员清理", "path": "/groups/{group_id}/member-cleanup"},
    {"key": "event_notice", "label": "事件提醒", "path": "/groups/{group_id}/event-notice"},
    {"key": "announcements", "label": "群公告", "path": "/groups/{group_id}/announcements"},
    {"key": "essence", "label": "精华消息", "path": "/groups/{group_id}/essence"},
    {"key": "honors", "label": "群荣誉", "path": "/groups/{group_id}/honors"},
    {"key": "files", "label": "群文件", "path": "/groups/{group_id}/files"},
    {"key": "wordcloud_card", "label": "词云卡片", "path": "/groups/{group_id}/wordcloud-card"},
]


RUNTIME_DEPENDENCIES = [
    {"key": "pyppeteer", "label": "截图链路", "module": "pyppeteer"},
    {"key": "jieba", "label": "中文分词", "module": "jieba"},
    {"key": "jinja2", "label": "模板渲染", "module": "jinja2"},
    {"key": "nonebot_plugin_apscheduler", "label": "定时任务", "module": "nonebot_plugin_apscheduler"},
    {"key": "nonebot_plugin_tortoise_orm", "label": "ORM", "module": "nonebot_plugin_tortoise_orm"},
    {"key": "tencentcloud", "label": "腾讯云审核 SDK", "module": "tencentcloud"},
    {"key": "openai", "label": "OpenAI 兼容客户端", "module": "openai"},
]


def build_dashboard_catalog_payload(base_path: str) -> dict[str, Any]:
    """
    构建面板catalogpayload
    :param base_path: 路径对象
    :return: dict[str, Any]
    """
    frontend_enabled = plugin_config.dashboard_frontend_enabled
    return {
        "mode": "integrated_web" if frontend_enabled else "api_only",
        "frontend_enabled": frontend_enabled,
        "frontend_path": base_path if frontend_enabled else None,
        "frontend_routes": (
            [
                {
                    "key": "home",
                    "label": "控制台首页",
                    "path": base_path,
                }
            ]
            if frontend_enabled
            else []
        ),
        "overview_routes": [
            {**item, "path": f"{base_path}/api{item['path']}"}
            for item in OVERVIEW_ROUTE_ITEMS
        ],
        "group_routes": [
            {**item, "path": f"{base_path}/api{item['path']}"}
            for item in GROUP_SECTION_ITEMS
        ],
    }


def _is_dependency_available(module_name: str) -> bool:
    """
    处理 _is_dependency_available 的业务逻辑
    :param module_name: module_name 参数
    :return: bool
    """
    try:
        return importlib.util.find_spec(module_name) is not None
    except ValueError:
        return module_name in sys.modules


async def fetch_group_profiles(group_ids: list[str]) -> dict[str, dict[str, Any]]:
    """
    拉取群profiles
    :param group_ids: 群号列表
    :return: dict[str, dict[str, Any]]
    """
    if not group_ids:
        return {}

    runtime_snapshot = await _load_runtime_group_snapshot()
    profiles: dict[str, dict[str, Any]] = {}
    for group_id in group_ids:
        profile = runtime_snapshot.get(str(group_id))
        if profile is not None:
            profiles[str(group_id)] = dict(profile)
    return profiles


async def fetch_member_display_names(group_id: int | str, user_ids: list[str]) -> dict[str, str]:
    """
    拉取成员displaynames
    :param group_id: 群号
    :param user_ids: 标识列表
    :return: dict[str, str]
    """
    names: dict[str, str] = {}
    normalized_group_id = normalize_group_id(group_id)
    if not user_ids:
        return names

    from .dashboard_live_service import _member_cache
    import time
    cache_key = str(normalized_group_id)
    now = time.time()
    cached = _member_cache.get(cache_key)
    if cached and (now - cached[0]) < 60:
        member_map = {str(m.get("user_id", "")): m for m in cached[1]}
        for user_id in user_ids:
            member = member_map.get(str(user_id))
            if member:
                names[user_id] = member.get("card") or member.get("nickname") or user_id

    remaining = [uid for uid in user_ids if uid not in names]
    if not remaining:
        return names

    for bot in nonebot.get_bots().values():
        for user_id in remaining:
            if user_id in names:
                continue
            try:
                member = await bot.get_group_member_info(
                    group_id=int(normalized_group_id),
                    user_id=int(user_id),
                )
            except Exception:
                continue
            names[user_id] = member.get("card") or member.get("nickname") or user_id

    return names


async def list_daily_trend(group_id: int | str, *, limit: int = 14) -> list[dict[str, Any]]:
    """
    列出每日trend
    :param group_id: 群号
    :param limit: 数量限制
    :return: list[dict[str, Any]]
    """
    normalized_group_id = normalize_group_id(group_id)
    return await orm_load_daily_trend(normalized_group_id, limit=limit)


def build_top_speakers_payload(
    stats: dict[str, int],
    *,
    limit: int = 10,
    member_names: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """
    构建topspeakerspayload
    :param stats: stats 参数
    :param limit: 数量限制
    :param member_names: member_names 参数
    :return: list[dict[str, Any]]
    """
    ranked_items = sorted(
        ((str(user_id), int(count)) for user_id, count in stats.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    return [
        {
            "user_id": user_id,
            "display_name": (member_names or {}).get(user_id) or user_id,
            "message_count": count,
        }
        for user_id, count in ranked_items[:limit]
    ]


async def build_feature_switch_payload(group_id: int | str) -> list[dict[str, Any]]:
    """
    构建featureswitchpayload
    :param group_id: 群号
    :return: list[dict[str, Any]]
    """
    normalized_group_id = normalize_group_id(group_id)
    switchers = dict(build_default_switchers())
    orm_snapshot = await orm_load_switcher()
    if normalized_group_id in orm_snapshot:
        switchers.update(orm_snapshot[normalized_group_id])

    return [
        {
            "key": key,
            "label": get_func_display_name(key),
            "enabled": bool(enabled),
            "default_enabled": is_default_enabled(key),
            "notify_when_disabled": should_notify_when_disabled(key),
        }
        for key, enabled in switchers.items()
    ]


def _is_switch_enabled(switches: list[dict[str, Any]], key: str) -> bool:
    """
    处理 _is_switch_enabled 的业务逻辑
    :param switches: switches 参数
    :param key: key 参数
    :return: bool
    """
    return next((item["enabled"] for item in switches if item["key"] == key), False)


async def build_group_feature_switches_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群featureswitchespayload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    switches = await build_feature_switch_payload(group_id)
    return {
        "group_id": normalize_group_id(group_id),
        "enabled_count": sum(1 for item in switches if item["enabled"]),
        "disabled_count": sum(1 for item in switches if not item["enabled"]),
        "switches": switches,
    }


async def build_switcher_overview_payload(group_ids: list[str] | None = None) -> dict[str, Any]:
    """
    构建开关overviewpayload
    :param group_ids: 群号列表
    :return: dict[str, Any]
    """
    group_ids = group_ids or await collect_dashboard_group_ids()
    feature_items: list[dict[str, Any]] = []

    for func_key, aliases in admin_funcs.items():
        enabled_groups = 0
        for group_id in group_ids:
            if _is_switch_enabled(await build_feature_switch_payload(group_id), func_key):
                enabled_groups += 1
        feature_items.append(
            {
                "key": func_key,
                "label": aliases[0] if aliases else func_key,
                "aliases": list(aliases),
                "default_enabled": is_default_enabled(func_key),
                "notify_when_disabled": should_notify_when_disabled(func_key),
                "enabled_groups": enabled_groups,
                "disabled_groups": max(0, len(group_ids) - enabled_groups),
            }
        )

    return {
        "group_count": len(group_ids),
        "feature_count": len(feature_items),
        "enabled_feature_entries": sum(item["enabled_groups"] for item in feature_items),
        "features": feature_items,
    }


def build_runtime_overview_payload(base_path: str) -> dict[str, Any]:
    """
    构建运行时overviewpayload
    :param base_path: 路径对象
    :return: dict[str, Any]
    """
    orm_state = get_statistics_orm_bootstrap_state()
    return {
        "mode": "integrated_web" if plugin_config.dashboard_frontend_enabled else "api_only",
        "base_path": base_path,
        "dashboard_enabled": plugin_config.dashboard_enabled,
        "dashboard_frontend_enabled": plugin_config.dashboard_frontend_enabled,
        "auth_required": bool(plugin_config.dashboard_api_token.strip()),
        "cors_enabled": bool(parse_string_list(plugin_config.dashboard_cors_allow_origins)),
        "cors_allow_origins": parse_string_list(plugin_config.dashboard_cors_allow_origins),
        "cors_allow_credentials": plugin_config.dashboard_cors_allow_credentials,
        "statistics_orm_enabled": plugin_config.statistics_orm_enabled,
        "statistics_orm_capture_message_content": plugin_config.statistics_orm_capture_message_content,
        "statistics_orm_bootstrap": orm_state,
        "dashboard_log_file_path": plugin_config.dashboard_log_file_path.strip() or None,
        "ai_verify_proxy_configured": bool(plugin_config.ai_verify_proxy.strip()),
        "ai_verify_use_proxy": plugin_config.ai_verify_use_proxy,
        "callback_notice": plugin_config.callback_notice,
        "optional_dependencies": [
            {
                "key": item["key"],
                "label": item["label"],
                "available": _is_dependency_available(item["module"]),
            }
            for item in RUNTIME_DEPENDENCIES
        ],
    }


async def build_wordcloud_keywords_payload(group_id: int | str, *, limit: int = 30) -> list[dict[str, Any]]:
    """
    构建词云keywordspayload
    :param group_id: 群号
    :param limit: 数量限制
    :return: list[dict[str, Any]]
    """
    source = await load_group_wordcloud_source(group_id)
    if not source.available:
        return []

    try:
        import jieba
    except ModuleNotFoundError:
        return []

    segmented_text = " ".join(jieba.lcut(source.text or ""))
    return [
        {"word": item.word, "count": item.count, "font_size": item.font_size}
        for item in build_wordcloud_items(segmented_text, stop_words=source.stop_words, limit=limit)
    ]


async def build_recent_message_preview(group_id: int | str, *, limit: int = 8) -> list[str]:
    """
    构建recent消息preview
    :param group_id: 群号
    :param limit: 数量限制
    :return: list[str]
    """
    text = await load_group_word_text_snapshot(group_id)
    if not text:
        return []
    return text.splitlines()[-limit:]


async def build_global_daily_trend(group_ids: list[str], *, limit: int = 14) -> list[dict[str, Any]]:
    """
    构建global每日trend
    :param group_ids: 群号列表
    :param limit: 数量限制
    :return: list[dict[str, Any]]
    """
    aggregated: dict[str, dict[str, Any]] = {}
    for group_id in group_ids:
        for item in await list_daily_trend(group_id, limit=max(limit * 3, limit)):
            bucket = aggregated.setdefault(
                item["date"],
                {
                    "date": item["date"],
                    "message_count": 0,
                    "active_members": 0,
                    "group_count": 0,
                },
            )
            bucket["message_count"] += int(item.get("message_count") or 0)
            bucket["active_members"] += int(item.get("active_members") or 0)
            bucket["group_count"] += 1
    return [aggregated[key] for key in sorted(aggregated.keys())][-limit:]


async def build_group_statistics_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群statisticspayload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    history_stats = await load_history_message_stats_snapshot(normalized_group_id)
    today_stats = await load_daily_message_stats_snapshot(normalized_group_id)
    ranking_user_ids = list({*history_stats.keys(), *today_stats.keys()})
    member_names = await fetch_member_display_names(normalized_group_id, ranking_user_ids)
    source = await load_group_wordcloud_source(normalized_group_id)

    return {
        "group_id": normalized_group_id,
        "record_enabled": await is_group_record_enabled(normalized_group_id),
        "history_message_count": sum(history_stats.values()),
        "today_message_count": sum(today_stats.values()),
        "active_members": len(history_stats),
        "today_active_members": len(today_stats),
        "tracked_days": len(await list_daily_trend(normalized_group_id, limit=3650)),
        "stop_words_count": len(await load_group_stop_words_snapshot(normalized_group_id)),
        "wordcloud_available": source.available,
        "history_ranking": build_top_speakers_payload(history_stats, member_names=member_names),
        "today_ranking": build_top_speakers_payload(today_stats, member_names=member_names),
        "daily_trend": await list_daily_trend(normalized_group_id),
        "wordcloud_keywords": await build_wordcloud_keywords_payload(normalized_group_id),
        "recent_messages": await build_recent_message_preview(normalized_group_id),
    }


async def build_statistics_overview_payload(group_ids: list[str] | None = None) -> dict[str, Any]:
    """
    构建statisticsoverviewpayload
    :param group_ids: 群号列表
    :return: dict[str, Any]
    """
    group_ids = group_ids or await collect_dashboard_group_ids_live()
    profiles = await fetch_group_profiles(group_ids)
    wordcloud_sources = await asyncio.gather(
        *[load_group_wordcloud_source(group_id) for group_id in group_ids]
    )
    wordcloud_available_groups = sum(1 for source in wordcloud_sources if source.available)
    group_summaries = await _build_group_summaries(group_ids, profiles=profiles)
    tracked_groups = [item for item in group_summaries if item["history_message_count"] > 0]
    top_history_groups = sorted(group_summaries, key=lambda item: item["history_message_count"], reverse=True)[:8]
    top_today_groups = sorted(group_summaries, key=lambda item: item["today_message_count"], reverse=True)[:8]

    return {
        "group_count": len(group_summaries),
        "record_enabled_groups": sum(1 for item in group_summaries if item["record_enabled"]),
        "tracked_groups": len(tracked_groups),
        "history_message_count": sum(item["history_message_count"] for item in group_summaries),
        "today_message_count": sum(item["today_message_count"] for item in group_summaries),
        "active_members": sum(item["active_members"] for item in group_summaries),
        "stop_words_count": sum(item["stop_words_count"] for item in group_summaries),
        "wordcloud_available_groups": wordcloud_available_groups,
        "orm_enabled": plugin_config.statistics_orm_enabled,
        "top_history_groups": [
            {
                "group_id": item["group_id"],
                "group_name": item["group_name"],
                "history_message_count": item["history_message_count"],
            }
            for item in top_history_groups
            if item["history_message_count"] > 0
        ],
        "top_today_groups": [
            {
                "group_id": item["group_id"],
                "group_name": item["group_name"],
                "today_message_count": item["today_message_count"],
            }
            for item in top_today_groups
            if item["today_message_count"] > 0
        ],
    }


async def _load_violation_group_snapshot(group_id: int | str) -> list[dict[str, Any]]:
    """
    加载违规群snapshot
    :param group_id: 群号
    :return: list[dict[str, Any]]
    """
    normalized_group_id = normalize_group_id(group_id)
    return await orm_load_group_violation_snapshot(normalized_group_id)


def _parse_limit_rule(rule: list[str], group_id: int | str | None = None) -> dict[str, Any]:
    """
    解析limit规则
    :param rule: rule 参数
    :param group_id: 群号
    :return: dict[str, Any]
    """
    pattern = rule[0] if rule else ""
    options = rule[1] if len(rule) > 1 else ""
    delete = "$撤回" in options
    ban = "$禁言" in options
    scope_mode = None
    scope_groups: list[str] = []

    match = GROUP_SCOPE_PATTERN.search(options)
    if match:
        scope_mode = match.group(1)
        scope_groups = [item for item in match.group(2).split(",") if item]

    applicable = True
    if group_id is not None:
        try:
            applicable = should_apply_group_scope(options, int(group_id))
        except ValueError:
            applicable = should_apply_group_scope(options, 0)

    return {
        "pattern": pattern,
        "options": options,
        "delete": delete,
        "ban": ban,
        "scope_mode": scope_mode,
        "scope_groups": scope_groups,
        "applicable": applicable,
    }


async def _load_content_guard_rules(group_id: int | str | None = None) -> list[dict[str, Any]]:
    """
    加载内容审核规则
    :param group_id: 群号
    :return: list[dict[str, Any]]
    """
    items = [_parse_limit_rule(rule, group_id) for rule in await load_runtime_limit_rules()]
    if group_id is None:
        return items
    return [item for item in items if item["applicable"]]


def _list_cleanup_locks() -> list[dict[str, Any]]:
    """
    列出清理locks
    :return: list[dict[str, Any]]
    """
    if not admin_path.kick_lock_path.exists():
        return []

    items: list[dict[str, Any]] = []
    for path in sorted(admin_path.kick_lock_path.glob("*.lock")):
        stat = path.stat()
        items.append(
            {
                "group_id": path.stem,
                "path": str(path),
                "updated_at": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            }
        )
    return items


EVENT_NOTICE_TYPES = [
    {
        "key": "group_recall",
        "label": "防撤回",
        "switch_key": "group_recall",
        "category": "anti_recall",
        "active": True,
        "description": "成员自行撤回消息时转发原消息内容。",
    },
    {
        "key": "honor",
        "label": "荣誉提醒",
        "switch_key": "particular_e_notice",
        "category": "notice",
        "active": True,
        "description": "群荣誉变动时发送提醒。",
    },
    {
        "key": "member_increase",
        "label": "入群提醒",
        "switch_key": "particular_e_notice",
        "category": "notice",
        "active": True,
        "description": "新成员进群时发送欢迎提醒。",
    },
    {
        "key": "member_decrease",
        "label": "退群提醒",
        "switch_key": "particular_e_notice",
        "category": "notice",
        "active": True,
        "description": "成员离群或被移出时发送提醒。",
    },
    {
        "key": "admin_change",
        "label": "管理员变动",
        "switch_key": "particular_e_notice",
        "category": "notice",
        "active": True,
        "description": "管理员设定和取消时发送提醒。",
    },
    {
        "key": "poke",
        "label": "戳一戳",
        "switch_key": "particular_e_notice",
        "category": "notice",
        "active": False,
        "description": "当前仅保留监听入口，不发送提醒。",
    },
    {
        "key": "upload_files",
        "label": "文件上传",
        "switch_key": "particular_e_notice",
        "category": "notice",
        "active": False,
        "description": "当前仅保留监听入口，不发送提醒。",
    },
    {
        "key": "red_packet",
        "label": "红包相关",
        "switch_key": "particular_e_notice",
        "category": "notice",
        "active": False,
        "description": "当前仅保留监听入口，不发送提醒。",
    },
]


async def _build_event_notice_switch_map(group_id: int | str) -> dict[str, bool]:
    """
    构建event通知switchmap
    :param group_id: 群号
    :return: dict[str, bool]
    """
    switches = await build_feature_switch_payload(group_id)
    return {item["key"]: bool(item["enabled"]) for item in switches}


async def build_group_event_notice_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群event通知payload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    switch_map = await _build_event_notice_switch_map(normalized_group_id)
    particular_enabled = switch_map.get("particular_e_notice", False)
    anti_recall_enabled = switch_map.get("group_recall", False)

    event_types = [
        {
            **item,
            "enabled": anti_recall_enabled if item["switch_key"] == "group_recall" else particular_enabled,
        }
        for item in EVENT_NOTICE_TYPES
    ]

    return {
        "particular_notice_enabled": particular_enabled,
        "anti_recall_enabled": anti_recall_enabled,
        "active_notice_types": sum(1 for item in event_types if item["enabled"] and item["active"]),
        "listener_only_types": sum(1 for item in event_types if item["enabled"] and not item["active"]),
        "event_types": event_types,
    }


async def build_event_notice_overview_payload(group_ids: list[str] | None = None) -> dict[str, Any]:
    """
    构建event通知overviewpayload
    :param group_ids: 群号列表
    :return: dict[str, Any]
    """
    group_ids = group_ids or await collect_dashboard_group_ids()
    detail_items = [await build_group_event_notice_payload(group_id) for group_id in group_ids]

    particular_enabled_groups = [
        item["group_id"]
        for item in (
            {
                "group_id": group_id,
                **detail,
            }
            for group_id, detail in zip(group_ids, detail_items)
        )
        if item["particular_notice_enabled"]
    ]
    anti_recall_enabled_groups = [
        item["group_id"]
        for item in (
            {
                "group_id": group_id,
                **detail,
            }
            for group_id, detail in zip(group_ids, detail_items)
        )
        if item["anti_recall_enabled"]
    ]

    return {
        "particular_notice_enabled_groups": len(particular_enabled_groups),
        "anti_recall_enabled_groups": len(anti_recall_enabled_groups),
        "active_notice_types": sum(1 for item in EVENT_NOTICE_TYPES if item["active"]),
        "listener_only_types": sum(1 for item in EVENT_NOTICE_TYPES if not item["active"]),
        "supported_notice_types": EVENT_NOTICE_TYPES,
        "sample_groups": [
            {
                "group_id": group_id,
                "particular_notice_enabled": detail["particular_notice_enabled"],
                "anti_recall_enabled": detail["anti_recall_enabled"],
                "active_notice_types": detail["active_notice_types"],
            }
            for group_id, detail in zip(group_ids[:8], detail_items[:8])
        ],
    }


BASIC_GROUP_ADMIN_COMMANDS = [
    {"key": "ban", "label": "禁言", "risk": "medium"},
    {"key": "unban", "label": "解禁", "risk": "medium"},
    {"key": "ban_all", "label": "全员禁言", "risk": "high"},
    {"key": "change_card", "label": "改名片", "risk": "low"},
    {"key": "title", "label": "头衔", "risk": "medium"},
    {"key": "delete_title", "label": "删头衔", "risk": "medium"},
    {"key": "kick", "label": "踢人", "risk": "high"},
    {"key": "kick_blacklist", "label": "踢人并拉黑", "risk": "high"},
    {"key": "set_admin", "label": "设置管理员", "risk": "high"},
    {"key": "unset_admin", "label": "取消管理员", "risk": "high"},
    {"key": "set_essence", "label": "加精", "risk": "low"},
    {"key": "delete_essence", "label": "取消精华", "risk": "low"},
    {"key": "recall", "label": "撤回消息", "risk": "high"},
]


async def build_group_basic_admin_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群basic管理员payload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    switch_map = await _build_event_notice_switch_map(normalized_group_id)
    deputy_admin_ids = _normalize_member_ids((await approval_store.g_admin_async()).get(normalized_group_id, []))
    deputy_admin_names = await fetch_member_display_names(normalized_group_id, deputy_admin_ids)

    return {
        "feature_enabled": bool(switch_map.get("admin", True)),
        "feature_label": get_func_display_name("admin"),
        "switch_key": "admin",
        "aliases": list(admin_funcs.get("admin", [])),
        "command_count": len(BASIC_GROUP_ADMIN_COMMANDS),
        "high_risk_command_count": sum(1 for item in BASIC_GROUP_ADMIN_COMMANDS if item["risk"] == "high"),
        "commands": BASIC_GROUP_ADMIN_COMMANDS,
        "deputy_admins": [
            {
                "user_id": user_id,
                "display_name": deputy_admin_names.get(user_id) or user_id,
            }
            for user_id in deputy_admin_ids
        ],
        "superusers": load_dashboard_superusers(),
        "all_members_target_supported": False,
        "title_self_service": True,
    }


async def build_basic_group_admin_overview_payload(group_ids: list[str] | None = None) -> dict[str, Any]:
    """
    构建basic群管理员overviewpayload
    :param group_ids: 群号列表
    :return: dict[str, Any]
    """
    group_ids = group_ids or await collect_dashboard_group_ids_live()
    detail_items = [await build_group_basic_admin_payload(group_id) for group_id in group_ids]

    return {
        "enabled_groups": sum(1 for item in detail_items if item["feature_enabled"]),
        "deputy_admin_groups": sum(1 for item in detail_items if item["deputy_admins"]),
        "deputy_admin_count": sum(len(item["deputy_admins"]) for item in detail_items),
        "command_count": len(BASIC_GROUP_ADMIN_COMMANDS),
        "high_risk_command_count": sum(1 for item in BASIC_GROUP_ADMIN_COMMANDS if item["risk"] == "high"),
        "commands": BASIC_GROUP_ADMIN_COMMANDS,
        "sample_groups": [
            {
                "group_id": group_id,
                "feature_enabled": detail["feature_enabled"],
                "deputy_admin_count": len(detail["deputy_admins"]),
                "high_risk_command_count": detail["high_risk_command_count"],
            }
            for group_id, detail in zip(group_ids[:8], detail_items[:8])
        ],
    }


async def build_group_summary_payload(
    group_id: int | str,
    *,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    构建群摘要payload
    :param group_id: 群号
    :param profile: profile 参数
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    cleanup_lock_active = any(item["group_id"] == normalized_group_id for item in _list_cleanup_locks())
    (
        history_stats,
        today_stats,
        trend,
        violation_entries,
        event_notice_payload,
        event_notice_switch_map,
        approval_admins,
        feature_switches,
        approval_terms,
        approval_blacklist,
        stop_words,
        broadcast_config,
        content_guard_rules,
        record_enabled,
    ) = await asyncio.gather(
        load_history_message_stats_snapshot(normalized_group_id),
        load_daily_message_stats_snapshot(normalized_group_id),
        list_daily_trend(normalized_group_id, limit=30),
        _load_violation_group_snapshot(normalized_group_id),
        build_group_event_notice_payload(normalized_group_id),
        _build_event_notice_switch_map(normalized_group_id),
        approval_store.g_admin_async(),
        build_feature_switch_payload(normalized_group_id),
        orm_load_approval_terms(),
        approval_blacklist_store.get_group_blacklist(normalized_group_id),
        load_group_stop_words_snapshot(normalized_group_id),
        broadcast_store.load_broadcast_config(load_dashboard_superusers()),
        _load_content_guard_rules(normalized_group_id),
        is_group_record_enabled(normalized_group_id),
    )
    basic_admin_enabled = event_notice_switch_map.get("admin", True)
    deputy_admin_count = len(_normalize_member_ids((approval_admins or {}).get(normalized_group_id, [])))

    return {
        "group_id": normalized_group_id,
        "group_name": (profile or {}).get("group_name") or f"? {normalized_group_id}",
        "member_count": (profile or {}).get("member_count"),
        "record_enabled": record_enabled,
        "history_message_count": sum(history_stats.values()),
        "today_message_count": sum(today_stats.values()),
        "active_members": len(history_stats),
        "today_active_members": len(today_stats),
        "tracked_days": len(trend),
        "latest_stat_date": trend[-1]["date"] if trend else None,
        "stop_words_count": len(stop_words),
        "feature_switches_enabled": sum(1 for item in feature_switches if item["enabled"]),
        "approval_terms_count": len((approval_terms or {}).get(normalized_group_id, [])),
        "approval_blacklist_count": len(approval_blacklist),
        "broadcast_excluded_by_users_count": sum(
            1
            for excluded_group_ids in broadcast_config.values()
            if normalized_group_id in excluded_group_ids
        ),
        "content_guard_rule_count": len(content_guard_rules),
        "violation_event_count": len(violation_entries),
        "cleanup_lock_active": cleanup_lock_active,
        "event_notice_enabled": event_notice_payload["particular_notice_enabled"],
        "anti_recall_enabled": event_notice_payload["anti_recall_enabled"],
        "basic_admin_enabled": basic_admin_enabled,
        "deputy_admin_count": deputy_admin_count,
    }


async def _build_group_summaries(
    group_ids: list[str],
    *,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    构建群summaries
    :param group_ids: 群号列表
    :param profiles: profiles 参数
    :return: list[dict[str, Any]]
    """
    if not group_ids:
        return []

    semaphore = asyncio.Semaphore(_GROUP_SUMMARY_CONCURRENCY)

    async def _build_one(group_id: str) -> dict[str, Any]:
        """
        构建one
        :param group_id: 群号
        :return: dict[str, Any]
        """
        async with semaphore:
            return await build_group_summary_payload(group_id, profile=(profiles or {}).get(group_id))

    return list(await asyncio.gather(*[_build_one(group_id) for group_id in group_ids]))


async def build_dashboard_overview_payload() -> dict[str, Any]:
    """
    构建面板overviewpayload
    :return: dict[str, Any]
    """
    group_ids = await collect_dashboard_group_ids_live()
    profiles = await fetch_group_profiles(group_ids)
    group_summaries = await _build_group_summaries(group_ids, profiles=profiles)
    top_groups = sorted(group_summaries, key=lambda item: item["today_message_count"], reverse=True)[:8]

    return {
        "group_count": len(group_summaries),
        "record_enabled_groups": sum(1 for item in group_summaries if item["record_enabled"]),
        "tracked_groups": sum(1 for item in group_summaries if item["history_message_count"] > 0),
        "history_message_count": sum(item["history_message_count"] for item in group_summaries),
        "today_message_count": sum(item["today_message_count"] for item in group_summaries),
        "active_members": sum(item["active_members"] for item in group_summaries),
        "stop_words_count": sum(item["stop_words_count"] for item in group_summaries),
        "violation_event_count": sum(item["violation_event_count"] for item in group_summaries),
        "cleanup_lock_count": sum(1 for item in group_summaries if item["cleanup_lock_active"]),
        "event_notice_enabled_groups": sum(1 for item in group_summaries if item["event_notice_enabled"]),
        "anti_recall_enabled_groups": sum(1 for item in group_summaries if item["anti_recall_enabled"]),
        "basic_admin_enabled_groups": sum(1 for item in group_summaries if item["basic_admin_enabled"]),
        "deputy_admin_count": sum(item["deputy_admin_count"] for item in group_summaries),
        "daily_trend": await build_global_daily_trend(group_ids),
        "top_groups": [
            {
                "group_id": item["group_id"],
                "group_name": item["group_name"],
                "member_count": item["member_count"],
                "today_message_count": item["today_message_count"],
                "history_message_count": item["history_message_count"],
            }
            for item in top_groups
        ],
        "dashboard_title": plugin_config.dashboard_title,
        "orm_enabled": plugin_config.statistics_orm_enabled,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }


async def build_operations_overview_payload() -> dict[str, Any]:
    """
    构建operationsoverviewpayload
    :return: dict[str, Any]
    """
    group_ids = await collect_dashboard_group_ids_live()
    profiles = await fetch_group_profiles(group_ids)
    group_summaries = await _build_group_summaries(group_ids, profiles=profiles)

    return {
        "group_count": len(group_summaries),
        "manageable_group_count": sum(1 for item in group_summaries if item["basic_admin_enabled"]),
        "feature_switch_entry_count": sum(item["feature_switches_enabled"] for item in group_summaries),
        "broadcast_target_count": len(group_summaries),
        "record_enabled_groups": sum(1 for item in group_summaries if item["record_enabled"]),
        "cleanup_lock_count": sum(1 for item in group_summaries if item["cleanup_lock_active"]),
        "top_groups": sorted(
            [
                {
                    "group_id": item["group_id"],
                    "group_name": item["group_name"],
                    "member_count": item["member_count"],
                    "feature_switches_enabled": item["feature_switches_enabled"],
                    "today_message_count": item["today_message_count"],
                }
                for item in group_summaries
            ],
            key=lambda item: item["today_message_count"],
            reverse=True,
        )[:8],
    }


async def list_group_summaries_payload() -> list[dict[str, Any]]:
    """
    列出群summariespayload
    :return: list[dict[str, Any]]
    """
    group_ids = await collect_dashboard_group_ids_live()
    profiles = await fetch_group_profiles(group_ids)
    return await _build_group_summaries(group_ids, profiles=profiles)


def resolve_wordcloud_output_path(group_id: int | str) -> Path:
    """
    解析词云output路径
    :param group_id: 群号
    :return: Path
    """
    return admin_path.re_img_path / f"dashboard_wordcloud_{normalize_group_id(group_id)}.png"


async def build_group_approval_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群审批payload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    terms_by_group = await orm_load_approval_terms() or {}
    admins_by_group = await approval_store.g_admin_async()
    ai_verify_config = (await ai_verify_store.load_config()).get(normalized_group_id, {"enabled": False, "prompt": ""})
    blacklist_terms = await approval_blacklist_store.get_group_blacklist(normalized_group_id)
    admin_ids = _normalize_member_ids(admins_by_group.get(normalized_group_id, []))
    admin_names = await fetch_member_display_names(normalized_group_id, admin_ids)

    return {
        "terms": list(terms_by_group.get(normalized_group_id, [])),
        "blacklist_terms": blacklist_terms,
        "group_admins": [
            {
                "user_id": user_id,
                "display_name": admin_names.get(user_id) or user_id,
            }
            for user_id in admin_ids
        ],
        "superuser_receive_enabled": str(admins_by_group.get("su", "True")) == "True",
        "ai_verify_enabled": bool(ai_verify_config.get("enabled", False)),
        "ai_verify_prompt": str(ai_verify_config.get("prompt", "")),
    }


async def build_approval_overview_payload() -> dict[str, Any]:
    """
    构建审批overviewpayload
    :return: dict[str, Any]
    """
    terms_by_group = await orm_load_approval_terms() or {}
    admins_by_group = await approval_store.g_admin_async()
    blacklist_by_group = await approval_blacklist_store.load_blacklist()
    ai_verify_config = await ai_verify_store.load_config()

    ai_enabled_groups = sorted(
        str(group_id)
        for group_id, config in ai_verify_config.items()
        if isinstance(config, dict) and config.get("enabled")
    )

    sample_group_ids = _sort_group_ids(
        set(str(group_id) for group_id in terms_by_group.keys())
        | set(str(group_id) for group_id in blacklist_by_group.keys())
        | set(ai_enabled_groups)
    )[:8]

    return {
        "group_terms_configured": len(terms_by_group),
        "group_admins_configured": len([group_id for group_id in admins_by_group.keys() if str(group_id) != "su"]),
        "blacklist_groups": len(blacklist_by_group),
        "blacklist_terms": sum(len(terms) for terms in blacklist_by_group.values()),
        "ai_verify_enabled_groups": len(ai_enabled_groups),
        "superuser_receive_enabled": str(admins_by_group.get("su", "True")) == "True",
        "sample_groups": [
            {
                "group_id": group_id,
                "terms_count": len(terms_by_group.get(group_id, [])),
                "blacklist_count": len(blacklist_by_group.get(group_id, [])),
                "ai_verify_enabled": group_id in ai_enabled_groups,
            }
            for group_id in sample_group_ids
        ],
    }


async def build_broadcast_overview_payload() -> dict[str, Any]:
    """
    构建broadcastoverviewpayload
    :return: dict[str, Any]
    """
    superusers = load_dashboard_superusers()
    config = await broadcast_store.load_broadcast_config(superusers)
    group_ids = await collect_dashboard_group_ids_live()
    profiles = await fetch_group_profiles(group_ids)

    user_items: list[dict[str, Any]] = []
    all_excluded_group_ids: set[str] = set()
    for user_id, excluded_group_ids in config.items():
        all_excluded_group_ids.update(str(group_id) for group_id in excluded_group_ids)
        user_items.append(
            {
                "user_id": str(user_id),
                "excluded_count": len(excluded_group_ids),
                "excluded_groups": [
                    {
                        "group_id": str(group_id),
                        "group_name": profiles.get(str(group_id), {}).get("group_name") or f"? {group_id}",
                    }
                    for group_id in excluded_group_ids[:8]
                ],
            }
        )

    return {
        "configured_users": len(user_items),
        "excluded_groups": len(all_excluded_group_ids),
        "total_exclusion_links": sum(item["excluded_count"] for item in user_items),
        "user_items": user_items,
    }


async def build_group_broadcast_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群broadcastpayload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    config = await broadcast_store.load_broadcast_config(load_dashboard_superusers())

    excluded_by: list[dict[str, Any]] = []
    reachable_by: list[dict[str, Any]] = []
    for user_id, excluded_group_ids in config.items():
        entry = {
            "user_id": str(user_id),
            "excluded_groups_count": len(excluded_group_ids),
        }
        if normalized_group_id in excluded_group_ids:
            excluded_by.append(entry)
        else:
            reachable_by.append(entry)

    return {
        "excluded_by": excluded_by,
        "reachable_by": reachable_by,
    }


async def build_content_guard_overview_payload() -> dict[str, Any]:
    """
    构建内容审核overviewpayload
    :return: dict[str, Any]
    """
    rules = await _load_content_guard_rules()
    group_ids = await collect_dashboard_group_ids()
    text_guard_enabled_groups = 0
    image_guard_switch_enabled_groups = 0
    violation_groups: set[str] = set()
    violation_users: set[tuple[str, str]] = set()
    recent_entries: list[dict[str, Any]] = []

    for group_id in group_ids:
        switches = await build_feature_switch_payload(group_id)
        if _is_switch_enabled(switches, "auto_ban"):
            text_guard_enabled_groups += 1
        if _is_switch_enabled(switches, "img_check"):
            image_guard_switch_enabled_groups += 1

    for group_id in group_ids:
        group_entries = await _load_violation_group_snapshot(group_id)
        if group_entries:
            violation_groups.add(str(group_id))
        for entry in group_entries:
            violation_users.add((entry["group_id"], entry["user_id"]))
        recent_entries.extend(group_entries[:3])

    recent_entries = sorted(recent_entries, key=lambda item: item["timestamp"], reverse=True)[:8]

    return {
        "rule_count": len(rules),
        "ban_rule_count": sum(1 for rule in rules if rule["ban"]),
        "delete_rule_count": sum(1 for rule in rules if rule["delete"]),
        "scoped_rule_count": sum(1 for rule in rules if rule["scope_mode"]),
        "violation_group_count": len(violation_groups),
        "violation_user_count": len(violation_users),
        "text_guard_enabled_groups": text_guard_enabled_groups,
        "image_guard_switch_enabled_groups": image_guard_switch_enabled_groups,
        "image_guard": build_image_guard_status_payload(image_guard_switch_enabled_groups > 0),
        "recent_violations": recent_entries,
        "sample_rules": rules[:8],
    }


async def build_group_content_guard_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群内容审核payload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    switches = await build_feature_switch_payload(normalized_group_id)
    rules = await _load_content_guard_rules(normalized_group_id)
    text_guard_enabled = _is_switch_enabled(switches, "auto_ban")
    image_guard_switch_enabled = _is_switch_enabled(switches, "img_check")
    image_guard = build_image_guard_status_payload(image_guard_switch_enabled)

    return {
        "rule_count": len(rules),
        "ban_rule_count": sum(1 for rule in rules if rule["ban"]),
        "delete_rule_count": sum(1 for rule in rules if rule["delete"]),
        "scoped_rule_count": sum(1 for rule in rules if rule["scope_mode"]),
        "rules": rules[:12],
        "recent_violations": (await _load_violation_group_snapshot(normalized_group_id))[:10],
        "text_guard_enabled": text_guard_enabled,
        "image_guard_enabled": image_guard["processing_enabled"],
        "image_guard_switch_enabled": image_guard_switch_enabled,
        "image_guard": image_guard,
    }


async def build_member_cleanup_overview_payload() -> dict[str, Any]:
    """
    构建成员清理overviewpayload
    :return: dict[str, Any]
    """
    locks = _list_cleanup_locks()
    profiles = await fetch_group_profiles([item["group_id"] for item in locks])

    return {
        "active_lock_count": len(locks),
        "active_groups": [
            {
                "group_id": item["group_id"],
                "group_name": profiles.get(item["group_id"], {}).get("group_name") or f"? {item['group_id']}",
                "updated_at": item["updated_at"],
            }
            for item in locks
        ],
        "supported_modes": [
            {"key": "level", "label": "按等级清理"},
            {"key": "last_sent_time", "label": "按最后发言时间清理"},
        ],
    }


def build_group_member_cleanup_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群成员清理payload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    lock = next((item for item in _list_cleanup_locks() if item["group_id"] == normalized_group_id), None)

    return {
        "lock_active": lock is not None,
        "lock_updated_at": lock["updated_at"] if lock else None,
        "supported_modes": [
            {"key": "level", "label": "按等级清理"},
            {"key": "last_sent_time", "label": "按最后发言时间清理"},
        ],
    }


async def build_group_detail_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群detailpayload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    profiles = await fetch_group_profiles([normalized_group_id])
    summary = await build_group_summary_payload(normalized_group_id, profile=profiles.get(normalized_group_id))
    statistics_payload = await build_group_statistics_payload(normalized_group_id)
    feature_switches_payload = await build_group_feature_switches_payload(normalized_group_id)

    return {
        "summary": summary,
        "statistics": statistics_payload,
        "history_ranking": statistics_payload["history_ranking"],
        "today_ranking": statistics_payload["today_ranking"],
        "daily_trend": statistics_payload["daily_trend"],
        "feature_switches": feature_switches_payload["switches"],
        "feature_switches_summary": feature_switches_payload,
        "wordcloud_keywords": statistics_payload["wordcloud_keywords"],
        "recent_messages": statistics_payload["recent_messages"],
        "approval": await build_group_approval_payload(normalized_group_id),
        "broadcast": await build_group_broadcast_payload(normalized_group_id),
        "basic_group_admin": await build_group_basic_admin_payload(normalized_group_id),
        "content_guard": await build_group_content_guard_payload(normalized_group_id),
        "member_cleanup": build_group_member_cleanup_payload(normalized_group_id),
        "event_notice": await build_group_event_notice_payload(normalized_group_id),
    }
