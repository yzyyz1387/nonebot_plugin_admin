# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/16 10:15
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : utils.py
# @Software: PyCharm
import json
import nonebot
import random
import os
import re
from os.path import dirname
from nonebot import logger
import httpx

config_path = dirname(__file__) + "/config/"
config_json = config_path + "admin.json"
config_group = config_path + "group_admin.json"
word_path = config_path + "word_config.txt"
words_path = dirname(__file__) + "/config/words/"
res_path = dirname(__file__) + "/resource/"
re_img_path = dirname(__file__) + "/resource/imgs"
ttf_name = dirname(__file__) + "/resource/msyhblod.ttf"


def At(data: str):
    """
    检测at了谁
    :param data: event.json
    :return: list
    """
    try:
        qq_list = []
        data = json.loads(data)
        for msg in data["message"]:
            if msg["type"] == "at":
                if 'all' not in str(msg):
                    qq_list.append(int(msg["data"]["qq"]))
                else:
                    return ['all']
        return qq_list
    except KeyError:
        return []


async def init():
    """
    初始化配置文件
    :return:
    """
    if not os.path.exists(config_path):
        os.mkdir(config_path)
        logger.info("创建 config 文件夹")
    if not os.path.exists(config_json):
        with open(config_json, 'w', encoding='utf-8') as c:
            c.write('{"1008611":["This_is_an_example"]}')
            c.close()
            logger.info("创建admin.json")
    if not os.path.exists(config_group):
        with open(config_group, 'w', encoding='utf-8') as c:
            c.write('{"su":"True"}')
            c.close()
            logger.info("创建group_admin.json")
    if not os.path.exists(word_path):
        with open(word_path, 'w', encoding='utf-8') as c:
            c.write('123456789\n')
            c.close()
            logger.info("创建word_config.txt")
    if not os.path.exists(words_path):
        os.mkdir(words_path)
        logger.info("创建/config/words/")
    if not os.path.exists(res_path):
        os.mkdir(res_path)
        logger.info("创建/resource")
    if not os.path.exists(re_img_path):
        os.mkdir(re_img_path)
        logger.info("创建/resource/imgs")
    if not os.path.exists(ttf_name):
        logger.info("下载资源字体")
        async with httpx.AsyncClient() as client:
            r = (await client.get(url="https://cdn.jsdelivr.net/gh/yzyyz1387/blogimages/msyhblod.ttf")).content
        with open(ttf_name, "wb") as tfn:
            tfn.write(r)
            tfn.close()
    logger.info("Admin 插件 初始化检测完成")


async def banSb(gid: int, ban_list: list, **time: int):
    """
    构造禁言
    :param gid: 群号
    :param time: 时间（s)
    :param ban_list: at列表
    :return:禁言操作
    """
    if 'all' in ban_list:
        yield nonebot.get_bot().set_group_whole_ban(
            group_id=gid,
            enable=True
        )
    else:
        if not time:
            time = random.randint(1, 2591999)
        else:
            time = time['time']
        for qq in ban_list:
            yield nonebot.get_bot().set_group_ban(
                group_id=gid,
                user_id=qq,
                duration=time,
            )


async def replace_tmr(msg: str) -> str:
    """

    :param msg: 消息字符串
    :return: 去除cq码、链接等的消息字符串
    """
    find_cq = re.compile(r"(\[CQ:.*])")
    find_link = re.compile("(https?://.*[^\u4e00-\u9fa5])")
    cq_code = re.findall(find_cq, msg)
    for cq in cq_code:
        msg = msg.replace(cq, "")
    links = re.findall(find_link, msg)
    for link in links:
        msg = msg.replace(link, "链接")
    return msg
