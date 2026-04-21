from __future__ import annotations

import datetime as dt
from collections.abc import Iterable

from nonebot import logger
from nonebot.adapters.onebot.v11 import Message, MessageSegment


def should_forward_recall(
    user_id: int,
    operator_id: int,
    operator_role: str,
    superusers: Iterable[str | int],
) -> bool:
    """
    处理 should_forward_recall 的业务逻辑
    :param user_id: 用户号
    :param operator_id: 标识值
    :param operator_role: operator_role 参数
    :param superusers: 超管列表
    :return: bool
    """
    if int(user_id) != int(operator_id):
        return False
    if str(operator_id) in {str(superuser) for superuser in superusers}:
        return False
    return operator_role == "member"


def _format_timestamp(raw_time) -> str:
    """
    格式化timestamp
    :param raw_time: raw_time 参数
    :return: str
    """
    try:
        ts = int(raw_time)
        return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OSError):
        return str(raw_time)


def _segment_to_message_segment(seg: dict) -> MessageSegment | None:
    """
    处理 _segment_to_message_segment 的业务逻辑
    :param seg: seg 参数
    :return: MessageSegment | None
    """
    seg_type = seg.get("type", "")
    seg_data = seg.get("data", {})
    if not seg_type:
        return None
    try:
        return MessageSegment(type_=seg_type, data=seg_data)
    except Exception:
        pass
    constructors = {
        "text": lambda d: MessageSegment.text(d.get("text", "")),
        "image": lambda d: MessageSegment.image(d.get("url", d.get("file", ""))),
        "face": lambda d: MessageSegment.face(int(d.get("id", 0))),
        "at": lambda d: MessageSegment.at(d.get("qq", "")),
        "record": lambda d: MessageSegment.record(d.get("url", d.get("file", ""))),
        "video": lambda d: MessageSegment.video(d.get("url", d.get("file", ""))),
        "file": lambda d: MessageSegment.file(d.get("url", d.get("file", "")), d.get("name", "")),
        "reply": lambda d: MessageSegment.reply(int(d.get("id", 0))),
    }
    constructor = constructors.get(seg_type)
    if constructor:
        try:
            return constructor(seg_data)
        except Exception:
            return None
    return None


def _extract_plain_from_segments(payload: list) -> str:
    """
    处理 _extract_plain_from_segments 的业务逻辑
    :param payload: 载荷数据
    :return: str
    """
    parts: list[str] = []
    for segment in payload:
        if not isinstance(segment, dict):
            continue
        seg_type = segment.get("type", "")
        seg_data = segment.get("data", {})
        if seg_type == "text":
            text = seg_data.get("text", "")
            if text:
                parts.append(text)
        elif seg_type == "image":
            parts.append("[图片]")
        elif seg_type == "face":
            parts.append(f"[表情{seg_data.get('id', '')}]")
        elif seg_type == "at":
            qq = seg_data.get("qq", "")
            parts.append(f"@{qq}")
        elif seg_type == "record":
            parts.append("[语音]")
        elif seg_type == "video":
            parts.append("[视频]")
        elif seg_type == "file":
            parts.append("[文件]")
        elif seg_type == "reply":
            parts.append("[回复]")
        elif seg_type == "forward":
            parts.append("[转发消息]")
        else:
            if seg_type:
                parts.append(f"[{seg_type}]")
            else:
                parts.append(str(segment))
    return " ".join(parts) if parts else ""


def _parse_cq_message(raw_message: str) -> Message | None:
    """
    解析cq消息
    :param raw_message: 原始消息文本
    :return: Message | None
    """
    text = str(raw_message or "").strip()
    if not text or "[CQ:" not in text:
        return None
    try:
        parsed = Message(text)
    except Exception:
        return None
    if not parsed:
        return None
    if all(getattr(segment, "type", "") == "text" for segment in parsed):
        return None
    return parsed


def _extract_cq_payload_text(payload: list) -> str | None:
    """
    处理 _extract_cq_payload_text 的业务逻辑
    :param payload: 载荷数据
    :return: str | None
    """
    text_parts: list[str] = []
    for segment in payload:
        if isinstance(segment, dict):
            if segment.get("type") != "text":
                return None
            text_parts.append(str((segment.get("data") or {}).get("text") or ""))
            continue
        if isinstance(segment, MessageSegment):
            if segment.type != "text":
                return None
            text_parts.append(str(segment.data.get("text") or ""))
            continue
        return None
    text = "".join(text_parts).strip()
    return text if "[CQ:" in text else None


def build_recall_message(operator_info: dict, recalled_message: dict) -> Message | str:
    """
    构建recall消息
    :param operator_info: operator_info 参数
    :param recalled_message: recalled_message 参数
    :return: Message | str
    """
    operator_name = operator_info.get("card") or operator_info.get("nickname") or str(operator_info["user_id"])
    notice = f"检测到 {operator_name}({operator_info['user_id']}) 撤回了一条消息：\n\n"

    payload = recalled_message.get("message")

    if payload is None or (isinstance(payload, list) and len(payload) == 0):
        raw_message = recalled_message.get("raw_message", "")
        if raw_message:
            parsed = _parse_cq_message(raw_message)
            if parsed is not None:
                return Message([MessageSegment.text(notice), *list(parsed)])
            return notice + raw_message

        sender = recalled_message.get("sender", {})
        sender_name = sender.get("nickname", "") or sender.get("card", "")
        time_raw = recalled_message.get("time", "")
        time_str = _format_timestamp(time_raw) if time_raw else ""
        fallback_parts = []
        if sender_name:
            fallback_parts.append(f"发送者：{sender_name}")
        if time_str:
            fallback_parts.append(f"时间：{time_str}")
        fallback = "、".join(fallback_parts)
        return notice + f"（消息内容获取失败，{fallback}）" if fallback else notice + "（消息内容获取失败，可能已被服务器删除）"

    if isinstance(payload, str):
        parsed = _parse_cq_message(payload)
        if parsed is not None:
            return Message([MessageSegment.text(notice), *list(parsed)])
        return notice + payload

    cq_payload_text = _extract_cq_payload_text(payload)
    if cq_payload_text:
        parsed = _parse_cq_message(cq_payload_text)
        if parsed is not None:
            return Message([MessageSegment.text(notice), *list(parsed)])

    segments = [MessageSegment.text(notice)]
    for segment in payload:
        if isinstance(segment, dict):
            ms = _segment_to_message_segment(segment)
            if ms is not None:
                segments.append(ms)
                continue
        if isinstance(segment, MessageSegment):
            segments.append(segment)
            continue

    if len(segments) == 1:
        plain = _extract_plain_from_segments(payload)
        if plain:
            segments.append(MessageSegment.text(plain))
        else:
            segments.append(MessageSegment.text("（消息内容无法解析）"))

    return Message(segments)
