# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/16 22:21
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : word_analyze.py
# @Software: PyCharm
from nonebot import on_command, logger, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from .utils import init, replace_tmr, participle_simple_handle, check_func_status
from pathlib import Path
import os
from .path import *


word_start = on_command("记录本群", block=True, priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@word_start.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    status = await check_func_status("wordcloud", gid)
    if status:
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
    else:
        await word_start.finish("请先发送【开关群词云】开启此功能")


word_stop = on_command("停止记录本群", block=True, priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@word_stop.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    status = await check_func_status("wordcloud", gid)
    if status:
        if not os.path.exists(word_path):
            await init()
        txt = open(word_path, 'r', encoding='utf-8').read()
        if gid in txt:
            with open(word_path,'w',encoding='utf-8') as c:
                c.write(txt.replace(gid,""))
                c.close()
                logger.info(f"停止记录{gid}")
                await word_start.finish("成功，曾经的记录不会被删除")
        else:
            logger.info(f"停用失败：{gid}不存在")
            await word_start.finish(f"停用失败：{gid}不存在")
    else:
        await word_start.finish("请先发送【开关群词云】开启此功能")

word = on_message(priority=10, block=False)


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
    path_temp = words_contents_path / f"{str(gid)}.txt"
    if not os.path.exists(word_path):
        await init()
    txt = open(word_path, "r", encoding="utf-8").read().split("\n")
    if gid in txt:
        msg = await replace_tmr(msg)
        with open(path_temp, "a+") as c:
            c.write(msg + "\n")


cloud = on_command("群词云", priority=1)


@cloud.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    from wordcloud import WordCloud
    import jieba
    ttf_name_ = Path() / "resource" / "msyhblod.ttf"
    gid = str(event.group_id)
    path_temp = words_contents_path / f"{str(gid)}.txt"
    dir_list = os.listdir(words_contents_path)
    status = await check_func_status("wordcloud", gid)
    if status:
        if gid + ".txt" in dir_list:
            text = open(path_temp).read()
            txt = jieba.lcut(text)
            stop_ = await participle_simple_handle()
            string = " ".join(txt)
            try:
                wc = WordCloud(font_path=str(ttf_name_.resolve()), width=800, height=600, mode='RGBA',
                               background_color="#ffffff", stopwords=stop_).generate(string)
                img = Path(re_img_path / f"{gid}.png")
                wc.to_file(img)
                await cloud.send(MessageSegment.image(img))
            except Exception as err:
                await cloud.send(f"出现错误{type(err)}:{err}")
    else:
        await cloud.send("请先发送【开关群词云】开启此功能")
