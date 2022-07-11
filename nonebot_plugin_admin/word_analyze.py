# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/16 22:21
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : word_analyze.py
# @Software: PyCharm
import datetime
import json
import os

import aiofiles
import httpx
from nonebot import on_command, logger, on_message
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .path import *
from .utils import init, replace_tmr, del_txt_line, add_txt_line, get_txt_line, upload, load, At, MsgText, error_log

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
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    """
    记录聊天内容
    :param bot:
    :param event:
    :return:
    """
    gid = str(event.group_id)
    uid = str(event.user_id)
    msg = str(MsgText(event.json())).replace(" ", "")
    path_temp = words_contents_path / f"{str(gid)}.txt"
    message_path_group = group_message_data_path / f"{gid}"
    # datetime获取今日日期
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    this_time = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    try:
        if not os.path.exists(word_path) or not os.path.exists(group_message_data_path):
            await init()
        if not os.path.exists(message_path_group):
            os.mkdir(message_path_group)
        if not os.path.exists(message_path_group / "sum.json"):  # 总记录 {日期：{时间：[uid, 消息]}}
            await upload(message_path_group / "sum.json", {today: {this_time: [uid, event.raw_message]}})
        else:
            dic_ = await load(message_path_group / "sum.json")
            if today not in dic_:
                dic_[today] = {this_time: [uid, event.raw_message]}
            else:
                dic_[today][this_time] = [uid, event.raw_message]
            await upload(message_path_group / "sum.json", dic_)
        if not os.path.exists(message_path_group / f"{today}.json"):  # 日消息条数记录 {uid：消息数}
            await upload(message_path_group / f"{today}.json", {uid: 1})
        else:
            dic_ = await load(message_path_group / f"{today}.json")
            if uid not in dic_:
                dic_[uid] = 1
            else:
                dic_[uid] += 1
            await upload(message_path_group / f"{today}.json", dic_)
        if not os.path.exists(message_path_group / "history.json"):  # 历史发言条数记录 {uid：消息数}
            await upload(message_path_group / "history.json", {uid: 1})
        else:
            dic_ = await load(message_path_group / "history.json")
            if uid not in dic_:
                dic_[uid] = 1
            else:
                dic_[uid] += 1
            await upload(message_path_group / "history.json", dic_)
        txt = open(word_path, "r", encoding="utf-8").read().split("\n")
        if gid in txt:
            msg = await replace_tmr(msg)
            with open(path_temp, "a+", encoding="utf-8") as c:
                c.write(msg + "\n")
    except Exception as e:
        logger.error("word_analyze.py 消息记录发生错误：" + str(e))
        await error_log(event.group_id, this_time, matcher, str(e))


stop_words_add = on_command("添加停用词", aliases={'增加停用词', '新增停用词'}, block=True, priority=1,
                            permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@stop_words_add.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    """
    添加停用词
    """
    await add_txt_line(stop_words_path, matcher, event, args, "停用词")


stop_words_del = on_command("删除停用词", aliases={'移除停用词', '去除停用词'}, block=True, priority=1,
                            permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@stop_words_del.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    """
    删除停用词
    """
    await del_txt_line(stop_words_path, matcher, event, args, "停用词")


stop_words_list = on_command("停用词列表", aliases={'查看停用词', '查询停用词'}, block=True, priority=1,
                             permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@stop_words_list.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    """
    停用词列表
    """
    await get_txt_line(stop_words_path, matcher, event, args, "停用词")


update_mask = on_command("更新mask", aliases={'下载mask'}, block=True, priority=1,
                         permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


@update_mask.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    更新mask
    """
    already_have = len(os.listdir(wordcloud_bg_path))
    try:
        async with httpx.AsyncClient() as client:
            num_in_cloud = int((await client.get(
                "https://fastly.jsdelivr.net/gh/yzyyz1387/blogimages/nonebot/wordcloud/num.txt")).read())
            if num_in_cloud > already_have:
                await update_mask.send("正zhai更新中...")
                for i in range(already_have, num_in_cloud):
                    img_content = (await client.get(
                        f"https://fastly.jsdelivr.net/gh/yzyyz1387/blogimages/nonebot/wordcloud/bg{i}.png")).content
                    with open(wordcloud_bg_path / f"{i}.png", "wb") as f:
                        f.write(img_content)
                await update_mask.send("更新完成（好耶）")
            elif num_in_cloud == already_have:
                await update_mask.send("蚌！已经是最新了耶")
    except Exception as e:
        logger.info(e)
        await update_mask.send(f"QAQ,更新mask失败:\n{e}")
        return


# FIXME: 这一块重复代码有点多了
who_speak_most_today = on_command("今日榜首", aliases={'今天谁话多', '今儿谁话多', '今天谁屁话最多'}, block=True, priority=1)


@who_speak_most_today.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    gid = event.group_id
    today = datetime.date.today().strftime("%Y-%m-%d")
    dic_ = await load(group_message_data_path / f"{gid}" / f"{today}.json")
    top = sorted(dic_.items(), key=lambda x: x[1], reverse=True)
    if len(top) == 0:
        await who_speak_most_today.send("没有任何人说话")
        return
    else:
        await who_speak_most_today.send(f"太强了！今日榜首：\n{top[0][0]}，发了{top[0][1]}条消息")


speak_top = on_command("今日发言排行", aliases={'今日排行榜', '今日发言排行榜', '今日排行'}, block=True, priority=1)


@speak_top.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    gid = event.group_id
    today = datetime.date.today().strftime("%Y-%m-%d")
    dic_ = await load(group_message_data_path / f"{gid}" / f"{today}.json")
    top = sorted(dic_.items(), key=lambda x: x[1], reverse=True)
    if len(top) == 0:
        await speak_top.send("没有任何人说话")
        return
    top_list = []
    for i in range(min(len(top), 10)):
        top_list.append(f"{i + 1}. {top[i][0]}，发了{top[i][1]}条消息")
    await speak_top.send("\n".join(top_list))


speak_top_yesterday = on_command("昨日发言排行", aliases={'昨日排行榜', '昨日发言排行榜', '昨日排行'}, block=True, priority=1)


@speak_top_yesterday.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    gid = event.group_id
    today = datetime.date.today().strftime("%Y-%m-%d")
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    if os.path.exists(group_message_data_path / f"{gid}" / f"{yesterday}.json"):
        dic_ = await load(group_message_data_path / f"{gid}" / f"{yesterday}.json")
        top = sorted(dic_.items(), key=lambda x: x[1], reverse=True)
        if len(top) == 0:
            await speak_top_yesterday.send("没有任何人说话")
            return
        top_list = []
        for i in range(min(len(top), 10)):
            top_list.append(f"{i + 1}. {top[i][0]}，发了{top[i][1]}条消息")
        await speak_top_yesterday.send("\n".join(top_list))
    else:
        await speak_top_yesterday.send("昨日没有记录")


who_speak_most = on_command("排行", aliases={'谁话多', '谁屁话最多', '排行', '排行榜'}, block=True, priority=1)


@who_speak_most.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    gid = event.group_id
    dic_ = await load(group_message_data_path / f"{gid}" / "history.json")
    top = sorted(dic_.items(), key=lambda x: x[1], reverse=True)
    if len(top) == 0:
        await who_speak_most.send("没有任何人说话")
        return
    else:
        top_list = []
        for i in range(min(len(top), 10)):
            top_list.append(f"{i + 1}. {top[i][0]}，发了{top[i][1]}条消息")
        await who_speak_most.send("\n".join(top_list))


get_speak_num = on_command("发言数", aliases={'发言数', '发言', '发言量'}, block=True, priority=1)


@get_speak_num.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    gid = event.group_id
    dic_ = await load(group_message_data_path / f"{gid}" / "history.json")
    at_list = At(event.json())
    if at_list:
        for qq in at_list:
            qq = str(qq)
            if qq in dic_:
                await get_speak_num.send(f"有记录以来{qq}在本群发了{dic_[qq]}条消息")
            else:
                await get_speak_num.send(f"{qq}没有发消息")


get_speak_num_today = on_command("今日发言数", aliases={'今日发言数', '今日发言', '今日发言量'}, block=True, priority=1)


@get_speak_num_today.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    gid = event.group_id
    today = datetime.date.today().strftime("%Y-%m-%d")
    dic_ = await load(group_message_data_path / f"{gid}" / f"{today}.json")
    at_list = At(event.json())
    if at_list:
        for qq in at_list:
            qq = str(qq)
            if qq in dic_:
                await get_speak_num_today.send(f"今天{qq}发了{dic_[qq]}条消息")
            else:
                await get_speak_num_today.send(f"今天{qq}没有发消息")
