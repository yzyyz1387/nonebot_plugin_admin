# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/16 10:15
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : utils.py
# @Software: PyCharm
import asyncio
import base64
import datetime
import json
import os
import random
import re
from typing import Union, Optional

import httpx
import nonebot
from nonebot import logger
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, ActionFailed, Bot
from nonebot.matcher import Matcher
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ims.v20201229 import ims_client, models

from .config import plugin_config, global_config
from .path import *

TencentID = plugin_config.tenid
TencentKeys = plugin_config.tenkeys
su = global_config.superusers
cb_notice = plugin_config.callback_notice


def At(data: str) -> Union[list[str], list[int], list]:
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
        for msg in data['message']:
            if msg['type'] == 'at':
                if 'all' not in str(msg):
                    qq_list.append(int(msg['data']['qq']))
                else:
                    return ['all']
        return qq_list
    except KeyError:
        return []


def Reply(data: str):
    """
    检测回复哪条消息，返回 reply 对象
    如果没有回复任何人，返回 None
    :param data: event.json()
    :return: dict | None
    """
    try:
        data = json.loads(data)
        if data['reply'] and data['reply']['message_id']:  # 待优化
            return data['reply']
        else:
            return None
    except KeyError:
        return None


def MsgText(data: str):
    """
    返回消息文本段内容(即去除 cq 码后的内容)
    :param data: event.json()
    :return: str
    """
    try:
        data = json.loads(data)
        # 过滤出类型为 text 的【并且过滤内容为空的】
        msg_text_list = filter(lambda x: x['type'] == 'text' and x['data']['text'].replace(' ', '') != '',
                               data['message'])
        # 拼接成字符串并且去除两端空格
        msg_text = ' '.join(map(lambda x: x['data']['text'].strip(), msg_text_list)).strip()
        return msg_text
    except:
        return ''


dirs = [config_path,
        template_path,
        words_contents_path,
        res_path,
        re_img_path,
        stop_words_path,
        wordcloud_bg_path,
        user_violation_info_path,
        group_message_data_path,
        error_path,
        kick_lock_path]


async def init():
    """
    初始化配置文件
    :return:
    """
    for d in dirs:
        if not d.exists():
            await mk('dir', d, mode=None)
    if not config_admin.exists():
        await mk('file', config_admin, 'w', content='{"1008611": ["This_is_an_example"]}')
    if not config_group_admin.exists():
        await mk('file', config_group_admin, 'w', content='{"su": "True"}')
    if not word_path.exists():
        await mk('file', word_path, 'w', content='123456789\n')
    if not switcher_path.exists():
        bots = nonebot.get_bots()
        for bot in bots.values():
            logger.info('创建开关配置文件,分群设置, 图片检测和违禁词检测,防撤回，广播，早晚安默认关,其他默认开')
            g_list = (await bot.get_group_list())
            switcher_dict = {}
            for group in g_list:
                switchers = {}
                for fn_name in admin_funcs:
                    switchers.update({fn_name: True})
                    if fn_name in ['img_check', 'auto_ban', 'group_msg', 'particular_e_notice', 'group_recall']:
                        switchers.update({fn_name: False})
                switcher_dict.update({str(group['group_id']): switchers})
            with open(switcher_path, 'w', encoding='utf-8') as swp:
                swp.write(f"{json.dumps(switcher_dict)}")
    if not limit_word_path.exists():  # 要联网的都丢最后面去
        if (config_path / '违禁词_简单.txt').exists():
            with open(config_path / '违禁词_简单.txt', 'r', encoding='utf-8') as f:
                content = f.read()
            with open(limit_word_path, 'w', encoding='utf-8') as f:
                f.write(content)
            (config_path / '违禁词_简单.txt').unlink()
        else:
            await mk('file', limit_word_path, 'w',
                     url='https://fastly.jsdelivr.net/gh/yzyyz1387/nwafu/f_words/f_word_easy', dec='简单违禁词词库')
    if not ttf_name.exists():
        await mk('file', ttf_name, 'wb', url='https://fastly.jsdelivr.net/gh/yzyyz1387/blogimages/msyhblod.ttf',
                 dec='资源字体')
    # 删除成员清理锁文件
    for lock in kick_lock_path.iterdir():
        lock.unlink()
        logger.info(f"删除成员清理锁文件{lock}")
    logger.info('Admin 插件 初始化检测完成')


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
    if type_ == 'dir':
        os.mkdir(path_)
        logger.info(f"创建文件夹{path_}")
    elif type_ == 'file':
        if 'url' in kwargs:
            if kwargs['dec']:
                logger.info(f"开始下载文件{kwargs['dec']}")
            async with httpx.AsyncClient() as client:
                try:
                    r = await client.get(kwargs['url'])
                    if mode[0] == 'w':
                        with open(path_, 'w', encoding='utf-8') as f:
                            f.write(r.text)
                    elif mode[0] == 'wb':
                        with open(path_, 'wb') as f:
                            f.write(r.content)
                    logger.info(f"下载文件 {kwargs['dec']} 到 {path_}")
                except:
                    logger.error('文件下载失败!!!')
        else:
            if mode:
                with open(path_, mode[0]) as f:
                    f.write(kwargs['content'])
                logger.info(f"创建文件{path_}")
            else:
                raise Exception('mode 不能为空')
    else:
        raise Exception('type_参数错误')


async def banSb(bot: Bot, gid: int, ban_list: list, time: int = None, scope: list = None):
    """
    构造禁言
    :param gid: 群号
    :param time: 时间（s)
    :param ban_list: at列表
    :param scope: 用于被动检测禁言的时间范围
    :return:禁言操作
    """
    if 'all' in ban_list:
        yield bot.set_group_whole_ban(
            group_id=gid,
            enable=True
        )
    else:
        if time is None:
            if scope is None:
                time = random.randint(plugin_config.ban_rand_time_min, plugin_config.ban_rand_time_max)
            else:
                time = random.randint(scope[0], scope[1])
        for qq in ban_list:
            if int(qq) in su or str(qq) in su:
                logger.info(f"SUPERUSER无法被禁言, {qq}")
                # if cb_notice:
                #     await nonebot.get_bot().send_group_msg(group_id = gid, message = 'SUPERUSER无法被禁言')
            else:
                yield bot.set_group_ban(
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
        msg = msg.replace(cq, '')
    links = re.findall(find_link, msg)
    for link in links:
        msg = msg.replace(link, '')
    return msg


async def participle_simple_handle() -> list[str]:
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
             '被', '给', '让', '叫', '归', '由', '把', '将', '管', '对', '对于', '关于', '跟',
             '和', '给', '替', '向', '同', '除了']

    pron_ = ['各个', '本人', '这个', '各自', '哪些', '怎的', '我', '大家', '她们', '多少', '怎么', '那么', '那样',
             '怎样', '几时', '哪儿', '我们', '自我', '什么', '哪个', '那个', '另外', '自己', '哪样', '这儿', '那些',
             '这样', '那儿', '它们', '它', '他', '你', '谁', '今', '吗', '是', '乌', '如何', '彼此', '其次', '列位',
             '该', '各', '然', '安', '之', '怎', '夫', '其', '每', '您', '伊', '此', '者', '咱们', '某', '诸位',
             '这些', '予', '任何', '若', '彼', '恁', '焉', '兹', '俺', '汝', '几许', '多咱', '谁谁', '有些', '干吗',
             '何如', '怎么样', '好多', '哪门子', '这程子', '他人', '奈何', '人家', '若干', '本身', '旁人', '其他',
             '其余', '一切', '如此', '谁人', '怎么着', '那会儿', '自家', '哪会儿', '谁边', '这会儿', '几儿', '这么些',
             '那阵儿', '那么点儿', '这么点儿', '这么样', '这阵儿', '一应', '多会儿', '何许', '若何', '大伙儿', '几多',
             '恁地', '谁个', '乃尔', '那程子', '多早晚', '如许', '倷', '孰', '侬', '怹', '朕', '他们', '这么着',
             '那么些', '咱家', '你们', '那么着']

    others_ = ['就', '这', '那', '都', '也', '还', '又', '有', '没', '好', '我', '我的', '说', '去', '点', '不是',
               '就是', '要', '一个', '现在',
               '啥']

    sum_ = prep_ + pron_ + others_
    return sum_


# async def pic_cof(data: str, **kwargs) -> Optional[dict]:
#     try:
#         if kwargs['mode'] == 'url':
#             async with httpx.AsyncClient() as client:
#                 data_ = str(base64.b64encode((await client.get(url = data)).content), encoding = 'utf-8')
#             json_ = {'data': [f"data:image/png;base64,{data_}"]}
#         else:
#             json_ = {'data': [f"data:image/png;base64,{data}"]}
#     except Exception as err:
#         json_ = {'data': ['data:image/png;base64,']}
#         print(err)
#     try:
#         async with httpx.AsyncClient() as client:
#             r = (await client.post(
#                 url = 'https://hf.space/gradioiframe/mayhug/rainchan-image-porn-detection/+/api/predict/',
#                 json = json_)).json()
#         if 'error' in r:
#             return None
#         else:
#             return r
#     except Exception as err:
#         logger.debug(f"于\"utils.py\"中的 pic_cof 发生错误：{err}")
#         return None
#
#
# async def pic_ban_cof(**data) -> Optional[bool]:
#     global result
#     if data:
#         if 'url' in data:
#             result = await pic_cof(data = data['url'], mode = 'url')
#         if 'base64' in data:
#             result = await pic_cof(data = data['data'], mode = 'default')
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
        httpProfile.endpoint = 'ims.tencentcloudapi.com'

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = ims_client.ImsClient(cred, 'ap-shanghai', clientProfile)

        req = models.ImageModerationRequest()
        params = (
            {'BizType': 'group_recall', 'FileUrl': img}
            if type(img) is str
            else {'BizType': 'group_recall', 'FileContent': bytes_to_base64(img)}
        )
        req.from_json_string(json.dumps(params))

        resp = client.ImageModeration(req)
        return json.loads(resp.to_json_string())

    except TencentCloudSDKException as err:
        return err
    except KeyError as kerr:
        return kerr


async def image_moderation_async(img: Union[str, bytes]) -> Optional[dict]:
    try:
        resp = (await asyncio.to_thread(image_moderation, img))
        return resp
    except Exception as e:
        return None


def bytes_to_base64(data):
    return base64.b64encode(data).decode('utf-8')


def json_load(path) -> Optional[dict]:
    """
    加载json文件
    :return: Optional[dict]
    """
    try:
        with open(path, mode='r', encoding='utf-8') as f:
            contents = json.load(f)
            return contents
    except FileNotFoundError:
        return None


def json_upload(path, dict_content) -> None:
    """
    更新json文件
    :param path: 路径
    :param dict_content: python对象，字典
    """
    with open(path, mode='w', encoding='utf-8') as c:
        c.write(json.dumps(dict_content, ensure_ascii=False, indent=2))


async def del_txt_line(path: Path, matcher: Matcher, event: GroupMessageEvent, args: Message, dec: str,
                       group: bool = True) -> None:
    """
    分群、按行删除txt内容
    :param path: 文件父级路径（文件以群号命名）
    :param matcher: matcher
    :param event: 事件
    :param args: 文本
    :param dec: 描述
    :param group: 是否为群聊
    """
    gid = str(event.group_id)
    logger.info(args)
    if args:
        msg = str(args).split(' ')
        logger.info(msg)
        this_path = (path / f"{str(gid)}.txt") if group else path
        try:
            with open(this_path, mode='r+', encoding='utf-8') as c:
                is_saved = c.read().split("\n")
            with open(this_path, mode='w', encoding='utf-8') as c:
                success_del = []
                already_del = []
                for words in msg:
                    if words not in is_saved:
                        already_del.append(words)
                    for i in is_saved:
                        if words == i:
                            is_saved.remove(i)
                            logger.info(f"删除{dec} \"{words}\"成功")
                            success_del.append(words)
                c.write('\n'.join(is_saved))
                if success_del:
                    await matcher.send(f"{str(success_del)}删除成功")
                if already_del:
                    await matcher.send(f"{str(already_del)}还不是{dec}")
        except FileNotFoundError:
            await matcher.finish(f"该群没有{dec}")
    else:
        await matcher.finish(f"请输入删除内容,多个以空格分隔，例：\n删除{dec} 内容1 内容2")


async def add_txt_line(path: Path, matcher: Matcher, event: GroupMessageEvent, args: Message, dec: str,
                       group: bool = True) -> None:
    """
    分群、按行添加txt内容
    :param path: 文件父级路径（文件以群号命名）
    :param matcher: matcher
    :param event: 事件
    :param args: 文本
    :param dec: 描述
    :param group: 是否为群聊
    """
    gid = str(event.group_id)
    logger.info(args)
    if args:
        msg = str(args).split(' ')
        logger.info(msg)
        this_path = (path / f"{str(gid)}.txt") if group else path
        try:
            with open(this_path, mode='r+', encoding='utf-8') as c:
                is_saved = c.read().split('\n')
                success_add = []
                already_add = []
                for words in msg:
                    if words in is_saved:
                        logger.info(f"{words}已存在")
                        already_add.append(words)
                    else:
                        c.write(words + '\n')
                        logger.info(f"添加\"{words}\"为{dec}成功")
                        success_add.append(words)
                if already_add:
                    await matcher.send(f"{str(already_add)}已存在")
                if success_add:
                    await matcher.send(f"{str(success_add)}添加成功")
        except FileNotFoundError:
            success_add = []
            with open(this_path, mode='w', encoding='utf-8') as c:
                for words in msg:
                    c.write(words + '\n')
                    logger.info(f"添加\"{words}\"为{dec}成功")
                    success_add.append(words)
            await matcher.finish(f"添加{str(success_add)}成功")
    else:
        await matcher.finish(f"请输入添加内容,多个以空格分隔，例：\n添加{dec} 内容1 内容2")


async def get_txt_line(path: Path, matcher: Matcher, event: GroupMessageEvent, args: Message, dec: str,
                       group: bool = True) -> None:
    """
    分群、按行获取txt内容
    :param path: 文件父级路径（文件以群号命名）
    :param matcher: matcher
    :param event: 事件
    :param args: 文本
    :param dec: 描述
    :param group: 是否为群聊
    """
    gid = str(event.group_id)
    try:
        this_path = (path / f"{str(gid)}.txt") if group else path
        try:
            with open(this_path, 'r', encoding='utf-8') as c:
                is_saved = c.read().split('\n')
                is_saved.remove('')
            await matcher.finish(f"{str(is_saved)}")
        except ActionFailed:
            await matcher.finish('内容太长，无法发送')
        except FileNotFoundError:
            await matcher.finish(f"该群没有{dec}")
    except FileNotFoundError:
        logger.error('文件不存在!!!!!')


async def change_s_title(bot: Bot, matcher: Matcher, gid: int, uid: int, s_title: Optional[str]):
    """
    改头衔
    :param bot: bot
    :param matcher: matcher
    :param gid: 群号
    :param uid: 用户号
    :param s_title: 头衔
    """
    try:
        await bot.set_group_special_title(
            group_id=gid,
            user_id=uid,
            special_title=s_title,
            duration=-1,
        )
        await log_fi(matcher, f"头衔操作成功:{s_title}")
    except ActionFailed:
        logger.info('权限不足')


async def get_user_violation(gid: int, uid: int, label: str, content: str, add_: bool = True) -> int:
    """
    获取用户违规情况
    :param gid: 群号
    :param uid: 用户号
    :param label: 违规标签
    :param content: 内容
    :param add_: 等级是否+1
    :return: 违规等级
    """
    path_grop = user_violation_info_path / f"{str(gid)}"
    path_user = path_grop / f"{str(uid)}.json"
    this_time = str(datetime.datetime.now()).replace(' ', '-')
    uid = str(uid)
    if not os.path.exists(user_violation_info_path):
        await mk('dir', user_violation_info_path, mode=None)
    if not os.path.exists(path_grop):
        await mk('dir', path_grop, mode=None)
        await vio_level_init(path_user, uid, this_time, label, content)
        return 0
    try:
        info = json_load(path_user)
        level = info[uid]['level']
        if add_:
            info[uid]['level'] += 1
        info[uid]['info'][this_time] = [label, content]
        json_upload(path_user, info)
        if level >= 7:
            return 7
        else:
            return level
    except FileNotFoundError:
        await vio_level_init(path_user, uid, this_time, label, content)
        return 0
    except Exception as e:
        logger.error(f"获取用户违禁等级出错：{e}，尝试初始化此用户违禁等级")
        await vio_level_init(path_user, uid, this_time, label, content)
        return 0


async def vio_level_init(path_user, uid, this_time, label, content) -> None:
    with open(path_user, mode='w', encoding='utf-8') as c:
        c.write(json.dumps({uid: {'level': 0, 'info': {this_time: [label, content]}}}, ensure_ascii=False))


async def error_log(gid: int, time: str, matcher: Matcher, err: str) -> None:
    module = str(matcher.module_name)
    if not os.path.exists(error_path):
        await mk('dir', error_path, mode=None)
    if not os.path.exists(error_path / f"{str(gid)}.json"):
        json_upload(error_path / f"{str(gid)}.json", {str(gid): {time: [module, err]}})
    else:
        try:
            info = json_load(error_path / f"{str(gid)}.json")
            info[str(gid)][time] = [module, err]
            json_upload(error_path / f"{str(gid)}.json", info)
        except Exception as e:
            logger.error(f"写入错误日志出错：{e}")


async def sd(cmd: Matcher, msg, at=False) -> None:
    if cb_notice:
        await cmd.send(msg, at_sender=at)


async def log_sd(cmd: Matcher, msg, log: str = None, at=False, err=False) -> None:
    (logger.error if err else logger.info)(log if log else msg)
    await sd(cmd, msg, at)


async def fi(cmd: Matcher, msg) -> None:
    await cmd.finish(msg if cb_notice else None)


async def log_fi(cmd: Matcher, msg, log: str = None, err=False) -> None:
    (logger.error if err else logger.info)(log if log else msg)
    await fi(cmd, msg)
