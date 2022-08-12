# python3
# -*- coding: utf-8 -*-
# @Time    : 2021/12/23 0:52
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : __init__.py
# @Software: PyCharm

import json
from nonebot.params import CommandArg
import nonebot
from nonebot.adapters import Message
from asyncio import sleep as asleep
from traceback import print_exc
from random import randint
from nonebot import on_command, logger, on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, NoticeEvent
from nonebot.adapters.onebot.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from . import (
    approve,
    auto_ban,
    auto_ban_,
    func_hook,
    group_request_verify,
    img_check,
    notice,
    request,
    request_manual,
    word_analyze,
    wordcloud,
    switcher,
    utils,
    hello,
)
from .utils import At, Reply, MsgText, banSb, init, check_func_status, change_s_title
from .group_request_verify import verify
from .config import plugin_config, global_config




su = global_config.superusers
cb_notice = plugin_config.callback_notice

admin_init = on_command('群管初始化', priority=1, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@admin_init.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await init()


ban = on_command('禁', priority=1, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@ban.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    /禁 @user 禁言
    """
    try:
        msg = MsgText(event.json()).replace(" ", "").replace("禁", "")
        time = int("".join(map(str, list(map(lambda x: int(x), filter(lambda x: x.isdigit(), msg))))))
        # 提取消息中所有数字作为禁言时间
    except ValueError:
        time = None
    sb = At(event.json())
    gid = event.group_id
    if sb:
        baning = banSb(gid, ban_list=sb, time=time)
        try:
            async for baned in baning:
                if baned:
                    await baned
        except ActionFailed:
            await ban.finish("权限不足")
        else:
            logger.info("禁言操作成功")
            if cb_notice:  # 迭代结束再通知
                if time is not None:
                    await ban.finish("禁言操作成功")
                else:
                    await ban.finish("该用户已被禁言随机时长")
    else:
        pass


unban = on_command("解", priority=1, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@unban.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    /解 @user 解禁
    """
    sb = At(event.json())
    gid = event.group_id
    if sb:
        baning = banSb(gid, ban_list=sb, time=0)
        try:
            async for baned in baning:
                if baned:
                    await baned
        except ActionFailed:
            await unban.finish("权限不足")
        else:
            logger.info("解禁操作成功")
            if cb_notice:  # 迭代结束再通知
                await unban.finish("解禁操作成功")


ban_all = on_command("/all", aliases={"/全员"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


@ban_all.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    （测试时没用..） 
    # note: 如果在 .env.* 文件内设置了 COMMAND_START ，且不包含 "" (即所有指令都有前缀，假设 '/' 是其中一个前缀)，则应该发 //all 触发 
    /all 全员禁言
    /all  解 关闭全员禁言
    """
    msg = event.get_message()
    if msg and '解' in str(msg):
        enable = False
    else:
        enable = True
    try:
        await bot.set_group_whole_ban(
            group_id=event.group_id,
            enable=enable
        )
    except ActionFailed:
        await ban_all.finish("权限不足")
    else:
        logger.info(f"全体操作成功: {'禁言' if enable else '解禁'}")
        if cb_notice:
            await ban_all.finish(f"全体操作成功: {'禁言' if enable else '解禁'}")


change = on_command('改', permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


@change.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    /改 @user xxx 改群昵称
    """
    msg = str(event.get_message())
    logger.info(msg.split())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        try:
            for user_ in sb:
                await bot.set_group_card(
                    group_id=gid,
                    user_id=int(user_),
                    card=msg.split()[-1:][0]
                )
        except ActionFailed:
            await change.finish("权限不足")
        else:
            logger.info("改名片操作成功")
            if cb_notice:
                await change.finish("改名片操作成功")


title = on_command('头衔', priority=1, block=True)


@title.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent):
    """
    /头衔 @user  xxx  给某人头衔
    """
    # msg = str(event.get_message())
    msg = MsgText(event.json())
    s_title = msg.replace(" ", "").replace("头衔", "", 1)
    sb = At(event.json())
    gid = event.group_id
    uid = event.user_id
    if not sb or (len(sb) == 1 and sb[0] == uid):
        await change_s_title(bot, matcher, gid, uid, s_title)
    elif sb:
        if 'all' not in sb:
            if uid in su or (str(uid) in su):
                for qq in sb:
                    await change_s_title(bot, matcher, gid, int(qq), s_title)

            else:
                await title.finish("超级用户才可以更改他人头衔，更改自己头衔请直接使用【头衔 xxx】")
        else:
            await title.finish("不能含有@全体成员")


title_ = on_command('删头衔', priority=1, block=True)


@title_.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent):
    """
    /删头衔 @user 删除头衔
    """
    msg = MsgText(event.json())
    s_title = ""
    sb = At(event.json())
    gid = event.group_id
    uid = event.user_id
    if not sb or (len(sb) == 1 and sb[0] == uid):
        await change_s_title(bot, matcher, gid, uid, s_title)
    elif sb:
        if 'all' not in sb:
            if uid in su or (str(uid) in su):
                for qq in sb:
                    await change_s_title(bot, matcher, gid, int(qq), s_title)
            else:
                await title.finish("超级用户才可以删他人头衔，删除自己头衔请直接使用【删头衔】")
        else:
            await title.finish("不能含有@全体成员")


kick = on_command('踢', permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


@kick.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    /踢 @user 踢出某人
    """
    msg = str(event.get_message())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if 'all' not in sb:
            try:
                for qq in sb:
                    await bot.set_group_kick(
                        group_id=gid,
                        user_id=int(qq),
                        reject_add_request=False
                    )
            except ActionFailed:
                await kick.finish("权限不足")
            else:
                logger.info(f"踢人操作成功")
                if cb_notice:
                    await kick.finish(f"踢人操作成功")
        else:
            await kick.finish("不能含有@全体成员")


kick_ = on_command('黑', permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=1, block=True)


@kick_.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    黑 @user 踢出并拉黑某人
    """
    msg = str(event.get_message())
    sb = At(event.json())
    gid = event.group_id
    if sb:
        if 'all' not in sb:
            try:
                for qq in sb:
                    await bot.set_group_kick(
                        group_id=gid,
                        user_id=int(qq),
                        reject_add_request=True
                    )
            except ActionFailed:
                await kick_.finish("权限不足")
            else:
                logger.info(f"踢人并拉黑操作成功")
                if cb_notice:
                    await kick_.finish(f"踢人并拉黑操作成功")
        else:
            await kick_.finish("不能含有@全体成员")


set_g_admin = on_command("管理员+", permission=SUPERUSER | GROUP_OWNER, priority=1, block=True)


@set_g_admin.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    管理员+ @user 添加群管理员
    """
    msg = str(event.get_message())
    logger.info(msg)
    logger.info(msg.split())
    sb = At(event.json())
    logger.info(sb)
    gid = event.group_id
    if sb:
        if 'all' not in sb:
            try:
                for qq in sb:
                    await bot.set_group_admin(
                        group_id=gid,
                        user_id=int(qq),
                        enable=True
                    )
            except ActionFailed:
                await set_g_admin.finish("权限不足")
            else:
                logger.info(f"设置管理员操作成功")
                await set_g_admin.finish("设置管理员操作成功")
        else:
            await set_g_admin.finish("指令不正确 或 不能含有@全体成员")


unset_g_admin = on_command("管理员-", permission=SUPERUSER | GROUP_OWNER, priority=1, block=True)


@unset_g_admin.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    """
    管理员+ @user 添加群管理员
    """
    msg = str(event.get_message())
    logger.info(msg)
    logger.info(msg.split())
    sb = At(event.json())
    logger.info(sb)
    gid = event.group_id
    if sb:
        if 'all' not in sb:
            try:
                for qq in sb:
                    await bot.set_group_admin(
                        group_id=gid,
                        user_id=int(qq),
                        enable=False
                    )
            except ActionFailed:
                await unset_g_admin.finish("权限不足")
            else:
                logger.info(f"取消管理员操作成功")
                await unset_g_admin.finish("取消管理员操作成功")
        else:
            await unset_g_admin.finish("指令不正确 或 不能含有@全体成员")


msg_recall = on_command("撤回", priority=1, aliases={"删除", "recall"}, block=True,
                        permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@msg_recall.handle()
async def _(bot: Bot, event: GroupMessageEvent):  # by: @tom-snow
    """
    指令格式:
    /撤回 @user n
    回复指定消息时撤回该条消息；使用艾特时撤回被艾特的人在本群 n*19 历史消息内的所有消息。
    不输入 n 则默认 n=5
    """
    # msg = str(event.get_message())
    msg = MsgText(event.json())
    sb = At(event.json())
    rp = Reply(event.json())
    gid = event.group_id
    if not gid:  # FIXME: 有必要加吗？
        await msg_recall.finish("请在群内使用！")

    recall_msg_id = []
    if rp:
        recall_msg_id.append(rp["message_id"])
    elif sb:
        seq = None
        if len(msg.split(" ")) > 1:
            try:  # counts = n
                counts = int(msg.split(" ")[-1])
            except ValueError:
                counts = 5  # 出现错误就默认为 5 【理论上除非是 /撤回 @user n 且 n 不是数值时才有可能触发】
        else:
            counts = 5

        try:
            for i in range(counts):  # 获取 n 次
                await asleep(randint(0, 10))  # 睡眠随机时间，避免黑号
                res = await bot.call_api("get_group_msg_history", group_id=gid, message_seq=seq)  # 获取历史消息
                flag = True
                for message in res["messages"]:  # 历史消息列表
                    if flag:
                        seq = int(message["message_seq"]) - 1
                        flag = False
                    if int(message["user_id"]) in sb:  # 将消息id加入列表
                        recall_msg_id.append(int(message["message_id"]))
        except ActionFailed as e:
            await msg_recall.send(f"获取群历史消息时发生错误")
            logger.error(f"获取群历史消息时发生错误：{e}, seq: {seq}")
            print_exc()
    else:
        await msg_recall.finish("指令格式：\n/撤回 @user n\n回复指定消息时撤回该条消息；使用艾特时撤回被艾特的人在本群 n*19 历史消息内的所有消息。\n不输入 n 则默认 n=5")

    # 实际进行撤回的部分
    try:
        for msg_id in recall_msg_id:
            await asleep(randint(0, 3))  # 睡眠随机时间，避免黑号
            await bot.call_api("delete_msg", message_id=msg_id)
    except ActionFailed as e:
        logger.warning(f"执行失败，可能是我权限不足 {e}")
        await msg_recall.finish("执行失败，可能是我权限不足")
    else:
        logger.info(f"操作成功，一共撤回了 {len(recall_msg_id)} 条消息")
        if cb_notice:
            await msg_recall.finish(f"操作成功，一共撤回了 {len(recall_msg_id)} 条消息")


"""
! 消息防撤回模块，默认不开启，有需要的自行开启，想对部分群生效也需自行实现(可以并入本插件的开关系统内，也可控制 go-cqhttp 的事件过滤器)

如果在 go-cqhttp 开启了事件过滤器，请确保允许 post_type=notice 通行
【至少也得允许 notice_type=group_recall 通行】
"""


async def _group_recall(bot: Bot, event: NoticeEvent) -> bool:
    # 有需要自行取消注释
    # if event.notice_type == 'group_recall':
    #     return True
    return False


group_recall = on_notice(_group_recall, priority=5)


@group_recall.handle()
async def _(bot: Bot, event: NoticeEvent):
    event_obj = json.loads(event.json())
    user_id = event_obj["user_id"]  # 消息发送者
    operator_id = event_obj["operator_id"]  # 撤回消息的人
    group_id = event_obj["group_id"]  # 群号
    message_id = event_obj["message_id"]  # 消息 id

    if int(user_id) != int(operator_id): return  # 撤回人不是发消息人，是管理员撤回成员消息，不处理
    if int(operator_id) in su or str(operator_id) in su: return  # 发起撤回的人是超管，不处理
    # 管理员撤回自己的也不处理
    operator_info = await bot.get_group_member_info(group_id=group_id, user_id=operator_id, no_cache=True)
    if operator_info["role"] != "member": return
    # 防撤回
    recalled_message = await bot.get_msg(message_id=message_id)
    recall_notice = f"检测到{operator_info['card'] if operator_info['card'] else operator_info['nickname']}({operator_info['user_id']})撤回了一条消息：\n\n"
    await bot.send_group_msg(group_id=group_id, message=recall_notice + recalled_message['message'])
    await group_recall.finish()


__usage__ = """
【初始化】：
  群管初始化 ：初始化插件

【群管】：
权限：permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER
  禁言:
    禁 @某人 时间（s）[1,2591999]
    禁 时间（s）@某人 [1,2591999]
    禁 @某人 缺省时间则随机
    禁 @某人 0 可解禁
    解 @某人
  全群禁言（好像没用？）
    /all 
    /all 解
  改名片
    改 @某人 名片
  改头衔
    头衔 @某人 头衔
    删头衔
  踢出：
    踢 @某人
  踢出并拉黑：
   黑 @某人
  撤回:
   撤回 (回复某条消息即可撤回对应消息)
   撤回 @user [(可选，默认n=5)历史消息倍数n] (实际检查的历史数为 n*19)
   
【管理员】permission=SUPERUSER | GROUP_OWNER
  管理员+ @xxx 设置某人为管理员
  管理员- @xxx 取消某人管理员
  
【加群自动审批】：
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  查看词条 ： 查看本群审批词条   或/审批
  词条+ [词条] ：增加审批词条 或/审批+
  词条- [词条] ：删除审批词条 或/审批-

【superuser】：
  所有词条 ：  查看所有审批词条   或/su审批
  指定词条+ [群号] [词条] ：增加指定群审批词条 或/su审批+
  指定词条- [群号] [词条] ：删除指定群审批词条 或/su审批-
  自动审批处理结果将发送给superuser

【分群管理员设置】*分管：可以接受加群处理结果消息的用户
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  分管+ [user] ：user可用@或qq 添加分群管理员
  分管- [user] ：删除分群管理员
  查看分管 ：查看本群分群管理员

群内或私聊 permission=SUPERUSER
  所有分管 ：查看所有分群管理员
  群管接收 ：打开或关闭超管消息接收（关闭则审批结果不会发送给superusers）
  
【群词云统计】
该功能所用库 wordcloud 未写入依赖，请自行安装
群内发送：
  记录本群 ： 开始统计聊天记录 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  停止记录本群 ：停止统计聊天记录
  群词云 ： 发送词云图片
  
【被动识别】
涩图检测：将禁言随机时间

违禁词检测：已支持正则表达式，可定义触发违禁词操作(默认为禁言+撤回)
定义操作方法：用制表符分隔，左边为触发条件，右边为操作定义($禁言、$撤回)
群内发送：
  简单违禁词 ：简单级别过滤
  严格违禁词 ：严格级别过滤(不建议)
  更新违禁词库 ：手动更新词库
    违禁词库每周一自动更新
    
【功能开关】
群内发送：
  开关xx : 对某功能进行开/关  permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER
  开关状态 ： 查看各功能的状态
  xx in ：
    ['管理', '踢', '禁', '改', '基础群管']  #基础功能 踢、禁、改、管理员+-
    ['加群', '审批', '加群审批', '自动审批'] #加群审批
    ['词云', '群词云', 'wordcloud'] #群词云
    ['违禁词', '违禁词检测'] #违禁词检测
    ['图片检测', '图片鉴黄', '涩图检测', '色图检测'] #图片检测
所有功能默认开
"""
__help_plugin_name__ = "简易群管"

__permission__ = 1
__help__version__ = '0.2.0'
