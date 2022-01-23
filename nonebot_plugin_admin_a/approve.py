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

config_path = dirname(__file__) + "/config/"
config_json = config_path + "admin.json"
config_group = config_path + "group_admin.json"


async def load() -> Optional[dict]:
    """
    加载配置
    :return:dict
    """
    async with aiofiles.open(config_json, mode='r') as f:
        contents_ = await f.read()
        contents = json.loads(contents_)
        return contents


async def g_admin():
    """
    :return : 分群管理json对象
    """
    async with aiofiles.open(config_group, mode='r') as f:
        admins_ = await f.read()
        admins = json.loads(admins_)
    return admins


async def g_admin_add(gid: str, qq: int) -> Optional[bool]:
    """

    添加分群管理（处理加群请求时接收处理结果）
    :param gid: 群号
    :param qq: qq
    :return: bool
    """
    admins = await g_admin()
    if gid in admins:
        if qq in admins[gid]:
            logger.info(f'{qq}已经是群{gid}的分群管理了')
            return False
        else:
            g_admins = admins[gid]
            g_admins.append(qq)
            admins[gid] = g_admins
            async with aiofiles.open(config_group, mode='w') as c:
                await c.write(str(json.dumps(admins)))
            logger.info(f"群{gid}添加分群管理：{qq}")
            return True
    else:
        logger.info(f'群{gid}首次加入分群管理')
        admins.update({gid: [qq]})
        async with aiofiles.open(config_group, mode='w') as c:
            await c.write(str(json.dumps(admins)))
        return True


async def g_admin_del(gid: str, qq: int) -> Optional[bool]:
    """
    删除分群管理
    :param gid: 群号
    :param qq: qq
    :return: bool
    """
    admins = await g_admin()
    if gid in admins:
        if qq in admins[gid]:
            logger.info(f'已删除群{gid}的分群管理{qq}')
            data = admins[gid]
            data.remove(qq)
            if data:
                admins[gid] = data
            else:
                del (admins[gid])
            async with aiofiles.open(config_group, mode='w') as c:
                await c.write(str(json.dumps(admins)))
            return True
        else:
            logger.info(f'删除失败：群{gid}中{qq}还不是分群管理')
            return False
    else:
        logger.info(f'群{gid}还未添加过分群管理')
        return None


async def su_on_off() -> Optional[bool]:
    admins = await g_admin()
    if admins['su'] == 'False':
        admins['su'] = 'True'
        logger.info("打开超管消息接收")
        async with aiofiles.open(config_group, mode='w') as c:
            await c.write(str(json.dumps(admins)))
        return True
    else:
        admins['su'] = 'False'
        logger.info("关闭超管消息接收")
        async with aiofiles.open(config_group, mode='w') as c:
            await c.write(str(json.dumps(admins)))
        return False


async def write(gid: str, answer: str) -> Optional[bool]:
    """
    写入词条
    :param gid: 群号
    :param answer: 词条
    :return: bool
    """
    contents = await load()
    if gid in contents:
        data = contents[gid]
        if answer in data:
            logger.info(f'{answer} 已存在于群{gid}的词条中')
            return False
        else:
            data.append(answer)
            contents[gid] = data
            async with aiofiles.open(config_json, mode='w') as c:
                await c.write(str(json.dumps(contents)))
            logger.info(f"群{gid}添加入群审批词条：{answer}")
            return True

    else:
        logger.info(f'群{gid}第一次配置此词条：{answer}')
        contents.update({gid: [answer]})
        async with aiofiles.open(config_json, mode='w') as c:
            await c.write(str(json.dumps(contents)))
        return True


async def delete(gid: str, answer: str) -> Optional[bool]:
    """
    删除词条
    :param gid: 群号
    :param answer: 词条
    :return: bool
    """
    contents = await load()
    if gid in contents:
        if answer in contents[gid]:
            data = contents[gid]
            data.remove(answer)
            if data:
                contents[gid] = data
            else:
                del (contents[gid])
            async with aiofiles.open(config_json, mode='w') as c:
                await c.write(str(json.dumps(contents)))
            logger.info(f'群{gid}删除词条：{answer}')
            return True

        else:
            logger.info(f'删除失败，群{gid}不存在词条：{answer}')
            return False
    else:
        logger.info(f'群{gid}从未配置过词条')
        return None
