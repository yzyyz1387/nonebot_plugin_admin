# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/16 10:15
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : utils.py
# @Software: PyCharm
import os
import re
import json
import httpx
import random
import base64
import nonebot
from pathlib import Path
from nonebot import logger
from typing import Optional

config_path = Path() / "config"
config_json = config_path / "admin.json"
config_group = config_path / "group_admin.json"
word_path = config_path / "word_config.txt"
words_path = Path() / "config" / "words"
res_path = Path() / "resource"
re_img_path = Path() / "resource" / "imgs"
ttf_name = Path() / "resource" / "msyhblod.ttf"
limit_word_path = config_path / "违禁词.txt"


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
    if not os.path.exists(limit_word_path):
        logger.info("下载违禁词库")
        async with httpx.AsyncClient() as client:
            r = (await client.get(url="https://cdn.jsdelivr.net/gh/yzyyz1387/nwafu/f_words/f_word")).text
        with open(limit_word_path, "w",encoding='utf-8') as lwp:
            lwp.write(r)
            lwp.close()
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
    原始消息简单处理
    :param msg: 消息字符串
    :return: 去除cq码,链接等
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


async def participle_simple_handle() -> set:
    """
    wordcloud停用词
    """
    prep_ = ['么', '了', '与', '不', '且', '之', '为', '兮', '其', '到', '云', '阿', '却', '个',
             '以', '们', '价', '似', '讫', '诸', '取', '若', '得', '逝', '将', '夫', '头', '只',
             '吗', '向', '吧', '呗', '呃', '呀', '员', '呵', '呢', '哇', '咦', '哟', '哉', '啊',
             '哩', '啵', '唻', '啰', '唯', '嘛', '噬', '嚜', '家', '如', '掉', '给', '维', '圪',
             '在', '尔', '惟', '子', '赊', '焉', '然', '旃', '所', '见', '斯', '者', '来', '欤',
             '是', '毋', '曰', '的', '每', '看', '着', '矣', '罢', '而', '耶', '粤', '聿', '等',
             '言', '越', '馨', '趴', '从', '自从', '自', '打', '到', '往', '在', '由', '向', '于',
             '至', '趁', '当', '当着', '沿着', '顺着', '按', '按照', '遵照', '依照', '靠', '本着',
             '用', '通过', '根据', '据', '拿', '比', '因', '因为', '由于', '为', '为了', '为着',
             '被', '给', '让', '叫', '归', '由', '把', '将', '管', '对', '对于', '关于', '跟', '和', '给', '替', '向', '同', '除了']

    pron_ = ["各个", "本人", "这个", "各自", "哪些", "怎的", "我", "大家", "她们", "多少", "怎么", "那么", "那样", "怎样", "几时", "哪儿", "我们", "自我",
             "什么", "哪个", "那个", "另外", "自己", "哪样", "这儿", "那些", "这样", "那儿", "它们", "它", "他", "你", "谁", "今", "吗", "是", "乌",
             "如何", "彼此", "其次", "列位", "该", "各", "然", "安", "之", "怎", "夫", "其", "每", "您", "伊", "此", "者", "咱们", "某", "诸位",
             "这些", "予", "任何", "若", "彼", "恁", "焉", "兹", "俺", "汝", "几许", "多咱", "谁谁", "有些", "干吗", "何如", "怎么样", "好多", "哪门子",
             "这程子", "他人", "奈何", "人家", "若干", "本身", "旁人", "其他", "其余", "一切", "如此", "谁人", "怎么着", "那会儿", "自家", "哪会儿", "谁边",
             "这会儿", "几儿", "这么些", "那阵儿", "那么点儿", "这么点儿", "这么样", "这阵儿", "一应", "多会儿", "何许", "若何", "大伙儿", "几多", "恁地", "谁个",
             "乃尔", "那程子", "多早晚", "如许", "倷", "孰", "侬", "怹", "朕", "他们", "这么着", "那么些", "咱家", "你们", "那么着"]

    others_ = ['就', '这', '那', '都', '也', '还', '又', '有', '没', '好', '我', '我的', '说', '去', '点', '不是', '就是', '要', '一个', '现在',
               '啥']

    sum_ = set(prep_ + pron_ + others_)
    return sum_


async def pic_cof(data: str, **kwargs) -> Optional[json]:
    try:
        if kwargs['mode'] == 'url':
            async with httpx.AsyncClient() as client:
                data_ = str(base64.b64encode((await client.get(url=data)).content),encoding='utf-8')
            json_ = {"data": [f"data:image/png;base64,{data_}"]}
        else:
            json_ = {"data": [f"data:image/png;base64,{data}"]}
    except Exception as err:
        json_ = {"data": ["data:image/png;base64,"]}
        print(err)
    try:
        async with httpx.AsyncClient() as client:
            r = (await client.post(
                url='https://hf.space/gradioiframe/mayhug/rainchan-image-porn-detection/+/api/predict/',
                json=json_)).json()
        if 'error' in r:
            return None
        else:
            return r
    except Exception as err:
        logger.debug(f'于"utils.py"中的 pic_cof 发生错误：{err}')
        return None


async def pic_ban_cof(**data) -> Optional[bool]:
    global result
    if data:
        if 'url' in data:
            result = await pic_cof(data=data['url'], mode='url')
        if 'base64' in data:
            result = await pic_cof(data=data['data'], mode='default')
        if result:
            if result['data'][0]['label'] != 'safe':
                return True
            else:
                return False
        else:
            return None

