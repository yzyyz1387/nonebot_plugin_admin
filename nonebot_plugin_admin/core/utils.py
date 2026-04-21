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
from typing import Union, Optional

import httpx
import nonebot
from nonebot import logger
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, ActionFailed, Bot
from nonebot.matcher import Matcher

from ..util.file_util import read_all_lines, read_all_text, write_all_txt
from .config import plugin_config, global_config
from .path import *

TencentID = plugin_config.tenid
TencentKeys = plugin_config.tenkeys
su = global_config.superusers
cb_notice = plugin_config.callback_notice

dirs = [
    config_path,
    template_path,
    res_path,
    re_img_path,
    wordcloud_bg_path,
    error_path,
    kick_lock_path,
]
LEGACY_RUNTIME_STORAGE_PATHS = {
    str(word_path),
    str(statistics_record_state_path),
    str(limit_word_path),
}


def clear_all_cleanup_locks() -> int:
    """
    清理all清理locks
    :return: int
    """
    if not kick_lock_path.exists():
        return 0

    cleared = 0
    for lock in kick_lock_path.iterdir():
        if not lock.is_file():
            continue
        try:
            lock.unlink()
            cleared += 1
            logger.info(f"删除成员清理锁文件{lock}")
        except FileNotFoundError:
            continue
    return cleared


async def init():
    """
    初始化配置文件
    :return:
    """
    for d in dirs:
        if not d.exists():
            await mk('dir', d, mode=None)
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


async def _init_runtime_assets():
    """Initialize required runtime directories and bundled assets."""
    for d in dirs:
        if not d.exists():
            await mk('dir', d, mode=None)
    if not ttf_name.exists():
        await mk(
            'file',
            ttf_name,
            'wb',
            url='https://fastly.jsdelivr.net/gh/yzyyz1387/blogimages/msyhblod.ttf',
            dec='资源字体',
        )
    for lock in kick_lock_path.iterdir():
        lock.unlink()
        logger.info(f"删除成员清理锁文件：{lock}")
    logger.info("Admin 插件初始化检测完成")


init = _init_runtime_assets


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
        if str(path_) in LEGACY_RUNTIME_STORAGE_PATHS:
            logger.info(f"跳过旧版文本存储初始化：{path_}")
            return
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


async def mute_sb(bot: Bot, gid: int, lst: list, time: int = None, scope: list = None):
    """
    构造禁言
    :param gid: 群号
    :param time: 时间（s)
    :param lst: at列表
    :param scope: 用于被动检测禁言的时间范围
    :return:禁言操作
    """
    if 'all' in lst:
        yield bot.set_group_whole_ban(group_id=gid, enable=True)
    else:
        if time is None:
            if scope is None:
                time = random.randint(plugin_config.ban_rand_time_min, plugin_config.ban_rand_time_max)
            else:
                time = random.randint(scope[0], scope[1])
        for qq in lst:
            if int(qq) in su or str(qq) in su:
                logger.info(f"SUPERUSER无法被禁言, {qq}")
            else:
                yield bot.set_group_ban(group_id=gid, user_id=qq, duration=time)


def participle_simple_handle() -> list[str]:
    """
    wordcloud停用词
    """
    prep_ = ['么', '了', '与', '不', '且', '之', '为', '兮', '其', '到', '云', '阿', '却', '个', '以', '们', '价', '似',
             '讫', '诸', '取', '若', '得', '逝', '将', '夫', '头', '只', '吗', '向', '吧', '呗', '呃', '呀', '员', '呵',
             '呢', '哇', '咦', '哟', '哉', '啊', '哩', '啵', '唻', '啰', '唯', '嘛', '噬', '嚜', '家', '如', '掉', '给',
             '维', '圪', '在', '尔', '惟', '子', '赊', '焉', '然', '旃', '所', '见', '斯', '者', '来', '欤', '是', '毋',
             '曰', '的', '每', '看', '着', '矣', '罢', '而', '耶', '粤', '聿', '等', '言', '越', '馨', '趴', '从',
             '自从', '自', '打', '到', '往', '在', '由', '向', '于', '至', '趁', '当', '当着', '沿着', '顺着', '按',
             '按照', '遵照', '依照', '靠', '本着', '用', '通过', '根据', '据', '拿', '比', '因', '因为', '由于', '为',
             '为了', '为着', '被', '给', '让', '叫', '归', '由', '把', '将', '管', '对', '对于', '关于', '跟', '和',
             '给', '替', '向', '同', '除了']

    pron_ = ['各个', '本人', '这个', '各自', '哪些', '怎的', '我', '大家', '她们', '多少', '怎么', '那么', '那样',
             '怎样', '几时', '哪儿', '我们', '自我', '什么', '哪个', '那个', '另外', '自己', '哪样', '这儿', '那些',
             '这样', '那儿', '它们', '它', '他', '你', '谁', '今', '吗', '是', '乌', '如何', '彼此', '其次', '列位',
             '该', '各', '然', '安', '之', '怎', '夫', '其', '每', '您', '伊', '此', '者', '咱们', '某', '诸位', '这些',
             '予', '任何', '若', '彼', '恁', '焉', '兹', '俺', '汝', '几许', '多咱', '谁谁', '有些', '干吗', '何如',
             '怎么样', '好多', '哪门子', '这程子', '他人', '奈何', '人家', '若干', '本身', '旁人', '其他', '其余',
             '一切', '如此', '谁人', '怎么着', '那会儿', '自家', '哪会儿', '谁边', '这会儿', '几儿', '这么些', '那阵儿',
             '那么点儿', '这么点儿', '这么样', '这阵儿', '一应', '多会儿', '何许', '若何', '大伙儿', '几多', '恁地',
             '谁个', '乃尔', '那程子', '多早晚', '如许', '倷', '孰', '侬', '怹', '朕', '他们', '这么着', '那么些',
             '咱家', '你们', '那么着']

    others_ = ['就', '这', '那', '都', '也', '还', '又', '有', '没', '好', '我', '我的', '说', '去', '点', '不是',
               '就是', '要', '一个', '现在', '啥']

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
    """
    处理 image_moderation 的业务逻辑
    :param img: img 参数
    :return: None
    """
    try:
        from tencentcloud.common import credential
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.ims.v20201229 import ims_client, models
        try:
            cred = credential.Credential(TencentID, TencentKeys)
            httpProfile = HttpProfile()
            httpProfile.endpoint = 'ims.tencentcloudapi.com'

            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = ims_client.ImsClient(cred, 'ap-shanghai', clientProfile)

            req = models.ImageModerationRequest()
            params = (
                {'BizType': 'group_recall', 'FileUrl': img}
                if type(img) is str else
                {'BizType': 'group_recall', 'FileContent': bytes_to_base64(img)}
            )
            req.from_json_string(json.dumps(params))

            resp = client.ImageModeration(req)
            return json.loads(resp.to_json_string())

        except TencentCloudSDKException as err:
            return err
        except KeyError as kerr:
            return kerr
    except Exception:
        return None


async def image_moderation_async(img: Union[str, bytes]) -> Optional[dict]:
    """
    处理 image_moderation_async 的业务逻辑
    :param img: img 参数
    :return: Optional[dict]
    """
    try:
        return await asyncio.to_thread(image_moderation, img)
    except Exception:
        return None


def bytes_to_base64(data):
    """
    处理 bytes_to_base64 的业务逻辑
    :param data: 数据对象
    :return: None
    """
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


def json_load_or_default(path, default):
    """
    处理 json_load_or_default 的业务逻辑
    :param path: 路径对象
    :param default: default 参数
    :return: None
    """
    contents = json_load(path)
    if contents is None:
        return default.copy() if isinstance(default, dict) else default
    return contents


def json_upload(path, dict_content) -> None:
    """
    更新json文件
    :param path: 路径
    :param dict_content: python对象，字典
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode='w', encoding='utf-8') as c:
        c.write(json.dumps(dict_content, ensure_ascii=False, indent=2))


def get_group_path(event: GroupMessageEvent, path: Path) -> Path:
    """
    获取群路径
    :param event: 事件对象
    :param path: 路径对象
    :return: Path
    """
    return path / f"{str(event.group_id)}.txt"


async def del_txt_line(path: Path, matcher: Matcher, args: Message, dec: str) -> None:
    """
    分群、按行删除txt内容
    :param path: 文件路径
    :param matcher: matcher
    :param args: 文本
    :param dec: 描述
    """
    logger.info(args)
    if not args:
        await matcher.finish(f"请输入删除内容,多个以空格分隔，例：\n删除{dec} 内容1 内容2")
    else:
        msg = str(args).split(' ')
        logger.info(msg)
        saved_words = read_all_lines(path)
        success_del = []
        already_del = []

        for word in msg:
            # FIXME: word一般为'群主是猪',需要加参的话\t手机比较难打出来,用代码将word中的\\t替换为\t?
            if word in saved_words:
                saved_words.remove(word)
                success_del.append(word)
                logger.info(f"删除'{dec}' '{word}'成功")
            else:
                already_del.append(word)

        # 回写
        if saved_words:
            r = '\n'.join(saved_words)
            write_all_txt(path, r, False)
        if success_del:
            await matcher.send(f"{str(success_del)}删除成功")
        if already_del:
            await matcher.send(f"{str(already_del)}还不是{dec}")
        await matcher.finish()


async def add_txt_line(path: Path, matcher: Matcher, args: Message, dec: str) -> None:
    """
    分群、按行添加txt内容
    :param path: 文件父级路径（文件以群号命名）
    :param matcher: matcher
    :param args: 文本
    :param dec: 描述
    """
    logger.info(args)
    if not args:
        await matcher.finish(f"请输入添加内容,多个以空格分隔，例：\n添加{dec} 内容1 内容2")
    else:
        msg = str(args).split(' ')
        logger.info(msg)
        saved_words = read_all_lines(path)
        already_add = []
        success_add = []
        write_append = []
        for words in msg:
            if words in saved_words:
                logger.info(f"{words}已存在")
                already_add.append(words)
            else:
                write_append.append(words + '\n')
                logger.info(f"添加\"{words}\"为{dec}成功")
                success_add.append(words)
        if write_append:
            r = '\n'.join(write_append)
            write_all_txt(path, r, True)
        if already_add:
            await matcher.send(f"{str(already_add)}已存在")
        if success_add:
            await matcher.send(f"{str(success_add)}添加成功")


async def get_txt_line(path: Path, matcher: Matcher, dec: str) -> None:
    """
    分群、按行获取txt内容
    :param path: 文件父级路径（文件以群号命名）
    :param matcher: matcher
    :param dec: 描述
    """
    try:
        saved_words = read_all_text(path).rstrip()
        await matcher.finish(saved_words)
    except ActionFailed:
        await matcher.finish('内容太长，无法发送')
    except FileNotFoundError:
        await matcher.finish(f"该群没有{dec}")


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
        await bot.set_group_special_title(group_id=gid, user_id=uid, special_title=s_title, duration=-1)
        await log_fi(matcher, f"头衔操作成功:{s_title}")
    except ActionFailed:
        logger.info('权限不足')


async def get_user_violation(gid: int, uid: int, label: str, content: str, add_: bool = True) -> int:
    """
    获取user违规
    :param gid: 群号
    :param uid: 用户号
    :param label: label 参数
    :param content: 内容
    :param add_: add_ 参数
    :return: int
    """
    from ..statistics.config_orm_store import (
        orm_add_violation_record,
        orm_get_user_violation_level,
        orm_save_user_violation,
    )

    this_time = str(datetime.datetime.now()).replace(' ', '-')
    gid_str = str(gid)
    uid_str = str(uid)

    try:
        level = await orm_get_user_violation_level(gid_str, uid_str)
        current_level = int(level or 0)
        if level is None:
            new_level = 0
        else:
            new_level = current_level + 1 if add_ else current_level
        await orm_save_user_violation(gid_str, uid_str, new_level)
        await orm_add_violation_record(gid_str, uid_str, this_time, label, content)
        return min(current_level, 7)
    except Exception as e:
        logger.error(f"获取用户违禁等级出错：{e}")
        return 0


async def error_log(gid: int, time: str, matcher: Matcher, err: str) -> None:
    """
    处理 error_log 的业务逻辑
    :param gid: 群号
    :param time: time 参数
    :param matcher: Matcher 实例
    :param err: err 参数
    :return: None
    """
    module = str(matcher.module_name)
    try:
        from ..dashboard.dashboard_oplog_service import record_oplog
        await record_oplog(
            action="plugin_error",
            group_id=str(gid),
            detail=f"[{module}] {err}",
            extra={"module": module, "error": err, "time": time},
        )
    except Exception:
        pass

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


async def sd(cmd: Matcher, msg: str, at=False) -> None:
    """
    处理 sd 的业务逻辑
    :param cmd: cmd 参数
    :param msg: 消息文本
    :param at: at 参数
    :return: None
    """
    if cb_notice:
        await cmd.send(msg, at_sender=at)


async def log_sd(cmd: Matcher, msg, log: str = None, at=False, err=False) -> None:
    """
    处理 log_sd 的业务逻辑
    :param cmd: cmd 参数
    :param msg: 消息文本
    :param log: log 参数
    :param at: at 参数
    :param err: err 参数
    :return: None
    """
    (logger.error if err else logger.info)(log if log else msg)
    await sd(cmd, msg, at)


async def fi(cmd: Matcher, msg) -> None:
    """
    处理 fi 的业务逻辑
    :param cmd: cmd 参数
    :param msg: 消息文本
    :return: None
    """
    await cmd.finish(msg if cb_notice else None)


async def log_fi(cmd: Matcher, msg, log: str = None, err=False) -> None:
    """
    处理 log_fi 的业务逻辑
    :param cmd: cmd 参数
    :param msg: 消息文本
    :param log: log 参数
    :param err: err 参数
    :return: None
    """
    (logger.error if err else logger.info)(log if log else msg)
    await fi(cmd, msg)
