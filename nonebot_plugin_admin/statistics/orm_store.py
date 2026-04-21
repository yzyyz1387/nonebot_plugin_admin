from __future__ import annotations

import datetime
import re
from typing import Iterable

from nonebot import logger

from ..core.config import plugin_config
from ..dashboard.dashboard_oplog_service import record_oplog
from . import models
from .orm_bootstrap import ensure_statistics_orm_support

_FAILED_ACTIONS: set[str] = set()
_IMAGE_SEGMENT_PATTERN = re.compile(r"\[image:([^\]]*)\]")


def _is_orm_sync_enabled() -> bool:
    """
    处理 _is_orm_sync_enabled 的业务逻辑
    :return: bool
    """
    if not plugin_config.statistics_orm_enabled:
        return False
    ensure_statistics_orm_support()
    return bool(models.ORM_MODELS_AVAILABLE and models.StatisticsGroupRecordSetting is not None)


def _log_sync_failure(action: str, err: Exception) -> None:
    """
    处理 _log_sync_failure 的业务逻辑
    :param action: action 参数
    :param err: err 参数
    :return: None
    """
    if action in _FAILED_ACTIONS:
        logger.debug(f"Statistics ORM sync failed again ({action}): {type(err).__name__}: {err}")
        return
    _FAILED_ACTIONS.add(action)
    logger.warning(f"Statistics ORM sync failed ({action}), fallback to file storage: {type(err).__name__}: {err}")


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


def _coerce_date(
    day: datetime.date | str | None = None,
    created_at: datetime.datetime | datetime.date | int | float | str | None = None,
) -> datetime.date:
    """
    处理 _coerce_date 的业务逻辑
    :param day: day 参数
    :param created_at: 创建时间
    :return: datetime.date
    """
    if isinstance(day, datetime.date):
        return day
    if isinstance(day, str):
        return datetime.date.fromisoformat(day)
    if isinstance(created_at, datetime.datetime):
        return created_at.date()
    if isinstance(created_at, datetime.date):
        return created_at
    if isinstance(created_at, (int, float)):
        return datetime.datetime.fromtimestamp(created_at).date()
    return datetime.date.today()


def _coerce_datetime(
    created_at: datetime.datetime | datetime.date | int | float | str | None,
    stat_date: datetime.date,
) -> datetime.datetime:
    """
    处理 _coerce_datetime 的业务逻辑
    :param created_at: 创建时间
    :param stat_date: stat_date 参数
    :return: datetime.datetime
    """
    if isinstance(created_at, datetime.datetime):
        return created_at
    if isinstance(created_at, datetime.date):
        return datetime.datetime.combine(created_at, datetime.time.min)
    if isinstance(created_at, (int, float)):
        return datetime.datetime.fromtimestamp(created_at)
    if isinstance(created_at, str):
        try:
            return datetime.datetime.fromisoformat(created_at)
        except ValueError:
            return datetime.datetime.combine(stat_date, datetime.time.min)
    return datetime.datetime.now()


def _build_message_key(group_id: str, message_id: int | str | None) -> str | None:
    """
    构建消息key
    :param group_id: 群号
    :param message_id: 标识值
    :return: str | None
    """
    if message_id in (None, ""):
        return None
    return f"{group_id}:{message_id}"


def _extract_media_tags(raw_message: str) -> list[str]:
    """
    处理 _extract_media_tags 的业务逻辑
    :param raw_message: 原始消息文本
    :return: list[str]
    """
    if not raw_message:
        return []
    tags: list[str] = []
    for match in _IMAGE_SEGMENT_PATTERN.finditer(raw_message):
        segment = match.group(1)
        if "sub_type=1" in segment or "表情" in segment:
            tags.append("[表情包]")
        else:
            tags.append("[图片]")
    return tags


async def _increment_counter(model_cls, **lookup) -> bool:
    """
    处理 _increment_counter 的业务逻辑
    :param model_cls: model_cls 参数
    :param lookup: 额外关键字参数
    :return: bool
    """
    record, _ = await model_cls.get_or_create(**lookup, defaults={"message_count": 0})
    record.message_count = int(getattr(record, "message_count", 0)) + 1
    await record.save()
    return True


async def _set_counter(model_cls, message_count: int, **lookup) -> bool:
    """
    处理 _set_counter 的业务逻辑
    :param model_cls: model_cls 参数
    :param message_count: message_count 参数
    :param lookup: 额外关键字参数
    :return: bool
    """
    normalized_count = max(int(message_count), 0)
    record, created = await model_cls.get_or_create(**lookup, defaults={"message_count": normalized_count})
    if not created and int(getattr(record, "message_count", 0)) != normalized_count:
        record.message_count = normalized_count
        await record.save()
    return True


async def sync_group_record_setting(group_id: int | str, enabled: bool) -> bool:
    """
    同步群记录setting
    :param group_id: 群号
    :param enabled: 开关状态
    :return: bool
    """
    if not _is_orm_sync_enabled():
        return False

    try:
        await models.StatisticsGroupRecordSetting.get_or_create(
            group_id=_normalize_group_id(group_id),
            defaults={"enabled": bool(enabled)},
        )
        record, _ = await models.StatisticsGroupRecordSetting.get_or_create(
            group_id=_normalize_group_id(group_id),
            defaults={"enabled": bool(enabled)},
        )
        if bool(getattr(record, "enabled", False)) != bool(enabled):
            record.enabled = bool(enabled)
            await record.save()
        return True
    except Exception as err:
        _log_sync_failure("record-setting", err)
        return False


async def replace_group_stop_words(group_id: int | str, words: Iterable[str]) -> bool:
    """
    替换群stop词料
    :param group_id: 群号
    :param words: words 参数
    :return: bool
    """
    if not _is_orm_sync_enabled():
        return False

    normalized_group_id = _normalize_group_id(group_id)
    normalized_words: list[str] = []
    seen_words: set[str] = set()
    for word in words:
        normalized_word = str(word).strip()
        if not normalized_word or normalized_word in seen_words:
            continue
        seen_words.add(normalized_word)
        normalized_words.append(normalized_word)

    try:
        await models.StatisticsGroupStopWord.filter(group_id=normalized_group_id).delete()
        if normalized_words:
            await models.StatisticsGroupStopWord.bulk_create(
                [
                    models.StatisticsGroupStopWord(group_id=normalized_group_id, word=word)
                    for word in normalized_words
                ]
            )
        return True
    except Exception as err:
        _log_sync_failure("stop-words", err)
        return False


async def load_group_stop_words(group_id: int | str) -> list[str]:
    """
    加载群stop词料
    :param group_id: 群号
    :return: list[str]
    """
    if not _is_orm_sync_enabled():
        return []

    normalized_group_id = _normalize_group_id(group_id)
    try:
        rows = await models.StatisticsGroupStopWord.filter(group_id=normalized_group_id).all()
        sorted_rows = sorted(
            rows,
            key=lambda row: (
                getattr(row, "created_at", None)
                if isinstance(getattr(row, "created_at", None), datetime.datetime)
                else datetime.datetime.min,
                row.id,
            ),
        )
        return [str(row.word) for row in sorted_rows if str(getattr(row, "word", "")).strip()]
    except Exception as err:
        _log_sync_failure("stop-words-load", err)
        return []


async def load_group_word_corpus_lines(group_id: int | str) -> list[str]:
    """
    加载群词corpuslines
    :param group_id: 群号
    :return: list[str]
    """
    if not _is_orm_sync_enabled():
        return []

    normalized_group_id = _normalize_group_id(group_id)
    try:
        rows = await models.StatisticsWordCorpus.filter(group_id=normalized_group_id).all()
        sorted_rows = sorted(
            rows,
            key=lambda row: (
                getattr(row, "created_at", None)
                if isinstance(getattr(row, "created_at", None), datetime.datetime)
                else datetime.datetime.min,
                row.id,
            ),
        )
        return [str(row.content) for row in sorted_rows if str(getattr(row, "content", "")).strip()]
    except Exception as err:
        _log_sync_failure("word-corpus-load", err)
        return []


async def load_group_word_corpus_text(group_id: int | str) -> str | None:
    """
    加载群词corpus文本
    :param group_id: 群号
    :return: str | None
    """
    lines = await load_group_word_corpus_lines(group_id)
    if not lines:
        return None
    return "\n".join(lines) + "\n"


async def replace_group_word_corpus(
    group_id: int | str,
    contents: Iterable[str],
    *,
    source_type: str = "legacy",
) -> bool:
    """
    替换群词corpus
    :param group_id: 群号
    :param contents: contents 参数
    :param source_type: 来源类型
    :return: bool
    """
    if not _is_orm_sync_enabled():
        return False

    normalized_group_id = _normalize_group_id(group_id)
    normalized_contents = [str(content).strip() for content in contents if str(content).strip()]

    try:
        await models.StatisticsWordCorpus.filter(group_id=normalized_group_id).delete()
        if normalized_contents:
            await models.StatisticsWordCorpus.bulk_create(
                [
                    models.StatisticsWordCorpus(
                        group_id=normalized_group_id,
                        content=content,
                        source_type=str(source_type or "legacy"),
                    )
                    for content in normalized_contents
                ]
            )
        return True
    except Exception as err:
        _log_sync_failure("word-corpus-replace", err)
        return False


async def append_group_word_corpus(
    group_id: int | str,
    content: str,
    *,
    source_type: str = "message",
    created_at: datetime.datetime | datetime.date | int | float | str | None = None,
) -> bool:
    """
    处理 append_group_word_corpus 的业务逻辑
    :param group_id: 群号
    :param content: 内容
    :param source_type: 来源类型
    :param created_at: 创建时间
    :return: bool
    """
    if not _is_orm_sync_enabled():
        return False

    normalized_content = str(content).strip()
    if not normalized_content:
        return True

    normalized_group_id = _normalize_group_id(group_id)
    created_time = _coerce_datetime(created_at, datetime.date.today())

    try:
        await models.StatisticsWordCorpus.create(
            group_id=normalized_group_id,
            content=normalized_content,
            source_type=str(source_type or "message"),
            created_at=created_time,
        )
        return True
    except Exception as err:
        _log_sync_failure("word-corpus-append", err)
        return False


async def set_daily_message_stat(
    group_id: int | str,
    user_id: int | str,
    stat_date: datetime.date | str,
    message_count: int,
) -> bool:
    """
    处理 set_daily_message_stat 的业务逻辑
    :param group_id: 群号
    :param user_id: 用户号
    :param stat_date: stat_date 参数
    :param message_count: message_count 参数
    :return: bool
    """
    if not _is_orm_sync_enabled():
        return False

    try:
        return await _set_counter(
            models.StatisticsDailyMessageStat,
            group_id=_normalize_group_id(group_id),
            user_id=_normalize_user_id(user_id),
            stat_date=_coerce_date(stat_date),
            message_count=message_count,
        )
    except Exception as err:
        _log_sync_failure("daily-stat-import", err)
        return False


async def set_history_message_stat(group_id: int | str, user_id: int | str, message_count: int) -> bool:
    """
    处理 set_history_message_stat 的业务逻辑
    :param group_id: 群号
    :param user_id: 用户号
    :param message_count: message_count 参数
    :return: bool
    """
    if not _is_orm_sync_enabled():
        return False

    try:
        return await _set_counter(
            models.StatisticsHistoryMessageStat,
            group_id=_normalize_group_id(group_id),
            user_id=_normalize_user_id(user_id),
            message_count=message_count,
        )
    except Exception as err:
        _log_sync_failure("history-stat-import", err)
        return False


async def sync_group_message(
    group_id: int | str,
    user_id: int | str,
    message: str,
    day: datetime.date | str | None = None,
    *,
    message_id: int | str | None = None,
    created_at: datetime.datetime | datetime.date | int | float | str | None = None,
    record_text: bool,
    raw_message: str = "",
) -> bool:
    """
    同步群消息
    :param group_id: 群号
    :param user_id: 用户号
    :param message: 消息内容
    :param day: day 参数
    :param message_id: 标识值
    :param created_at: 创建时间
    :param record_text: 文本内容
    :param raw_message: 原始消息文本
    :return: bool
    """
    if not _is_orm_sync_enabled():
        return False

    normalized_group_id = _normalize_group_id(group_id)
    normalized_user_id = _normalize_user_id(user_id)
    stat_date = _coerce_date(day, created_at)
    created_time = _coerce_datetime(created_at, stat_date)
    plain_text = str(message or "")
    display_text = plain_text.strip() or str(raw_message or "").strip() or ""
    word_parts: list[str] = []
    if plain_text.strip():
        word_parts.append(plain_text.strip())
    word_parts.extend(_extract_media_tags(str(raw_message or "")))
    corpus_text = " ".join(word_parts).strip()

    try:
        await _increment_counter(
            models.StatisticsDailyMessageStat,
            group_id=normalized_group_id,
            user_id=normalized_user_id,
            stat_date=stat_date,
        )
        await _increment_counter(
            models.StatisticsHistoryMessageStat,
            group_id=normalized_group_id,
            user_id=normalized_user_id,
        )

        if record_text and corpus_text:
            await append_group_word_corpus(
                normalized_group_id,
                corpus_text,
                source_type="message",
                created_at=created_time,
            )

        if record_text and plugin_config.statistics_orm_capture_message_content and display_text:
            defaults = {
                "group_id": normalized_group_id,
                "user_id": normalized_user_id,
                "message_id": None if message_id in (None, "") else str(message_id),
                "plain_text": display_text,
                "message_length": len(display_text),
                "message_date": stat_date,
                "message_hour": created_time.hour,
                "created_at": created_time,
            }
            message_key = _build_message_key(normalized_group_id, message_id)
            if message_key:
                await models.StatisticsMessageRecord.get_or_create(message_key=message_key, defaults=defaults)
            else:
                await models.StatisticsMessageRecord.create(message_key=None, **defaults)
            await record_oplog(
                action="message_record",
                group_id=normalized_group_id,
                user_id=normalized_user_id,
                detail=display_text[:200],
            )
        return True
    except Exception as err:
        _log_sync_failure("message-record", err)
        return False
