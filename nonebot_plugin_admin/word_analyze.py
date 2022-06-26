# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/16 22:21
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : word_analyze.py
# @Software: PyCharm
from nonebot import on_command, logger, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment, ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from .utils import init, replace_tmr, participle_simple_handle, check_func_status
from pathlib import Path
import os
from .path import *
from nonebot.adapters import Message
from nonebot.params import CommandArg

word_start = on_command("记录本群", block=True, priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


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


word_stop = on_command("停止记录本群", block=True, priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@word_stop.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    if not os.path.exists(word_path):
        await init()
    txt = open(word_path, 'r', encoding='utf-8').read()
    if gid in txt:
        with open(word_path, 'w', encoding='utf-8') as c:
            c.write(txt.replace(gid, ""))
            c.close()
            logger.info(f"停止记录{gid}")
            await word_start.finish("成功，曾经的记录不会被删除")
    else:
        logger.info(f"停用失败：{gid}不存在")
        await word_start.finish(f"停用失败：{gid}不存在")


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
        with open(path_temp, "a+", encoding="utf-8") as c:
            c.write(msg + "\n")


stop_words_add = on_command("添加停用词", aliases={'增加停用词', '新增停用词'}, block=True, priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@stop_words_add.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """
    添加停用词
    """
    gid = str(event.group_id)
    logger.info(args)
    if args:
        msg = str(args).split(" ")
        logger.info(msg)
        this_stop_words_path = stop_words_path / f"{str(gid)}.txt"
        if not os.path.exists(this_stop_words_path):
            await init()
        try:
            with open(this_stop_words_path, "r+", encoding="utf-8") as c:
                is_saved = c.read().split("\n")
                success_add = []
                already_add = []
                for words in msg:
                    if words in is_saved:
                        logger.info(f"{words}已存在")
                        already_add.append(words)
                    else:
                        c.write(words + "\n")
                        logger.info(f"添加{words}成功")
                        success_add.append(words)
                if already_add:
                    await stop_words_add.send(f"{str(already_add)}已存在")
                if success_add:
                    await stop_words_add.send(f"{str(success_add)}添加成功")
        except FileNotFoundError:
            success_add = []
            with open(this_stop_words_path, "w", encoding="utf-8") as c:
                for words in msg:
                    c.write(words + "\n")
                    logger.info(f"添加{words}成功")
                    success_add.append(words)
                await stop_words_add.send(f"添加{str(success_add)}成功")
                c.close()
    else:
        await stop_words_add.send("请输入停用词,多个以空格分隔，例：\n添加停用词 停用词1 停用词2")


stop_words_del = on_command("删除停用词", aliases={'移除停用词', '去除停用词'}, block=True, priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@stop_words_del.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """
    删除停用词
    """
    gid = str(event.group_id)
    logger.info(args)
    if args:
        msg = str(args).split(" ")
        logger.info(msg)
        this_stop_words_path = stop_words_path / f"{str(gid)}.txt"
        if not os.path.exists(this_stop_words_path):
            await init()
        try:
            with open(this_stop_words_path, "r+", encoding="utf-8") as c:
                is_saved = c.read().split("\n")
                c.close()
            with open(this_stop_words_path, "w", encoding="utf-8") as c:
                success_del = []
                already_del = []
                for words in msg:
                    if words not in is_saved:
                        already_del.append(words)
                    for i in is_saved:
                        if words == i:
                            is_saved.remove(i)
                            logger.info(f"删除{words}成功")
                            success_del.append(words)
                c.write("\n".join(is_saved))
                if success_del:
                    await stop_words_del.send(f"{str(success_del)}删除成功")
                if already_del:
                    await stop_words_del.send(f"{str(already_del)}还不是停用词")
        except FileNotFoundError:
            await stop_words_del.send("该群没有停用词")
    else:
        await stop_words_del.send("请输入停用词,多个以空格分隔，例：\n删除停用词 停用词1 停用词2")


stop_words_list = on_command("停用词列表", aliases={'查看停用词', '查询停用词'}, block=True, priority=1, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@stop_words_list.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    停用词列表
    """
    gid = str(event.group_id)
    this_stop_words_path = stop_words_path / f"{str(gid)}.txt"
    if not os.path.exists(this_stop_words_path):
        await init()
    try:
        with open(this_stop_words_path, "r", encoding="utf-8") as c:
            is_saved = c.read().split("\n")
            is_saved.remove("")
            c.close()
        await stop_words_list.send(f"{str(is_saved)}")
    except ActionFailed:
        logger.info("用户正在查看停用此列表，可能是停用词太多了，无法发送")
        await stop_words_list.send("可能是停用词太多了，无法发送")
    except FileNotFoundError:
        await stop_words_list.send("该群没有停用词")