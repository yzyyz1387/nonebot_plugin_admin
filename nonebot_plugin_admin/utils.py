# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/16 10:15
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : utils.py
# @Software: PyCharm
import asyncio
import base64
import json
import os
import random
import re
from typing import Union, Optional
import aiofiles
import httpx
import nonebot
from nonebot import logger, require
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ims.v20201229 import ims_client, models
from .path import *

TencentID = nonebot.get_driver().config.tenid
TencentKeys = nonebot.get_driver().config.tenkeys
su = nonebot.get_driver().config.superusers


def At(data: str):
    """
    检测at了谁，返回[qq, qq, qq,...]
    包含全体成员直接返回['all']
    如果没有at任何人，返回[]
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
        await mk("dir", config_path, mode=None, )
    if not os.path.exists(template_path):
        await mk("dir", template_path, mode=None, )
    if not os.path.exists(config_admin):
        await mk("file", config_admin, "w", content='{"1008611":["This_is_an_example"]}')
    if not os.path.exists(config_group_admin):
        await mk("file", config_group_admin, "w", content='{"su":"True"}')
    if not os.path.exists(word_path):
        await mk("file", word_path, "w", content='123456789\n')
    if not os.path.exists(words_contents_path):
        await mk("dir", words_contents_path, mode=None)
    if not os.path.exists(res_path):
        await mk("dir", res_path, mode=None)
    if not os.path.exists(re_img_path):
        await mk("dir", re_img_path, mode=None)
    if not os.path.exists(ttf_name):
        await mk("file", ttf_name, "wb", url="https://cdn.jsdelivr.net/gh/yzyyz1387/blogimages/msyhblod.ttf",
                 dec="资源字体")
    if not os.path.exists(limit_word_path):
        await mk("file", limit_word_path, "w", url="https://cdn.jsdelivr.net/gh/yzyyz1387/nwafu/f_words/f_word_s",
                 dec="严格违禁词词库")
    if not os.path.exists(limit_word_path_easy):
        await mk("file", limit_word_path_easy, "w",
                 url="https://cdn.jsdelivr.net/gh/yzyyz1387/nwafu/f_words/f_word_easy",
                 dec="简单违禁词词库")
    if not os.path.exists(limit_level):
        bot = nonebot.get_bot()
        logger.info("创建违禁词监控等级配置文件,分群设置,默认easy")
        g_list = (await bot.get_group_list())
        level_dict = {}
        for group in g_list:
            level_dict.update({str(group['group_id']): "easy"})
        with open(limit_level, "w", encoding='utf-8') as lwp:
            lwp.write(f'{json.dumps(level_dict)}')
            lwp.close()
    if not os.path.exists(switcher_path):
        bot = nonebot.get_bot()
        logger.info("创建开关配置文件,分群设置,默认开")
        g_list = (await bot.get_group_list())
        switcher_dict = {}
        for group in g_list:
            switcher_dict.update({str(group['group_id']): {"admin": True, "requests": True, "wordcloud": True,
                                                           "auto_ban": True, "img_check": True}})
        with open(switcher_path, "w", encoding='utf-8') as swp:
            swp.write(f'{json.dumps(switcher_dict)}')
            swp.close()
    logger.info("Admin 插件 初始化检测完成")


async def mk(type_, path_, *mode, **kwargs):
    """
    创建文件夹 下载文件
    :param type_: ['dir', 'file']
    :param path_: Path
    :param mode: ['wb', 'w']
    :param kwargs: ['url', 'content', 'dec', 'info'] 文件地址 写入内容 描述信息 和 额外信息
    :return: None
    """
    if 'info' in kwargs:
        logger.info(kwargs['info'])
    if type_ == "dir":
        os.mkdir(path_)
        logger.info(f"创建文件夹{path_}")
    elif type_ == "file":
        if 'url' in kwargs:
            if kwargs['dec']:
                logger.info(f"开始下载文件{kwargs['dec']}")
            async with httpx.AsyncClient() as client:
                r = await client.get(kwargs['url'])
                if mode[0] == "w":
                    with open(path_, "w", encoding='utf-8') as f:
                        f.write(r.text)
                elif mode[0] == "wb":
                    with open(path_, "wb") as f:
                        f.write(r.content)
                logger.info(f"下载文件 {kwargs['dec']} 到 {path_}")
        else:
            if mode:
                with open(path_, mode[0]) as f:
                    f.write(kwargs["content"])
                logger.info(f"创建文件{path_}")
            else:
                raise Exception("mode 不能为空")
    else:
        raise Exception("type_参数错误")


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
            if int(qq) in su or str(qq) in su:
                logger.info(f"SUPERUSER无法被禁言")
            else:
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


# async def pic_cof(data: str, **kwargs) -> Optional[dict]:
#     try:
#         if kwargs['mode'] == 'url':
#             async with httpx.AsyncClient() as client:
#                 data_ = str(base64.b64encode((await client.get(url=data)).content), encoding='utf-8')
#             json_ = {"data": [f"data:image/png;base64,{data_}"]}
#         else:
#             json_ = {"data": [f"data:image/png;base64,{data}"]}
#     except Exception as err:
#         json_ = {"data": ["data:image/png;base64,"]}
#         print(err)
#     try:
#         async with httpx.AsyncClient() as client:
#             r = (await client.post(
#                 url='https://hf.space/gradioiframe/mayhug/rainchan-image-porn-detection/+/api/predict/',
#                 json=json_)).json()
#         if 'error' in r:
#             return None
#         else:
#             return r
#     except Exception as err:
#         logger.debug(f'于"utils.py"中的 pic_cof 发生错误：{err}')
#         return None
#
#
# async def pic_ban_cof(**data) -> Optional[bool]:
#     global result
#     if data:
#         if 'url' in data:
#             result = await pic_cof(data=data['url'], mode='url')
#         if 'base64' in data:
#             result = await pic_cof(data=data['data'], mode='default')
#         if result:
#             if result['data'][0]['label'] != 'safe':
#                 return True
#             else:
#                 return False
#         else:
#             return None


# TENCENT 图片检测 @A60 https://github.com/djkcyl/ABot-Graia
def image_moderation(img):
    try:
        cred = credential.Credential(
            TencentID,
            TencentKeys,
        )
        httpProfile = HttpProfile()
        httpProfile.endpoint = "ims.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = ims_client.ImsClient(cred, "ap-shanghai", clientProfile)

        req = models.ImageModerationRequest()
        params = (
            {"BizType": "group_recall", "FileUrl": img}
            if type(img) == str
            else {"BizType": "group_recall", "FileContent": bytes_to_base64(img)}
        )
        req.from_json_string(json.dumps(params))

        resp = client.ImageModeration(req)
        return json.loads(resp.to_json_string())

    except TencentCloudSDKException as err:
        return err
    except KeyError as kerr:
        return kerr


async def image_moderation_async(img: Union[str, bytes]) -> dict:
    try:
        resp = await asyncio.to_thread(image_moderation, img)
        if resp["Suggestion"] != "Pass":
            return {"status": False, "message": resp["Label"]}
        else:
            return {"status": True, "message": None}
    except Exception as e:
        return {"status": "error", "message": e}


def bytes_to_base64(data):
    return base64.b64encode(data).decode("utf-8")


async def auto_upload_f_words():
    logger.info("自动更新严格违禁词库...")
    async with httpx.AsyncClient() as client:
        try:
            r = (await client.get(url="https://cdn.jsdelivr.net/gh/yzyyz1387/nwafu/f_words/f_word_s")).text
        except Exception as err:
            logger.error(f"自动更新严格违禁词库失败：{err}")
            return True
    with open(limit_word_path, "w", encoding='utf-8') as lwp:
        lwp.write(r)
        lwp.close()
    logger.info("正在更新简单违禁词库")
    async with httpx.AsyncClient() as client:
        try:
            r = (await client.get(url="https://cdn.jsdelivr.net/gh/yzyyz1387/nwafu/f_words/f_word_easy")).text
        except Exception as err:
            logger.error(f"自动更新简单违禁词库失败：{err}")
            return True
    with open(limit_word_path_easy, "w", encoding='utf-8') as lwp:
        lwp.write(r)
        lwp.close()
    logger.info("更新完成")

scheduler = require("nonebot_plugin_apscheduler").scheduler
# 每周一更新违禁词库
scheduler.add_job(auto_upload_f_words, 'cron', day_of_week='mon', hour=0, minute=0, second=0, id='auto_upload_f_words')


async def load(path) -> Optional[dict]:
    """
    加载json文件
    :return: Optional[dict]
    """
    try:
        async with aiofiles.open(path, mode='r', encoding="utf-8") as f:
            contents_ = await f.read()
            contents = json.loads(contents_)
            await f.close()
            return contents
    except FileNotFoundError:
        return None


async def upload(path, dict_content) -> None:
    """
    更新json文件
    :param path: 路径
    :param dict_content: python对象，字典
    """
    async with aiofiles.open(path, mode='w', encoding="utf-8") as c:
        await c.write(str(json.dumps(dict_content)))
        await c.close()


async def check_func_status(func_name: str, gid: str) -> bool:
    """
    检查某个群的某个功能是否开启
    :param func_name: 功能名
    :param gid: 群号
    :return: bool
    """
    funcs_status = (await load(switcher_path))
    if funcs_status[gid][func_name]:
        return True
    else:
        return False
