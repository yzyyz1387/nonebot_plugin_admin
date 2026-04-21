import re
from typing import Iterable, Optional

from fuzzyfinder import fuzzyfinder
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot, GroupRequestEvent

from . import approval_blacklist_store
from .approval_store import g_admin_async
from .approval_text import (
    REQUEST_BLACKLIST_HIT_LOG,
    REQUEST_BLACKLIST_REASON_LOG,
    REQUEST_DENY_REASON,
    REQUEST_SKIP_LOG,
    format_request_approved,
    format_request_rejected,
)
from .approval_verify import verify


def _extract_request_answer(comment: str) -> str:
    """
    处理 _extract_request_answer 的业务逻辑
    :param comment: 验证文本
    :return: str
    """
    matched = re.findall(re.compile(r"答案：?(.*)"), comment)
    if matched and matched[0]:
        return matched[0]
    return comment


async def _match_blacklist_term(gid: str, word: str) -> Optional[list[str]]:
    """
    处理 _match_blacklist_term 的业务逻辑
    :param gid: 群号
    :param word: word 参数
    :return: Optional[list[str]]
    """
    blacklist = await approval_blacklist_store.get_group_blacklist(gid)
    if not blacklist:
        return None

    result = list(fuzzyfinder(word, blacklist))
    if result and len(word) >= len(result[0]) / 3:
        return result
    return None


async def _notify_admins(bot: Bot, gid: str, message: str, superusers: Iterable[str]):
    """
    通知管理员
    :param bot: Bot 实例
    :param gid: 群号
    :param message: 消息内容
    :param superusers: 超管列表
    :return: None
    """
    admins = await g_admin_async()
    if admins.get("su") == "True":
        for q in superusers:
            await bot.send_msg(user_id=int(q), message=message)

    if gid in admins:
        for q in admins[gid]:
            await bot.send_msg(
                message_type="private",
                user_id=q,
                group_id=int(gid),
                message=message,
            )


async def handle_group_request(bot: Bot, event: GroupRequestEvent, superusers: Iterable[str]) -> bool:
    """
    处理群请求
    :param bot: Bot 实例
    :param event: 事件对象
    :param superusers: 超管列表
    :return: bool
    """
    if event.sub_type != "add":
        return False

    gid = str(event.group_id)
    flag = event.flag
    uid = event.user_id
    word = _extract_request_answer(event.comment)

    blacklist_match = await _match_blacklist_term(gid, word)
    if blacklist_match:
        logger.info(REQUEST_BLACKLIST_HIT_LOG.format(word=word, matches=blacklist_match))
        await bot.set_group_add_request(
            flag=flag,
            sub_type=event.sub_type,
            approve=False,
            reason=REQUEST_DENY_REASON,
        )
        logger.info(format_request_rejected(uid, gid, word))
        logger.info(REQUEST_BLACKLIST_REASON_LOG)
        return True

    compared = await verify(word, gid)
    if compared is True:
        approve_message = format_request_approved(uid, gid, word)
        logger.info(approve_message)
        await bot.set_group_add_request(flag=flag, sub_type=event.sub_type, approve=True, reason=" ")
        await _notify_admins(bot, gid, approve_message, superusers)
        return True

    if compared is False:
        reject_message = format_request_rejected(uid, gid, word)
        logger.info(reject_message)
        await bot.set_group_add_request(
            flag=flag,
            sub_type=event.sub_type,
            approve=False,
            reason=REQUEST_DENY_REASON,
        )
        await _notify_admins(bot, gid, reject_message, superusers)
        return True

    logger.info(REQUEST_SKIP_LOG.format(gid=gid))
    return False


