# python3
# -*- coding: utf-8 -*-
# @Time    : 2021/12/26 5:29
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : approve.py
# @Software: PyCharm
from typing import Optional
import aiofiles
from os.path import dirname
import json
from nonebot import logger
config_path=dirname(__file__)+"/config/"
config_json=config_path+"admin.json"

async def load()->Optional[dict]:
    """
    加载配置
    :return:dict
    """
    async with aiofiles.open(config_json, mode='r') as f:
        contents_ = await f.read()
        contents=json.loads(contents_)
        return contents


async def wirte(gid:str,anwser:str) -> Optional[bool]:
    """
    写入词条
    :param gid: 群号
    :param anwser: 词条
    :return: bool
    """
    contents=await load()
    if gid in contents:
        data = contents[gid]
        if anwser in data:
            logger.info(f'{anwser} 已存在于群{gid}的词条中')
            return False
        else:
            data.append(anwser)
            contents[gid] = data
            async with aiofiles.open(config_json, mode='w') as c:
                await c.write(str(json.dumps(contents)))
            logger.info(f"群{gid}添加入群审批词条：{anwser}")
            return True

    else:
        logger.info(f'群{gid}第一次配置此词条：{anwser}')
        contents.update({gid: [anwser]})
        async with aiofiles.open(config_json, mode='w') as c:
            await c.write(str(json.dumps(contents)))
        return True

async def delete(gid:str,anwser:str) -> Optional[bool]:
    """
    删除词条
    :param gid: 群号
    :param anwser: 词条
    :return: bool
    """
    contents = await load()
    if gid in contents:
        if anwser in contents[gid]:
            data = contents[gid]
            data.remove(anwser)
            contents[gid] = data
            async with aiofiles.open(config_json, mode='w') as c:
                await c.write(str(json.dumps(contents)))
            logger.info(f'群{gid}删除词条：{anwser}')
            return True

        else:
            logger.info(f'删除失败，群{gid}不存在词条：{anwser}')
            return False
    else:
        logger.info(f'群{gid}从未配置过词条')
        return None
