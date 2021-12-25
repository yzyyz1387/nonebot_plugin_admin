# python3
# -*- coding: utf-8 -*-
# @Time    : 2021/12/26 1:58
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : group_request_verify.py
# @Software: PyCharm
from nonebot import logger
from typing import Optional
from fuzzyfinder import fuzzyfinder
import json
import aiofiles
from os.path import dirname
config_path=dirname(__file__)+"/config/"
config_json=config_path+"admin.json"


async def verify(word:str,group_id:str) -> Optional[bool]:
    """
    验证答案，验证消息必须大于等于答案长度的1/2
    :param word: 用户答案
    :param group_id: 群号
    :return: bool
    """
    async with aiofiles.open(config_json, mode='r') as f:
        anwsers_ = await f.read()
        anwsers = json.loads(anwsers_)
    anwser=anwsers[group_id]
    suggestions = fuzzyfinder(word, anwser)
    result=list(suggestions)
    if result and len(word)>=len(result[0])/2:
        return True
    else:
        return False

