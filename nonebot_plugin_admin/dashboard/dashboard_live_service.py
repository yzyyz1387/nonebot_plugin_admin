from __future__ import annotations

import asyncio
import datetime as dt
import math
import time
from typing import Any

import nonebot
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot

from ..broadcasting.broadcast_flow import fetch_group_catalog
from ..core.config import plugin_config
from ..core.path import build_default_switchers, get_func_display_name
from .dashboard_oplog_service import record_oplog
from ..statistics import models
from ..statistics.config_orm_store import orm_load_switcher, orm_save_switcher_group
from ..statistics.orm_bootstrap import ensure_statistics_orm_support
from ..statistics.statistics_read_service import load_group_word_text_snapshot
from ..statistics.statistics_store import is_group_record_enabled
from .dashboard_service import fetch_member_display_names, normalize_group_id

_member_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_MEMBER_CACHE_TTL = 60
_group_bot_cache: dict[str, tuple[float, Bot]] = {}
_group_bot_inflight: dict[str, asyncio.Task[Bot]] = {}
_GROUP_BOT_CACHE_TTL = 120


MESSAGE_SEGMENT_LABELS = {
    "image": "[图片]",
    "face": "[表情]",
    "record": "[语音]",
    "video": "[视频]",
    "file": "[文件]",
    "json": "[JSON]",
    "xml": "[XML]",
    "at": "[@]",
    "reply": "[回复]",
    "forward": "[合并转发]",
    "music": "[音乐]",
    "markdown": "[Markdown]",
}


HONOR_LABELS = {
    "current_talkative": "当前群聊之火",
    "talkative_list": "群聊之火",
    "performer_list": "群聊炽焰",
    "legend_list": "龙王",
    "strong_newbie_list": "冒尖小春笋",
    "emotion_list": "快乐源泉",
}


def _is_message_query_available() -> bool:
    """
    处理 _is_message_query_available 的业务逻辑
    :return: bool
    """
    if not plugin_config.statistics_orm_enabled:
        return False
    ensure_statistics_orm_support()
    return bool(models.ORM_MODELS_AVAILABLE and models.StatisticsMessageRecord is not None)


async def _first_available_bot() -> Bot:
    """
    处理 _first_available_bot 的业务逻辑
    :return: Bot
    """
    bots = list(nonebot.get_bots().values())
    if not bots:
        raise RuntimeError("No available bot instance.")
    return bots[0]


async def _find_group_bot(group_id: int | str) -> Bot:
    """
    处理 _find_group_bot 的业务逻辑
    :param group_id: 群号
    :return: Bot
    """
    normalized_group_id = int(normalize_group_id(group_id))
    cache_key = str(normalized_group_id)
    now = time.time()
    cached = _group_bot_cache.get(cache_key)
    if cached and (now - cached[0]) < _GROUP_BOT_CACHE_TTL:
        return cached[1]

    inflight = _group_bot_inflight.get(cache_key)
    if inflight is not None:
        return await inflight

    async def _resolve_group_bot() -> Bot:
        """
        解析群机器人
        :return: Bot
        """
        fallback_bot: Bot | None = None

        for bot in nonebot.get_bots().values():
            fallback_bot = bot
            try:
                group_list = await bot.get_group_list()
            except Exception:
                continue
            for group in group_list:
                if int(group.get("group_id", 0)) == normalized_group_id:
                    return bot

        if fallback_bot is not None:
            return fallback_bot

        raise RuntimeError("No available bot instance.")

    task = asyncio.create_task(_resolve_group_bot())
    _group_bot_inflight[cache_key] = task
    try:
        bot = await task
        _group_bot_cache[cache_key] = (time.time(), bot)
        return bot
    finally:
        if _group_bot_inflight.get(cache_key) is task:
            _group_bot_inflight.pop(cache_key, None)


async def _call_bot_api(bot: Bot, api: str, **params: Any) -> Any:
    """Call standard or NapCat extended API and unwrap common response envelopes."""
    try:
        if not api.startswith("_"):
            method = getattr(bot, api, None)
            if callable(method):
                try:
                    result = await method(**params)
                except TypeError:
                    result = await bot.call_api(api, **params)
            else:
                result = await bot.call_api(api, **params)
        else:
            result = await bot.call_api(api, **params)
    except Exception:
        raise

    if isinstance(result, dict) and {"status", "retcode", "data"}.issubset(result.keys()):
        return result.get("data")
    return result


def _timestamp_to_iso(raw_value: Any) -> str | None:
    """
    处理 _timestamp_to_iso 的业务逻辑
    :param raw_value: raw_value 参数
    :return: str | None
    """
    if raw_value in (None, "", 0):
        return None
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return str(raw_value)
    try:
        return dt.datetime.fromtimestamp(value).isoformat(timespec="seconds")
    except (OverflowError, OSError, ValueError):
        return str(raw_value)


def _timestamp_to_hour(raw_value: Any) -> int | None:
    """
    处理 _timestamp_to_hour 的业务逻辑
    :param raw_value: raw_value 参数
    :return: int | None
    """
    if raw_value in (None, "", 0):
        return None
    try:
        value = int(raw_value)
        return dt.datetime.fromtimestamp(value).hour
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _stringify_message_segment(segment: Any) -> str:
    """
    处理 _stringify_message_segment 的业务逻辑
    :param segment: segment 参数
    :return: str
    """
    if segment is None:
        return ""
    if isinstance(segment, str):
        return segment
    if not isinstance(segment, dict):
        return str(segment)

    segment_type = str(segment.get("type") or "").strip()
    data = segment.get("data") or {}
    if segment_type == "text":
        return str(data.get("text") or "")
    if segment_type == "at":
        qq = data.get("qq")
        return f"@{qq}" if qq else "[@]"
    if segment_type == "reply":
        reply_id = data.get("id")
        return f"[回复:{reply_id}]" if reply_id else "[回复]"
    return MESSAGE_SEGMENT_LABELS.get(segment_type, f"[{segment_type or '消息'}]")


def _extract_plain_text_from_message(message: Any, raw_message: str | None = None) -> str:
    """
    处理 _extract_plain_text_from_message 的业务逻辑
    :param message: 消息内容
    :param raw_message: 原始消息文本
    :return: str
    """
    if isinstance(message, str):
        return message.strip()
    if isinstance(message, list):
        text = "".join(_stringify_message_segment(segment) for segment in message).strip()
        if text:
            return text
    if isinstance(message, dict):
        text = _stringify_message_segment(message).strip()
        if text:
            return text
    return str(raw_message or "").strip()


def _normalize_contact_item(item: dict[str, Any]) -> dict[str, Any]:
    """
    规范化contactitem
    :param item: item 参数
    :return: dict[str, Any]
    """
    latest_message = dict(item.get("lastestMsg") or {})
    sender = dict(latest_message.get("sender") or {})
    preview = _extract_plain_text_from_message(latest_message.get("message"), latest_message.get("raw_message"))
    group_id = latest_message.get("group_id")
    chat_type = item.get("chatType")
    chat_kind = "group" if group_id not in (None, "", 0) or chat_type == 2 else "private"
    title = item.get("peerName") or item.get("remark") or item.get("sendMemberName") or item.get("sendNickName") or item.get("peerUin")
    subtitle = item.get("sendMemberName") or item.get("sendNickName") or sender.get("card") or sender.get("nickname")

    return {
        "peer_id": str(item.get("peerUin") or group_id or ""),
        "group_id": str(group_id) if group_id not in (None, "", 0) else None,
        "chat_type": chat_type,
        "chat_kind": chat_kind,
        "title": str(title or "未知会话"),
        "subtitle": str(subtitle or ""),
        "preview": preview,
        "msg_time": item.get("msgTime") or _timestamp_to_iso(latest_message.get("time")),
        "message_id": item.get("msgId") or latest_message.get("message_id"),
        "message_type": latest_message.get("message_type"),
        "sender_id": str(latest_message.get("user_id") or sender.get("user_id") or "") or None,
    }


async def fetch_group_bot_profile(group_id: int | str) -> dict[str, Any]:
    """
    拉取群机器人资料
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    bot = await _find_group_bot(normalized_group_id)
    role = "member"
    nickname = None
    card = None
    title = None

    try:
        member_info = await bot.get_group_member_info(group_id=int(normalized_group_id), user_id=int(bot.self_id))
        role = str(member_info.get("role") or "member")
        nickname = member_info.get("nickname")
        card = member_info.get("card")
        title = member_info.get("title") or member_info.get("special_title")
    except Exception as err:
        logger.debug(f"dashboard failed to fetch bot profile for group {normalized_group_id}: {type(err).__name__}: {err}")

    can_manage = role in {"owner", "admin"}
    return {
        "self_id": str(bot.self_id),
        "role": role,
        "nickname": nickname,
        "card": card,
        "title": title,
        "capabilities": {
            "can_send_message": True,
            "can_mute_members": can_manage,
            "can_kick_members": can_manage,
            "can_set_special_title": role == "owner",
            "can_whole_ban": can_manage,
            "can_mark_read": True,
        },
    }


async def build_account_overview_payload() -> dict[str, Any]:
    """
    构建accountoverviewpayload
    :return: dict[str, Any]
    """
    try:
        bot = await _first_available_bot()
    except RuntimeError:
        return {
            "available": False,
            "bot_count": 0,
            "self_id": None,
            "nickname": None,
            "online": False,
            "good": False,
            "group_count": 0,
            "friend_count": 0,
            "client_count": 0,
            "clients": [],
            "status": {},
        }

    login_info: dict[str, Any] = {}
    status_info: dict[str, Any] = {}
    clients: list[Any] = []
    group_list: list[Any] = []
    friend_list: list[Any] = []

    try:
        login_info = dict(await _call_bot_api(bot, "get_login_info") or {})
    except Exception as err:
        logger.debug(f"dashboard account overview get_login_info failed: {type(err).__name__}: {err}")
    try:
        status_info = dict(await _call_bot_api(bot, "get_status") or {})
    except Exception as err:
        logger.debug(f"dashboard account overview get_status failed: {type(err).__name__}: {err}")
    try:
        clients = list(await _call_bot_api(bot, "get_online_clients") or [])
    except Exception as err:
        logger.debug(f"dashboard account overview get_online_clients failed: {type(err).__name__}: {err}")
    try:
        group_list = list(await _call_bot_api(bot, "get_group_list") or [])
    except Exception as err:
        logger.debug(f"dashboard account overview get_group_list failed: {type(err).__name__}: {err}")
    try:
        friend_list = list(await _call_bot_api(bot, "get_friend_list") or [])
    except Exception as err:
        logger.debug(f"dashboard account overview get_friend_list failed: {type(err).__name__}: {err}")

    return {
        "available": True,
        "bot_count": len(nonebot.get_bots()),
        "self_id": str(login_info.get("user_id") or bot.self_id),
        "nickname": login_info.get("nickname"),
        "online": bool(status_info.get("online", True)),
        "good": bool(status_info.get("good", True)),
        "group_count": len(group_list),
        "friend_count": len(friend_list),
        "client_count": len(clients),
        "clients": clients,
        "status": status_info,
    }


async def build_recent_contacts_payload(*, count: int = 20) -> dict[str, Any]:
    """
    构建recentcontactspayload
    :param count: count 参数
    :return: dict[str, Any]
    """
    try:
        bot = await _first_available_bot()
    except RuntimeError:
        return {"items": [], "count": 0, "available": False}

    try:
        data = await _call_bot_api(bot, "get_recent_contact", count=max(int(count), 1))
    except Exception as err:
        logger.debug(f"dashboard recent contacts failed: {type(err).__name__}: {err}")
        return {"items": [], "count": 0, "available": False, "error": f"{type(err).__name__}: {err}"}

    raw_items = list(data or [])
    items = [_normalize_contact_item(item) for item in raw_items if isinstance(item, dict)]
    return {
        "items": items,
        "count": len(items),
        "available": True,
    }


async def build_group_profile_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群资料payload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    bot = await _find_group_bot(normalized_group_id)
    try:
        info = dict(await _call_bot_api(bot, "get_group_info", group_id=int(normalized_group_id)) or {})
    except Exception as err:
        logger.debug(f"dashboard get_group_info failed for {normalized_group_id}: {type(err).__name__}: {err}")
        return {
            "group_id": normalized_group_id,
            "group_name": None,
            "group_all_shut": False,
            "member_count": None,
            "max_member_count": None,
            "group_remark": None,
            "available": False,
            "error": f"{type(err).__name__}: {err}",
        }

    return {
        "group_id": str(info.get("group_id") or normalized_group_id),
        "group_name": info.get("group_name"),
        "group_all_shut": bool(info.get("group_all_shut")),
        "member_count": info.get("member_count"),
        "max_member_count": info.get("max_member_count"),
        "group_remark": info.get("group_remark"),
        "available": True,
        "raw": info,
    }


def _require_capability(bot_profile: dict[str, Any], capability_key: str, detail: str) -> None:
    """
    处理 _require_capability 的业务逻辑
    :param bot_profile: bot_profile 参数
    :param capability_key: capability_key 参数
    :param detail: detail 参数
    :return: None
    """
    capabilities = dict(bot_profile.get("capabilities") or {})
    if not capabilities.get(capability_key, False):
        raise PermissionError(detail)


def _normalize_member_payload(member: dict[str, Any]) -> dict[str, Any]:
    """
    规范化成员payload
    :param member: member 参数
    :return: dict[str, Any]
    """
    role = str(member.get("role") or "member")
    level = member.get("level")
    if level in (None, ""):
        level = member.get("qqLevel", member.get("qq_level"))

    return {
        "user_id": str(member.get("user_id")),
        "nickname": member.get("nickname"),
        "card": member.get("card"),
        "display_name": member.get("card") or member.get("nickname") or str(member.get("user_id")),
        "role": role,
        "title": member.get("title") or member.get("special_title"),
        "level": level,
        "join_time": member.get("join_time"),
        "last_sent_time": member.get("last_sent_time"),
        "shut_up_timestamp": member.get("shut_up_timestamp"),
    }


async def build_group_members_payload(
    group_id: int | str,
    *,
    page: int = 1,
    page_size: int = 50,
    keyword: str = "",
) -> dict[str, Any]:
    """
    构建群成员payload
    :param group_id: 群号
    :param page: 页码
    :param page_size: 分页大小
    :param keyword: 关键字
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    normalized_page = max(int(page), 1)
    normalized_page_size = max(1, min(int(page_size), 200))
    normalized_keyword = keyword.strip().lower()
    bot = await _find_group_bot(normalized_group_id)

    cache_key = str(normalized_group_id)
    now = time.time()
    cached = _member_cache.get(cache_key)
    if cached and (now - cached[0]) < _MEMBER_CACHE_TTL:
        members = cached[1]
    else:
        members = await bot.get_group_member_list(group_id=int(normalized_group_id))
        _member_cache[cache_key] = (now, members)

    normalized_members = [_normalize_member_payload(member) for member in members]
    normalized_members.sort(
        key=lambda item: (
            {"owner": 0, "admin": 1, "member": 2}.get(item["role"], 3),
            (item["display_name"] or item["user_id"]).lower(),
        )
    )

    if normalized_keyword:
        normalized_members = [
            item
            for item in normalized_members
            if normalized_keyword in str(item["user_id"]).lower()
            or normalized_keyword in str(item["nickname"] or "").lower()
            or normalized_keyword in str(item["card"] or "").lower()
            or normalized_keyword in str(item["display_name"] or "").lower()
        ]

    total = len(normalized_members)
    total_pages = max(1, math.ceil(total / normalized_page_size)) if total else 1
    start = (normalized_page - 1) * normalized_page_size
    end = start + normalized_page_size
    items = normalized_members[start:end]

    return {
        "group_id": normalized_group_id,
        "items": items,
        "pagination": {
            "page": normalized_page,
            "page_size": normalized_page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": normalized_page < total_pages,
            "has_prev": normalized_page > 1,
        },
        "bot_profile": await fetch_group_bot_profile(normalized_group_id),
    }


async def _build_group_messages_from_napcat_history(
    group_id: str,
    *,
    limit: int,
    before_id: int | None,
    after_id: int | None,
) -> dict[str, Any]:
    """
    构建群消息fromnapcat历史
    :param group_id: 群号
    :param limit: 数量限制
    :param before_id: 标识值
    :param after_id: 标识值
    :return: dict[str, Any]
    """
    bot = await _find_group_bot(group_id)
    history_cursor = int(before_id) if before_id is not None else 0
    history_payload = await _call_bot_api(
        bot,
        "get_group_msg_history",
        group_id=int(group_id),
        message_seq=history_cursor,
        count=int(limit),
        reverseOrder=False,
    )
    raw_messages = list((history_payload or {}).get("messages") or [])

    items: list[dict[str, Any]] = []
    for index, message in enumerate(raw_messages, start=1):
        if not isinstance(message, dict):
            continue
        sender = dict(message.get("sender") or {})
        message_seq = message.get("message_seq") or message.get("real_seq") or index
        try:
            item_id = int(message_seq)
        except (TypeError, ValueError):
            item_id = index
        plain_text = _extract_plain_text_from_message(message.get("message"), message.get("raw_message"))
        items.append(
            {
                "id": item_id,
                "message_id": message.get("message_id") or message.get("real_id"),
                "user_id": str(message.get("user_id") or sender.get("user_id") or "") or None,
                "display_name": sender.get("card") or sender.get("nickname") or str(message.get("user_id") or "未知成员"),
                "plain_text": plain_text,
                "message_length": len(plain_text),
                "created_at": _timestamp_to_iso(message.get("time")),
                "message_date": _timestamp_to_iso(message.get("time")),
                "message_hour": _timestamp_to_hour(message.get("time")),
                "raw_message": message.get("raw_message"),
                "message_segments": message.get("message"),
            }
        )

    items.sort(key=lambda item: item["id"])
    if after_id is not None:
        items = [item for item in items if item["id"] > int(after_id)]

    latest_id = max((item["id"] for item in items), default=None)
    next_before_id = min((item["id"] for item in items), default=None)
    return {
        "group_id": group_id,
        "mode": "napcat_history",
        "orm_enabled": False,
        "record_enabled": await is_group_record_enabled(group_id),
        "items": items,
        "pagination": {
            "limit": int(limit),
            "before_id": before_id,
            "after_id": after_id,
            "has_more": len(items) >= int(limit),
            "next_before_id": next_before_id,
            "latest_id": latest_id,
        },
    }


async def build_group_messages_payload(
    group_id: int | str,
    *,
    limit: int = 50,
    before_id: int | None = None,
    after_id: int | None = None,
) -> dict[str, Any]:
    """
    构建群消息payload
    :param group_id: 群号
    :param limit: 数量限制
    :param before_id: 标识值
    :param after_id: 标识值
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    normalized_limit = max(1, min(int(limit), 100))

    if _is_message_query_available():
        base_query = models.StatisticsMessageRecord.filter(group_id=normalized_group_id)
        if after_id is not None:
            records = await base_query.filter(id__gt=int(after_id)).order_by("id").limit(normalized_limit)
            has_more = len(records) >= normalized_limit
            next_before_id = None
        else:
            query = base_query.order_by("-id")
            if before_id is not None:
                query = query.filter(id__lt=int(before_id))
            records = list(await query.limit(normalized_limit))
            records.reverse()
            first_id = records[0].id if records else None
            has_more = bool(first_id and await base_query.filter(id__lt=int(first_id)).exists())
            next_before_id = first_id if has_more else None

        member_names = await fetch_member_display_names(
            normalized_group_id,
            [str(record.user_id) for record in records],
        )
        latest_record = await base_query.order_by("-id").first()

        return {
            "group_id": normalized_group_id,
            "mode": "orm",
            "orm_enabled": True,
            "record_enabled": await is_group_record_enabled(normalized_group_id),
            "items": [
                {
                    "id": int(record.id),
                    "message_id": record.message_id,
                    "user_id": str(record.user_id),
                    "display_name": member_names.get(str(record.user_id)) or str(record.user_id),
                    "plain_text": record.plain_text,
                    "message_length": int(record.message_length),
                    "created_at": record.created_at.isoformat(),
                    "message_date": record.message_date.isoformat(),
                    "message_hour": int(record.message_hour),
                }
                for record in records
            ],
            "pagination": {
                "limit": normalized_limit,
                "before_id": before_id,
                "after_id": after_id,
                "has_more": has_more,
                "next_before_id": next_before_id,
                "latest_id": int(latest_record.id) if latest_record else None,
            },
        }

    try:
        return await _build_group_messages_from_napcat_history(
            normalized_group_id,
            limit=normalized_limit,
            before_id=before_id,
            after_id=after_id,
        )
    except Exception as err:
        logger.debug(
            f"dashboard failed to fetch NapCat group history for {normalized_group_id}: {type(err).__name__}: {err}"
        )

    text = await load_group_word_text_snapshot(normalized_group_id) or ""
    lines = [line for line in text.splitlines() if line.strip()]
    indexed_lines = [{"id": index + 1, "plain_text": line} for index, line in enumerate(lines)]

    if after_id is not None:
        visible_items = [item for item in indexed_lines if item["id"] > int(after_id)][:normalized_limit]
        has_more = len(visible_items) >= normalized_limit
        next_before_id = None
    else:
        end_position = len(indexed_lines)
        if before_id is not None:
            end_position = max(int(before_id) - 1, 0)
        start_position = max(end_position - normalized_limit, 0)
        visible_items = indexed_lines[start_position:end_position]
        has_more = start_position > 0
        next_before_id = visible_items[0]["id"] if has_more and visible_items else None

    latest_id = indexed_lines[-1]["id"] if indexed_lines else None
    return {
        "group_id": normalized_group_id,
        "mode": "text_fallback",
        "orm_enabled": False,
        "record_enabled": await is_group_record_enabled(normalized_group_id),
        "items": [
            {
                "id": item["id"],
                "message_id": None,
                "user_id": None,
                "display_name": "文本记录",
                "plain_text": item["plain_text"],
                "message_length": len(item["plain_text"]),
                "created_at": None,
                "message_date": None,
                "message_hour": None,
            }
            for item in visible_items
        ],
        "pagination": {
            "limit": normalized_limit,
            "before_id": before_id,
            "after_id": after_id,
            "has_more": has_more,
            "next_before_id": next_before_id,
            "latest_id": latest_id,
        },
    }


async def build_group_announcements_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群announcementspayload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    bot = await _find_group_bot(normalized_group_id)
    try:
        raw_items = list(await _call_bot_api(bot, "_get_group_notice", group_id=int(normalized_group_id)) or [])
    except Exception as err:
        logger.debug(f"dashboard get group notice failed for {normalized_group_id}: {type(err).__name__}: {err}")
        return {"group_id": normalized_group_id, "items": [], "available": False, "error": f"{type(err).__name__}: {err}"}

    items = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        message = dict(item.get("message") or {})
        images = list(message.get("image") or [])
        items.append(
            {
                "notice_id": item.get("notice_id"),
                "sender_id": str(item.get("sender_id") or "") or None,
                "publish_time": _timestamp_to_iso(item.get("publish_time")),
                "text": message.get("text") or "",
                "images": images,
                "image_count": len(images),
            }
        )
    return {
        "group_id": normalized_group_id,
        "items": items,
        "available": True,
    }


async def build_group_essence_payload(group_id: int | str) -> dict[str, Any]:
    """
    构建群essencepayload
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    bot = await _find_group_bot(normalized_group_id)
    try:
        raw_items = list(await _call_bot_api(bot, "get_essence_msg_list", group_id=int(normalized_group_id)) or [])
    except Exception as err:
        logger.debug(f"dashboard get essence list failed for {normalized_group_id}: {type(err).__name__}: {err}")
        return {"group_id": normalized_group_id, "items": [], "available": False, "error": f"{type(err).__name__}: {err}"}

    items = []
    for index, item in enumerate(raw_items, start=1):
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        plain_text = _extract_plain_text_from_message(content, None)
        items.append(
            {
                "id": item.get("message_id") or index,
                "message_id": item.get("message_id"),
                "sender_id": str(item.get("sender_id") or "") or None,
                "sender_nick": item.get("sender_nick"),
                "operator_id": str(item.get("operator_id") or "") or None,
                "operator_nick": item.get("operator_nick"),
                "operator_time": _timestamp_to_iso(item.get("operator_time")),
                "plain_text": plain_text,
                "content": content,
            }
        )
    return {
        "group_id": normalized_group_id,
        "items": items,
        "available": True,
    }


async def build_group_honors_payload(group_id: int | str, *, honor_type: str = "all") -> dict[str, Any]:
    """
    构建群honorspayload
    :param group_id: 群号
    :param honor_type: honor_type 参数
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    bot = await _find_group_bot(normalized_group_id)
    normalized_type = str(honor_type or "all")

    try:
        payload = dict(
            await _call_bot_api(
                bot,
                "get_group_honor_info",
                group_id=int(normalized_group_id),
                type=normalized_type,
            )
            or {}
        )
    except Exception as err:
        logger.debug(f"dashboard get group honor failed for {normalized_group_id}: {type(err).__name__}: {err}")
        return {
            "group_id": normalized_group_id,
            "honor_type": normalized_type,
            "sections": [],
            "available": False,
            "error": f"{type(err).__name__}: {err}",
        }

    sections = []
    for key, label in HONOR_LABELS.items():
        value = payload.get(key)
        if key == "current_talkative":
            if isinstance(value, dict) and value:
                sections.append({"key": key, "label": label, "items": [value], "count": 1})
            continue
        items = list(value or []) if isinstance(value, list) else []
        sections.append({"key": key, "label": label, "items": items, "count": len(items)})

    return {
        "group_id": normalized_group_id,
        "honor_type": normalized_type,
        "sections": sections,
        "available": True,
        "raw": payload,
    }


async def build_group_files_payload(
    group_id: int | str,
    *,
    folder_id: str | None = None,
    folder: str | None = None,
    file_count: int = 50,
) -> dict[str, Any]:
    """
    构建群文件payload
    :param group_id: 群号
    :param folder_id: 标识值
    :param folder: folder 参数
    :param file_count: file_count 参数
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    normalized_file_count = max(1, min(int(file_count), 200))
    bot = await _find_group_bot(normalized_group_id)

    system_info: dict[str, Any] = {}
    try:
        system_info = dict(await _call_bot_api(bot, "get_group_file_system_info", group_id=int(normalized_group_id)) or {})
    except Exception as err:
        logger.debug(f"dashboard get group file system info failed for {normalized_group_id}: {type(err).__name__}: {err}")

    try:
        if folder_id or folder:
            listing = dict(
                await _call_bot_api(
                    bot,
                    "get_group_files_by_folder",
                    group_id=int(normalized_group_id),
                    folder_id=folder_id,
                    folder=folder,
                    file_count=normalized_file_count,
                )
                or {}
            )
        else:
            listing = dict(
                await _call_bot_api(
                    bot,
                    "get_group_root_files",
                    group_id=int(normalized_group_id),
                    file_count=normalized_file_count,
                )
                or {}
            )
    except Exception as err:
        logger.debug(f"dashboard get group files failed for {normalized_group_id}: {type(err).__name__}: {err}")
        return {
            "group_id": normalized_group_id,
            "system_info": system_info,
            "files": [],
            "folders": [],
            "available": False,
            "error": f"{type(err).__name__}: {err}",
        }

    files = []
    for item in list(listing.get("files") or []):
        if not isinstance(item, dict):
            continue
        files.append(
            {
                **item,
                "upload_time_iso": _timestamp_to_iso(item.get("upload_time")),
                "modify_time_iso": _timestamp_to_iso(item.get("modify_time")),
                "dead_time_iso": _timestamp_to_iso(item.get("dead_time")),
            }
        )

    folders = list(listing.get("folders") or [])
    return {
        "group_id": normalized_group_id,
        "folder_id": folder_id,
        "folder": folder,
        "system_info": system_info,
        "files": files,
        "folders": folders,
        "available": True,
    }


async def send_group_message_action(group_id: int | str, message: str) -> dict[str, Any]:
    """
    发送群消息action
    :param group_id: 群号
    :param message: 消息内容
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    bot = await _find_group_bot(normalized_group_id)
    result = await bot.send_group_msg(group_id=int(normalized_group_id), message=message)
    await record_oplog(
        action="send_message",
        group_id=normalized_group_id,
        detail=f"发送消息: {message[:80]}{'...' if len(message) > 80 else ''}",
    )
    try:
        from ..statistics.orm_store import sync_group_message
        from ..statistics.statistics_store import is_group_record_enabled

        bot_self_id = str(bot.self_id)
        sent_message_id = result.get("message_id") if isinstance(result, dict) else None
        record_enabled = await is_group_record_enabled(normalized_group_id)
        await sync_group_message(
            normalized_group_id,
            bot_self_id,
            message,
            message_id=sent_message_id,
            created_at=dt.datetime.now(),
            record_text=record_enabled,
            raw_message=message,
        )
    except Exception as err:
        logger.debug(f"Failed to record bot sent message: {type(err).__name__}: {err}")
    return {
        "group_id": normalized_group_id,
        "message": str(message),
        "result": result,
    }


async def set_group_whole_ban_action(group_id: int | str, enabled: bool) -> dict[str, Any]:
    """
    处理 set_group_whole_ban_action 的业务逻辑
    :param group_id: 群号
    :param enabled: 开关状态
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    bot_profile = await fetch_group_bot_profile(normalized_group_id)
    _require_capability(bot_profile, "can_whole_ban", "Bot does not have permission to whole-ban this group.")
    bot = await _find_group_bot(normalized_group_id)
    await _call_bot_api(bot, "set_group_whole_ban", group_id=int(normalized_group_id), enable=bool(enabled))
    await record_oplog(
        action="whole_ban",
        group_id=normalized_group_id,
        detail=f"{'开启' if enabled else '关闭'}全员禁言",
    )
    return {
        "group_id": normalized_group_id,
        "enabled": bool(enabled),
    }


async def mark_group_msg_as_read_action(group_id: int | str) -> dict[str, Any]:
    """
    处理 mark_group_msg_as_read_action 的业务逻辑
    :param group_id: 群号
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    bot = await _find_group_bot(normalized_group_id)
    await _call_bot_api(bot, "mark_group_msg_as_read", group_id=int(normalized_group_id))
    await record_oplog(
        action="mark_read",
        group_id=normalized_group_id,
        detail="标记群消息已读",
    )
    return {
        "group_id": normalized_group_id,
        "marked": True,
    }


async def set_group_feature_switch_action(group_id: int | str, switch_key: str, enabled: bool) -> dict[str, Any]:
    """
    处理 set_group_feature_switch_action 的业务逻辑
    :param group_id: 群号
    :param switch_key: switch_key 参数
    :param enabled: 开关状态
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    normalized_switch_key = str(switch_key).strip()
    default_switchers = build_default_switchers()
    if normalized_switch_key not in default_switchers:
        raise KeyError(normalized_switch_key)

    orm_snapshot = await orm_load_switcher()
    group_switches = dict(build_default_switchers())
    group_switches.update(orm_snapshot.get(normalized_group_id, {}))
    group_switches[normalized_switch_key] = bool(enabled)
    await orm_save_switcher_group(normalized_group_id, group_switches)
    label = get_func_display_name(normalized_switch_key)
    await record_oplog(
        action="feature_switch",
        group_id=normalized_group_id,
        detail=f"{'开启' if enabled else '关闭'}功能 [{label}]",
    )
    return {
        "group_id": normalized_group_id,
        "switch_key": normalized_switch_key,
        "enabled": bool(enabled),
        "label": label,
    }


async def broadcast_message_action(
    message: str,
    *,
    include_group_ids: list[str] | None = None,
    exclude_group_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    处理 broadcast_message_action 的业务逻辑
    :param message: 消息内容
    :param include_group_ids: 标识列表
    :param exclude_group_ids: 标识列表
    :return: dict[str, Any]
    """
    normalized_message = str(message).strip()
    if not normalized_message:
        raise ValueError("Message cannot be empty.")

    bot = await _find_group_bot(include_group_ids[0] if include_group_ids else "0")
    group_catalog = await fetch_group_catalog(bot)
    include_set = {normalize_group_id(item) for item in include_group_ids or []}
    exclude_set = {normalize_group_id(item) for item in exclude_group_ids or []}
    target_groups = [
        group
        for group in group_catalog
        if (not include_set or normalize_group_id(group["group_id"]) in include_set)
        and normalize_group_id(group["group_id"]) not in exclude_set
    ]

    success: list[str] = []
    failed: list[dict[str, Any]] = []
    for group in target_groups:
        group_id = normalize_group_id(group["group_id"])
        try:
            await bot.send_group_msg(group_id=int(group_id), message=normalized_message)
            success.append(group_id)
        except Exception as err:
            failed.append(
                {
                    "group_id": group_id,
                    "group_name": group.get("group_name"),
                    "error": f"{type(err).__name__}: {err}",
                }
            )
            logger.error("dashboard broadcast failed for group %s: %s", group_id, err)

    await record_oplog(
        action="broadcast",
        detail=f"广播消息至 {len(target_groups)} 个群，成功 {len(success)} 个",
        extra={
            "success_count": len(success),
            "failed_count": len(failed),
            "target_count": len(target_groups),
        },
    )

    return {
        "message": normalized_message,
        "success_group_ids": success,
        "failed_groups": failed,
        "target_count": len(target_groups),
        "success_count": len(success),
        "failed_count": len(failed),
    }


async def mute_group_member_action(group_id: int | str, user_id: int | str, duration: int) -> dict[str, Any]:
    """
    处理 mute_group_member_action 的业务逻辑
    :param group_id: 群号
    :param user_id: 用户号
    :param duration: duration 参数
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    normalized_user_id = str(user_id)
    bot_profile = await fetch_group_bot_profile(normalized_group_id)
    _require_capability(bot_profile, "can_mute_members", "Bot does not have permission to mute members in this group.")
    bot = await _find_group_bot(normalized_group_id)
    actual_duration = max(int(duration), 0)
    await bot.set_group_ban(
        group_id=int(normalized_group_id),
        user_id=int(normalized_user_id),
        duration=actual_duration,
    )
    await record_oplog(
        action="mute_member",
        group_id=normalized_group_id,
        user_id=normalized_user_id,
        detail=f"禁言用户 {normalized_user_id} {actual_duration}秒",
    )
    return {
        "group_id": normalized_group_id,
        "user_id": normalized_user_id,
        "duration": actual_duration,
    }


async def kick_group_member_action(
    group_id: int | str,
    user_id: int | str,
    *,
    reject_add_request: bool = False,
) -> dict[str, Any]:
    """
    处理 kick_group_member_action 的业务逻辑
    :param group_id: 群号
    :param user_id: 用户号
    :param reject_add_request: reject_add_request 参数
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    normalized_user_id = str(user_id)
    bot_profile = await fetch_group_bot_profile(normalized_group_id)
    _require_capability(bot_profile, "can_kick_members", "Bot does not have permission to kick members in this group.")
    bot = await _find_group_bot(normalized_group_id)
    await bot.set_group_kick(
        group_id=int(normalized_group_id),
        user_id=int(normalized_user_id),
        reject_add_request=bool(reject_add_request),
    )
    await record_oplog(
        action="kick_member",
        group_id=normalized_group_id,
        user_id=normalized_user_id,
        detail=f"踢出用户 {normalized_user_id}{'(拒绝再加群)' if reject_add_request else ''}",
    )
    return {
        "group_id": normalized_group_id,
        "user_id": normalized_user_id,
        "reject_add_request": bool(reject_add_request),
    }


async def set_group_special_title_action(group_id: int | str, user_id: int | str, special_title: str) -> dict[str, Any]:
    """
    处理 set_group_special_title_action 的业务逻辑
    :param group_id: 群号
    :param user_id: 用户号
    :param special_title: special_title 参数
    :return: dict[str, Any]
    """
    normalized_group_id = normalize_group_id(group_id)
    normalized_user_id = str(user_id)
    bot_profile = await fetch_group_bot_profile(normalized_group_id)
    _require_capability(bot_profile, "can_set_special_title", "Bot does not have permission to set special titles in this group.")
    bot = await _find_group_bot(normalized_group_id)
    await bot.set_group_special_title(
        group_id=int(normalized_group_id),
        user_id=int(normalized_user_id),
        special_title=str(special_title),
        duration=-1,
    )
    await record_oplog(
        action="special_title",
        group_id=normalized_group_id,
        user_id=normalized_user_id,
        detail=f"设置用户 {normalized_user_id} 头衔为 [{special_title or '(清空)'}]",
    )
    return {
        "group_id": normalized_group_id,
        "user_id": normalized_user_id,
        "special_title": str(special_title),
    }
