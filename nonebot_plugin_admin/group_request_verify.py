# python3
# -*- coding: utf-8 -*-
# @Time    : 2021/12/26 1:58
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : group_request_verify.py
# @Software: PyCharm
import json
from typing import Optional

from fuzzyfinder import fuzzyfinder
from nonebot import logger

from .path import *


async def verify(word: str, group_id: str) -> Optional[bool]:
    """
    验证答案，验证消息必须大于等于答案长度的1/2
    :param word: 用户答案
    :param group_id: 群号
    :return: bool
    """
    with open(config_admin, mode='r') as f:
        answers = json.load(f)
        if group_id in answers:
            answer = answers[group_id]
            suggestions = fuzzyfinder(word, answer)
            result = list(suggestions)
            return result and len(word) >= len(result[0]) / 2
    logger.info(f"群{group_id}从未配置审批词条，不进行操作")
    return None
