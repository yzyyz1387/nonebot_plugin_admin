from __future__ import annotations

import datetime

from nonebot import logger

from ..core.state_feedback import build_explicit_state_message
from .orm_store import sync_group_message
from .statistics_store import disable_group_record, enable_group_record, is_group_record_enabled

RECORD_FEATURE_NAME = "本群消息记录"
RECORD_ENABLE_COMMAND = "记录本群"
RECORD_DISABLE_COMMAND = "停止记录本群"


async def handle_enable_group_recording(group_id: int | str) -> tuple[bool, str]:
    """
    处理enable群recording
    :param group_id: 群号
    :return: tuple[bool, str]
    """
    if await enable_group_record(group_id):
        return True, build_explicit_state_message(
            RECORD_FEATURE_NAME,
            enabled=True,
            enable_command=RECORD_ENABLE_COMMAND,
            disable_command=RECORD_DISABLE_COMMAND,
        )

    return False, build_explicit_state_message(
        RECORD_FEATURE_NAME,
        enabled=True,
        enable_command=RECORD_ENABLE_COMMAND,
        disable_command=RECORD_DISABLE_COMMAND,
    )


async def handle_disable_group_recording(group_id: int | str) -> tuple[bool, str]:
    """
    处理disable群recording
    :param group_id: 群号
    :return: tuple[bool, str]
    """
    if await disable_group_record(group_id):
        return True, (
            build_explicit_state_message(
                RECORD_FEATURE_NAME,
                enabled=False,
                enable_command=RECORD_ENABLE_COMMAND,
                disable_command=RECORD_DISABLE_COMMAND,
            )
            + "\n历史记录不会删除。"
        )

    return False, build_explicit_state_message(
        RECORD_FEATURE_NAME,
        enabled=False,
        enable_command=RECORD_ENABLE_COMMAND,
        disable_command=RECORD_DISABLE_COMMAND,
    )


async def record_group_message(
    group_id: int | str,
    user_id: int | str,
    message: str,
    day: datetime.date | str | None = None,
    *,
    message_id: int | str | None = None,
    created_at: datetime.datetime | datetime.date | int | float | str | None = None,
    raw_message: str = "",
) -> None:
    """
    记录群消息
    :param group_id: 群号
    :param user_id: 用户号
    :param message: 消息内容
    :param day: day 参数
    :param message_id: 标识值
    :param created_at: 创建时间
    :param raw_message: 原始消息文本
    :return: None
    """
    record_enabled = await is_group_record_enabled(group_id)
    orm_saved = await sync_group_message(
        group_id,
        user_id,
        message,
        day,
        message_id=message_id,
        created_at=created_at,
        record_text=record_enabled,
        raw_message=raw_message,
    )
    if not orm_saved:
        logger.warning("statistics ORM message write skipped or failed")
