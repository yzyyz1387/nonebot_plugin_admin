from __future__ import annotations

import datetime as dt
import json
from typing import Any

from nonebot import logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from ..core.config import plugin_config
from ..statistics import models


def _archive_enabled() -> bool:
    """
    归档enabled
    :return: bool
    """
    return bool(
        plugin_config.statistics_orm_enabled
        and models.ORM_MODELS_AVAILABLE
        and models.RecallMessageArchive is not None
    )


def _message_record_enabled() -> bool:
    """
    处理 _message_record_enabled 的业务逻辑
    :return: bool
    """
    return bool(
        plugin_config.statistics_orm_enabled
        and models.ORM_MODELS_AVAILABLE
        and models.StatisticsMessageRecord is not None
    )


def _normalize_group_id(group_id: int | str) -> str:
    """
    规范化群id
    :param group_id: 群号
    :return: str
    """
    return str(group_id)


def _normalize_user_id(user_id: int | str) -> str:
    """
    规范化userid
    :param user_id: 用户号
    :return: str
    """
    return str(user_id)


def _normalize_message_id(message_id: int | str | None) -> str | None:
    """
    规范化消息id
    :param message_id: 标识值
    :return: str | None
    """
    if message_id in (None, ""):
        return None
    return str(message_id)


def _build_message_key(group_id: int | str, message_id: int | str | None) -> str | None:
    """
    构建消息key
    :param group_id: 群号
    :param message_id: 标识值
    :return: str | None
    """
    normalized_message_id = _normalize_message_id(message_id)
    if normalized_message_id is None:
        return None
    return f"{_normalize_group_id(group_id)}:{normalized_message_id}"


def _serialize_message_segments(message: Any) -> list[dict[str, Any]]:
    """
    处理 _serialize_message_segments 的业务逻辑
    :param message: 消息内容
    :return: list[dict[str, Any]]
    """
    if message is None:
        return []

    try:
        iterable = list(message)
    except TypeError:
        iterable = message if isinstance(message, list) else [message]

    segments: list[dict[str, Any]] = []
    for segment in iterable:
        if isinstance(segment, dict):
            seg_type = str(segment.get("type") or "").strip()
            seg_data = dict(segment.get("data") or {})
        else:
            seg_type = str(getattr(segment, "type", "") or "").strip()
            seg_data = dict(getattr(segment, "data", {}) or {})
        if not seg_type:
            continue
        segments.append({"type": seg_type, "data": seg_data})
    return segments


def _stringify_segment(segment: dict[str, Any]) -> str:
    """
    处理 _stringify_segment 的业务逻辑
    :param segment: segment 参数
    :return: str
    """
    seg_type = str(segment.get("type") or "").strip()
    seg_data = segment.get("data") or {}
    if seg_type == "text":
        return str(seg_data.get("text") or "")
    if seg_type == "at":
        qq = seg_data.get("qq")
        return f"@{qq}" if qq else "[@]"

    labels = {
        "image": "[图片]",
        "face": "[表情]",
        "record": "[语音]",
        "video": "[视频]",
        "file": "[文件]",
        "reply": "[回复]",
        "forward": "[转发消息]",
    }
    return labels.get(seg_type, f"[{seg_type or '消息'}]")


def _extract_plain_text(message_segments: list[dict[str, Any]], raw_message: str) -> str:
    """
    处理 _extract_plain_text 的业务逻辑
    :param message_segments: message_segments 参数
    :param raw_message: 原始消息文本
    :return: str
    """
    if raw_message.strip():
        return raw_message.strip()
    text = "".join(_stringify_segment(segment) for segment in message_segments).strip()
    return text


def _serialize_sender(event: GroupMessageEvent) -> dict[str, Any]:
    """
    处理 _serialize_sender 的业务逻辑
    :param event: 事件对象
    :return: dict[str, Any]
    """
    sender = getattr(event, "sender", None)
    if sender is None:
        return {"user_id": getattr(event, "user_id", None)}

    result: dict[str, Any] = {}
    for key in ("user_id", "nickname", "card", "role", "title", "sex", "age"):
        value = getattr(sender, key, None)
        if value not in (None, ""):
            result[key] = value
    if "user_id" not in result:
        result["user_id"] = getattr(event, "user_id", None)
    return result


def _event_timestamp(raw_time: Any) -> int:
    """
    处理 _event_timestamp 的业务逻辑
    :param raw_time: raw_time 参数
    :return: int
    """
    try:
        return int(raw_time)
    except (TypeError, ValueError):
        return int(dt.datetime.now().timestamp())


def _coerce_sent_at(raw_time: Any) -> dt.datetime:
    """
    处理 _coerce_sent_at 的业务逻辑
    :param raw_time: raw_time 参数
    :return: dt.datetime
    """
    try:
        return dt.datetime.fromtimestamp(int(raw_time))
    except (TypeError, ValueError, OSError):
        return dt.datetime.now()


def build_recall_message_payload(event: GroupMessageEvent) -> dict[str, Any]:
    """
    构建recall消息payload
    :param event: 事件对象
    :return: dict[str, Any]
    """
    message_id = _normalize_message_id(getattr(event, "message_id", None))
    message_segments = _serialize_message_segments(getattr(event, "message", None))
    raw_message = str(getattr(event, "raw_message", "") or "")
    group_id = _normalize_group_id(getattr(event, "group_id", ""))
    user_id = _normalize_user_id(getattr(event, "user_id", ""))
    timestamp = _event_timestamp(getattr(event, "time", None))

    return {
        "self_id": getattr(event, "self_id", None),
        "user_id": user_id,
        "time": timestamp,
        "message_id": message_id,
        "message_seq": message_id,
        "real_id": message_id,
        "real_seq": message_id,
        "message_type": str(getattr(event, "message_type", "group") or "group"),
        "sender": _serialize_sender(event),
        "raw_message": raw_message,
        "font": getattr(event, "font", 0),
        "sub_type": str(getattr(event, "sub_type", "normal") or "normal"),
        "message": message_segments,
        "message_format": "array",
        "post_type": str(getattr(event, "post_type", "message") or "message"),
        "group_id": group_id,
        "group_name": getattr(event, "group_name", None),
        "emoji_likes_list": [],
    }


async def archive_group_message_snapshot(event: GroupMessageEvent) -> bool:
    """
    归档群消息snapshot
    :param event: 事件对象
    :return: bool
    """
    if not _archive_enabled():
        return False

    message_id = _normalize_message_id(getattr(event, "message_id", None))
    message_key = _build_message_key(getattr(event, "group_id", ""), message_id)
    if message_id is None or message_key is None:
        return False

    payload = build_recall_message_payload(event)
    plain_text = _extract_plain_text(payload.get("message", []), str(payload.get("raw_message", "") or ""))
    defaults = {
        "group_id": _normalize_group_id(payload.get("group_id", "")),
        "user_id": _normalize_user_id(payload.get("user_id", "")),
        "message_id": message_id,
        "plain_text": plain_text,
        "payload_json": json.dumps(payload, ensure_ascii=False, default=str),
        "sent_at": _coerce_sent_at(payload.get("time")),
    }

    try:
        record, created = await models.RecallMessageArchive.get_or_create(
            message_key=message_key,
            defaults=defaults,
        )
        if created:
            return True

        changed = False
        for key, value in defaults.items():
            if getattr(record, key, None) != value:
                setattr(record, key, value)
                changed = True
        if changed:
            await record.save()
        return True
    except Exception as err:
        logger.debug(f"Failed to archive recall message {message_key}: {type(err).__name__}: {err}")
        return False


async def _load_archive_record(group_id: int | str, message_id: int | str | None) -> dict[str, Any] | None:
    """
    加载archive记录
    :param group_id: 群号
    :param message_id: 标识值
    :return: dict[str, Any] | None
    """
    if not _archive_enabled():
        return None

    message_key = _build_message_key(group_id, message_id)
    if message_key is None:
        return None

    try:
        record = await models.RecallMessageArchive.filter(message_key=message_key).first()
    except Exception as err:
        logger.debug(f"Failed to query recall archive {message_key}: {type(err).__name__}: {err}")
        return None
    if record is None:
        return None

    try:
        payload = json.loads(str(record.payload_json or "{}"))
    except Exception:
        payload = {}

    if isinstance(payload, dict) and payload:
        return payload

    plain_text = str(getattr(record, "plain_text", "") or "")
    normalized_group_id = _normalize_group_id(group_id)
    normalized_message_id = _normalize_message_id(message_id)
    return {
        "user_id": str(getattr(record, "user_id", "") or ""),
        "time": int(getattr(record, "sent_at", dt.datetime.now()).timestamp()),
        "message_id": normalized_message_id,
        "message_type": "group",
        "sender": {"user_id": str(getattr(record, "user_id", "") or "")},
        "raw_message": plain_text,
        "message": [{"type": "text", "data": {"text": plain_text}}] if plain_text else [],
        "message_format": "array",
        "post_type": "message",
        "group_id": normalized_group_id,
    }


async def _load_statistics_record_snapshot(
    group_id: int | str,
    message_id: int | str | None,
) -> dict[str, Any] | None:
    """
    加载statistics记录snapshot
    :param group_id: 群号
    :param message_id: 标识值
    :return: dict[str, Any] | None
    """
    if not _message_record_enabled():
        return None

    message_key = _build_message_key(group_id, message_id)
    if message_key is None:
        return None

    try:
        record = await models.StatisticsMessageRecord.filter(message_key=message_key).first()
        if record is None:
            record = await models.StatisticsMessageRecord.filter(
                group_id=_normalize_group_id(group_id),
                message_id=_normalize_message_id(message_id),
            ).first()
    except Exception as err:
        logger.debug(f"Failed to query statistics message record {message_key}: {type(err).__name__}: {err}")
        return None
    if record is None:
        return None

    plain_text = str(getattr(record, "plain_text", "") or "")
    created_at = getattr(record, "created_at", None)
    if isinstance(created_at, dt.datetime):
        timestamp = int(created_at.timestamp())
    else:
        timestamp = int(dt.datetime.now().timestamp())

    normalized_group_id = _normalize_group_id(group_id)
    normalized_message_id = _normalize_message_id(message_id)
    normalized_user_id = _normalize_user_id(getattr(record, "user_id", ""))
    return {
        "user_id": normalized_user_id,
        "time": timestamp,
        "message_id": normalized_message_id,
        "message_type": "group",
        "sender": {
            "user_id": normalized_user_id,
            "nickname": "",
            "card": "",
            "role": "member",
        },
        "raw_message": plain_text,
        "message": [{"type": "text", "data": {"text": plain_text}}] if plain_text else [],
        "message_format": "array",
        "post_type": "message",
        "group_id": normalized_group_id,
    }


async def load_recalled_message_snapshot(
    group_id: int | str,
    message_id: int | str | None,
) -> dict[str, Any] | None:
    """
    加载recalled消息snapshot
    :param group_id: 群号
    :param message_id: 标识值
    :return: dict[str, Any] | None
    """
    archived = await _load_archive_record(group_id, message_id)
    if archived is not None:
        return archived
    return await _load_statistics_record_snapshot(group_id, message_id)
