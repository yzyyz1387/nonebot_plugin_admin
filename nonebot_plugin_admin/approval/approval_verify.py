# python3
# -*- coding: utf-8 -*-

from typing import Optional

from fuzzyfinder import fuzzyfinder
from nonebot import logger

from ..statistics.config_orm_store import orm_load_approval_terms


async def verify(word: str, group_id: str) -> Optional[bool]:
    """
    处理 verify 的业务逻辑
    :param word: word 参数
    :param group_id: 群号
    :return: Optional[bool]
    """
    answers = await orm_load_approval_terms() or {}
    if group_id not in answers:
        logger.info(f"群 {group_id} 从未配置审批词条，不进行操作")
        return None
    answer = answers[group_id]

    suggestions = fuzzyfinder(word, answer)
    result = list(suggestions)
    return result and len(word) >= len(result[0]) / 2
