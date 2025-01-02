# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/12/19 3:01
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : admin.py
# @Software: PyCharm
import asyncio
from random import randint
from traceback import print_exc

from nonebot import on_command
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.permission import SUPERUSER

from .admin_role import DEPUTY_ADMIN
from .config import global_config
from .message import *
from .utils import mute_sb, change_s_title, fi, log_fi, sd, log_sd

su = global_config.superusers

ban = on_command('禁', priority=2, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)
@ban.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, msg: str = Depends(msg_text),
            sb: list = Depends(msg_at)):
    """
    /禁 @user 禁言
    """
    try:
        msg = msg.replace(' ', '').replace('禁', '')
        # 提取消息中所有数字作为禁言时间
        time = int(''.join(map(str, list(map(lambda x: int(x), filter(lambda x: x.isdigit(), msg))))))
    except ValueError:
        time = None
    if sb:
        baning = mute_sb(bot, event.group_id, lst=sb, time=time)
        try:
            async for baned in baning:
                if baned:
                    await baned
            await log_fi(matcher, '禁言操作成功' if time is not None else '用户已被禁言随机时长')
        except ActionFailed:
            await fi(matcher, '权限不足')

unban = on_command('解', priority=2, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)
@unban.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    """
    /解 @user 解禁
    """
    if sb:
        baning = mute_sb(bot, event.group_id, lst=sb, time=0)
        try:
            async for baned in baning:
                if baned:
                    await baned
            await log_fi(matcher, '解禁操作成功')
        except ActionFailed:
            await fi(matcher, '权限不足')

ban_all = on_command('/all', priority=2, aliases={'/全员'}, block=True,
                     permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)
@ban_all.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, msg: str = Depends(msg_text)):
    """
    # note: 如果在 .env.* 文件内设置了 COMMAND_START ，且不包含 "" (即所有指令都有前缀，假设 '/' 是其中一个前缀)，则应该发 //all 触发
    /all 全员禁言
    /all  解 关闭全员禁言
    """
    if msg and '解' in str(msg):
        enable = False
    else:
        enable = True
    try:
        await bot.set_group_whole_ban(group_id=event.group_id, enable=enable)
        await log_fi(matcher, f"全体操作成功: {'禁言' if enable else '解禁'}")
    except ActionFailed:
        await fi(matcher, '权限不足')

change = on_command('改', priority=2, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)
@change.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, msg: str = Depends(msg_text),
            sb: list = Depends(msg_at)):
    """
    /改 @user xxx 改群昵称
    """
    if sb:
        try:
            for user_ in sb:
                await bot.set_group_card(group_id=event.group_id, user_id=int(user_), card=msg.split()[-1:][0])
            await log_fi(matcher, '改名片操作成功')
        except ActionFailed:
            await fi(matcher, '权限不足')

title = on_command('头衔', priority=2, block=True)
@title.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, msg: str = Depends(msg_text),
            sb: list = Depends(msg_at)):
    """
    /头衔 @user  xxx  给某人头衔
    """
    s_title = msg.replace(' ', '').replace('头衔', '', 1)
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
                await fi(matcher, '超级用户才可以更改他人头衔，更改自己头衔请直接使用【头衔 xxx】')
        else:
            await fi(matcher, '不能含有@全体成员')

title_ = on_command('删头衔', priority=2, block=True)
@title_.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    """
    /删头衔 @user 删除头衔
    """
    s_title = ''
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
                await fi(matcher, '超级用户才可以删他人头衔，删除自己头衔请直接使用【删头衔】')
        else:
            await fi(matcher, '不能含有@全体成员')

kick = on_command('踢', priority=2, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)
@kick.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    """
    /踢 @user 踢出某人
    """
    if not sb or 'all' in sb:
        await fi(matcher, '指令不正确 或 不能含有@全体成员')
    try:
        for qq in sb:
            if qq == event.user_id:
                await sd(matcher, '你在玩一种很新的东西，不能踢自己!')
                continue
            if qq in su or (str(qq) in su):
                await sd(matcher, '超级用户不能被踢')
                continue
            await bot.set_group_kick(group_id=event.group_id, user_id=int(qq), reject_add_request=False)
        await log_fi(matcher, '踢人操作执行完毕')
    except ActionFailed:
        await fi(matcher, '权限不足')

kick_ = on_command('黑', priority=2, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)
@kick_.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    """
    黑 @user 踢出并拉黑某人
    """
    if not sb or 'all' in sb:
        await fi(matcher, '指令不正确 或 不能含有@全体成员')
    try:
        for qq in sb:
            if qq == event.user_id:
                await sd(matcher, '你在玩一种很新的东西，不能踢自己!')
                continue
            if qq in su or (str(qq) in su):
                await sd(matcher, '超级用户不能被踢')
                continue
            await bot.set_group_kick(group_id=event.group_id, user_id=int(qq), reject_add_request=True)
        await log_fi(matcher, '踢人并拉黑操作执行完毕')
    except ActionFailed:
        await fi(matcher, '权限不足')

set_g_admin = on_command('管理员+', aliases={'加管理', '管理加', '加管理员', '管理员加', 'gl+', 'gly+'}, priority=2, block=True, permission=SUPERUSER | GROUP_OWNER)
@set_g_admin.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    """
    管理员+ @user 添加群管理员
    """
    if not sb or 'all' in sb:
        await fi(matcher, '指令不正确 或 不能含有@全体成员')
    try:
        for qq in sb:
            await bot.set_group_admin(group_id=event.group_id, user_id=int(qq), enable=True)
        await log_fi(matcher, '设置管理员操作成功')
    except ActionFailed:
        await fi(matcher, '权限不足')

unset_g_admin = on_command('管理员-', aliases={'减管理', '管理减', '减管理员', '管理员减',  'gl-', 'gly-'}, priority=2, block=True, permission=SUPERUSER | GROUP_OWNER)
@unset_g_admin.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    """
    管理员+ @user 添加群管理员
    """
    if not sb or 'all' in sb:
        await fi(matcher, '指令不正确 或 不能含有@全体成员')
    try:
        for qq in sb:
            await bot.set_group_admin(group_id=event.group_id, user_id=int(qq), enable=False)
        await log_fi(matcher, '取消管理员操作成功')
    except ActionFailed:
        await fi(matcher, '权限不足')

set_essence = on_command("加精", priority=2, aliases={'加精', 'set_essence'}, block=True,
                         permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)
@set_essence.handle()
async def _(bot: Bot, rp = Depends(msg_reply)):
    if rp: await bot.call_api(api='set_essence_msg', message_id=rp)

del_essence = on_command("取消精华", priority=2, aliases={'取消加精', 'del_essence'}, block=True,
                         permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)
@del_essence.handle()
async def _(bot: Bot, rp = Depends(msg_reply)):
    if rp: await bot.call_api(api='delete_essence_msg', message_id=rp)

msg_recall = on_command('撤回', priority=2, aliases={'recall'}, block=True,
                        permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)
@msg_recall.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, msg: str = Depends(msg_text),
            sb: list = Depends(msg_at), rp = Depends(msg_reply)):
    # by: @tom-snow
    """
    指令格式:
    /撤回 @user n
    回复指定消息时撤回该条消息；使用艾特时撤回被艾特的人在本群 n*19 历史消息内的所有消息。
    不输入 n 则默认 n = 5
    """
    recall_msg_id = []
    if rp:
        recall_msg_id.append(rp)
    elif sb:
        seq = None
        if len(msg.split(' ')) > 1:
            try:  # counts = n
                counts = int(msg.split(' ')[-1])
            except ValueError:
                counts = 5  # 出现错误就默认为 5 【理论上除非是 /撤回 @user n 且 n 不是数值时才有可能触发】
        else:
            counts = 5

        try:
            for _ in range(counts):  # 获取 n 次
                await asyncio.sleep(randint(0, 5))  # 睡眠随机时间，避免黑号
                res = await bot.call_api('get_group_msg_history', group_id=event.group_id, message_seq=seq)  # 获取历史消息
                flag = True
                for message in res['messages']:  # 历史消息列表
                    if flag:
                        seq = int(message['message_seq']) - 1
                        flag = False
                    if int(message['user_id']) in sb:  # 将消息id加入列表
                        recall_msg_id.append(int(message['message_id']))
        except ActionFailed as e:
            await log_sd(matcher, '获取群历史消息时发生错误', f"获取群历史消息时发生错误：{e}, seq: {seq}", err=True)
            print_exc()
    else:
        await fi(matcher,
                 '指令格式：\n/撤回 @user n\n回复指定消息时撤回该条消息；使用艾特时撤回被艾特的人在本群 n*19 历史消息内的所有消息。\n不输入 n 则默认 n = 5')

    # 实际进行撤回的部分
    if recall_msg_id:
        try:
            for msg_id in recall_msg_id:
                await asyncio.sleep(randint(0, 2))  # 睡眠随机时间，避免黑号
                await bot.delete_msg(message_id=msg_id)
            await log_fi(matcher, f"操作成功，一共撤回了 {len(recall_msg_id)} 条消息")
        except ActionFailed as e:
            await log_fi(matcher, '撤回失败', f"撤回失败 {e}")
    else:
        pass
