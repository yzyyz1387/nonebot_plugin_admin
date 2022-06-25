# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/6/25 18:26
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : wordcloud.py
# @Software: PyCharm
from nonebot import on_command, logger, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from .utils import init, replace_tmr, participle_simple_handle, check_func_status
from pathlib import Path
import os
from .path import *

cloud = on_command("群词云", priority=1)


@cloud.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    from wordcloud import WordCloud
    import jieba
    ttf_name_ = Path() / "resource" / "msyhblod.ttf"
    gid = str(event.group_id)
    path_temp = words_contents_path / f"{str(gid)}.txt"
    dir_list = os.listdir(words_contents_path)
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

