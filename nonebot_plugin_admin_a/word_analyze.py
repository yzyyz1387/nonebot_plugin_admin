# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/16 10:36
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : word_analyze.py
# @Software: PyCharm

from nonebot import on_command, logger, on_message
from nonebot.adapters.cqhttp import Bot, GroupMessageEvent, MessageSegment
from nonebot.adapters.cqhttp.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from .utils import init, replace_tmr
import os
from pathlib import Path

config_path = Path() / "config"
word_path = config_path / "word_config.txt"
words_path = Path() / "config" / "words"
img_path = Path() / "resource" / "imgs"
word_start = on_command("记录本群", block=True, priority=2, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@word_start.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    if not os.path.exists(word_path):
        await init()
    with open(word_path, 'r+', encoding='utf-8') as c:
        txt = c.read().split("\n")
        if gid not in txt:
            c.write(gid + "\n")
            c.close()
            logger.info(f"开始记录{gid}")
            await word_start.finish("成功")
        else:
            logger.info(f"{gid}已存在")
            await word_start.finish(f"{gid}已存在")


word = on_message(priority=10)


@word.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    记录聊天内容
    :param bot:
    :param event:
    :return:
    """
    gid = str(event.group_id)
    msg = str(event.get_message()).replace(" ", "")
    path_temp = config_path / f"{str(gid)}.txt"
    txt = open(word_path, "r", encoding="utf-8").read().split("\n")
    if gid in txt:
        msg = await replace_tmr(msg)
        with open(path_temp, "a+") as c:
            c.write(msg + "\n")


cloud = on_command("群词云", priority=3)


@cloud.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    from wordcloud import WordCloud
    import jieba
    ttf_name = Path() / "resource" / "msyhblod.ttf"
    gid = str(event.group_id)
    path_temp = words_path / f"{str(gid)}.txt"
    dir_list = os.listdir(words_path)
    if gid + ".txt" in dir_list:
        text = open(path_temp).read()
        txt = jieba.lcut(text)
        string = " ".join(txt)
        try:
            wc = WordCloud(font_path=str(ttf_name.resolve()), width=800, height=600, mode='RGBA',
                           background_color="#ffffff").generate(
                string)
            img = Path(img_path / f"{gid}.png")
            wc.to_file(img)
            await cloud.send(MessageSegment.image(img))
        except Exception as err:
            await cloud.send(f"出现错误{type(err)}:{err}")
