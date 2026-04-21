from __future__ import annotations

import datetime
from dataclasses import dataclass

from ..core.utils import participle_simple_handle
from .orm_store import load_group_stop_words, load_group_word_corpus_text
from .statistics_store import load_daily_message_stats, load_history_message_stats


@dataclass(frozen=True)
class GroupWordcloudSource:
    group_id: str
    text: str | None
    stop_words: set[str]

    @property
    def available(self) -> bool:
        """
        处理 available 的业务逻辑
        :return: bool
        """
        return self.text is not None


def _normalize_group_id(group_id: int | str) -> str:
    """
    规范化群id
    :param group_id: 群号
    :return: str
    """
    return str(group_id)


async def load_group_stop_words_snapshot(group_id: int | str) -> list[str]:
    """
    加载群stop词料snapshot
    :param group_id: 群号
    :return: list[str]
    """
    return await load_group_stop_words(group_id)


async def build_group_stop_words_snapshot(group_id: int | str) -> set[str]:
    """
    构建群stop词料snapshot
    :param group_id: 群号
    :return: set[str]
    """
    return set((await load_group_stop_words_snapshot(group_id)) + participle_simple_handle())


async def load_group_word_text_snapshot(group_id: int | str) -> str | None:
    """
    加载群词文本snapshot
    :param group_id: 群号
    :return: str | None
    """
    return await load_group_word_corpus_text(_normalize_group_id(group_id))


async def load_group_wordcloud_source(group_id: int | str) -> GroupWordcloudSource:
    """
    加载群词云source
    :param group_id: 群号
    :return: GroupWordcloudSource
    """
    normalized_group_id = _normalize_group_id(group_id)
    return GroupWordcloudSource(
        group_id=normalized_group_id,
        text=await load_group_word_text_snapshot(normalized_group_id),
        stop_words=await build_group_stop_words_snapshot(normalized_group_id),
    )


async def daily_message_stats_exists_snapshot(
    group_id: int | str,
    day: datetime.date | str | None = None,
) -> bool:
    """
    处理 daily_message_stats_exists_snapshot 的业务逻辑
    :param group_id: 群号
    :param day: day 参数
    :return: bool
    """
    return bool(await load_daily_message_stats(group_id, day))


async def load_daily_message_stats_snapshot(
    group_id: int | str,
    day: datetime.date | str | None = None,
) -> dict[str, int]:
    """
    加载每日消息statssnapshot
    :param group_id: 群号
    :param day: day 参数
    :return: dict[str, int]
    """
    return await load_daily_message_stats(group_id, day)


async def load_history_message_stats_snapshot(group_id: int | str) -> dict[str, int]:
    """
    加载历史消息statssnapshot
    :param group_id: 群号
    :return: dict[str, int]
    """
    return await load_history_message_stats(group_id)
