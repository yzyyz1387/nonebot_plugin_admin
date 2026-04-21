# python3
# -*- coding: utf-8 -*-

import asyncio
from random import randint
from traceback import print_exc

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.permission import SUPERUSER

from .admin_role import DEPUTY_ADMIN
from ..core.config import global_config
from ..core.message import msg_at, msg_reply, msg_text
from ..core.utils import change_s_title, fi, log_fi, log_sd, mute_sb, sd

su = global_config.superusers

ban = on_command("禁", priority=2, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)


@ban.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, msg: str = Depends(msg_text), sb: list = Depends(msg_at)):
    try:
        msg = msg.replace(" ", "").replace("禁", "")
        time = int("".join(map(str, map(int, filter(lambda x: x.isdigit(), msg)))))
    except ValueError:
        time = None
    if sb:
        baning = mute_sb(bot, event.group_id, lst=sb, time=time)
        try:
            async for baned in baning:
                if baned:
                    await baned
            await log_fi(matcher, "禁言操作成功" if time is not None else "用户已被禁言随机时长")
        except ActionFailed:
            await fi(matcher, "权限不足")


unban = on_command("解", priority=2, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)


@unban.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    if sb:
        baning = mute_sb(bot, event.group_id, lst=sb, time=0)
        try:
            async for baned in baning:
                if baned:
                    await baned
            await log_fi(matcher, "解禁操作成功")
        except ActionFailed:
            await fi(matcher, "权限不足")


ban_all = on_command("/all", priority=2, aliases={"/全员"}, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)


@ban_all.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, msg: str = Depends(msg_text)):
    enable = not (msg and "解" in str(msg))
    try:
        await bot.set_group_whole_ban(group_id=event.group_id, enable=enable)
        await log_fi(matcher, f"全体操作成功: {'禁言' if enable else '解禁'}")
    except ActionFailed:
        await fi(matcher, "权限不足")


change = on_command("改", priority=2, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)


@change.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, msg: str = Depends(msg_text), sb: list = Depends(msg_at)):
    if sb:
        try:
            for user_ in sb:
                await bot.set_group_card(group_id=event.group_id, user_id=int(user_), card=msg.split()[-1:][0])
            await log_fi(matcher, "改名片操作成功")
        except ActionFailed:
            await fi(matcher, "权限不足")


title = on_command("头衔", priority=2, block=True)


@title.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, msg: str = Depends(msg_text), sb: list = Depends(msg_at)):
    s_title = msg.replace(" ", "").replace("头衔", "", 1)
    gid = event.group_id
    uid = event.user_id
    if not sb or (len(sb) == 1 and sb[0] == uid):
        await change_s_title(bot, matcher, gid, uid, s_title)
    elif "all" not in sb:
        if uid in su or str(uid) in su:
            for qq in sb:
                await change_s_title(bot, matcher, gid, int(qq), s_title)
        else:
            await fi(matcher, "超级用户才可以更改他人头衔，更改自己头衔请直接使用【头衔 xxx】")
    else:
        await fi(matcher, "不能含有@全体成员")


title_ = on_command("删头衔", priority=2, block=True)


@title_.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    gid = event.group_id
    uid = event.user_id
    if not sb or (len(sb) == 1 and sb[0] == uid):
        await change_s_title(bot, matcher, gid, uid, "")
    elif "all" not in sb:
        if uid in su or str(uid) in su:
            for qq in sb:
                await change_s_title(bot, matcher, gid, int(qq), "")
        else:
            await fi(matcher, "超级用户才可以删他人头衔，删除自己头衔请直接使用【删头衔】")
    else:
        await fi(matcher, "不能含有@全体成员")


kick = on_command("踢", priority=2, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)


@kick.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    if not sb or "all" in sb:
        await fi(matcher, "指令不正确 或 不能含有@全体成员")
    try:
        for qq in sb:
            if qq == event.user_id:
                await sd(matcher, "你在玩一种很新的东西，不能踢自己!")
                continue
            if qq in su or str(qq) in su:
                await sd(matcher, "超级用户不能被踢")
                continue
            await bot.set_group_kick(group_id=event.group_id, user_id=int(qq), reject_add_request=False)
        await log_fi(matcher, "踢人操作执行完毕")
    except ActionFailed:
        await fi(matcher, "权限不足")


kick_ = on_command("黑", priority=2, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)


@kick_.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    if not sb or "all" in sb:
        await fi(matcher, "指令不正确 或 不能含有@全体成员")
    try:
        for qq in sb:
            if qq == event.user_id:
                await sd(matcher, "你在玩一种很新的东西，不能踢自己!")
                continue
            if qq in su or str(qq) in su:
                await sd(matcher, "超级用户不能被踢")
                continue
            await bot.set_group_kick(group_id=event.group_id, user_id=int(qq), reject_add_request=True)
        await log_fi(matcher, "踢人并拉黑操作执行完毕")
    except ActionFailed:
        await fi(matcher, "权限不足")


set_g_admin = on_command("管理员+", aliases={"加管理", "管理加", "加管理员", "管理员加"}, priority=2, block=True, permission=SUPERUSER | GROUP_OWNER)


@set_g_admin.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    if not sb or "all" in sb:
        await fi(matcher, "指令不正确 或 不能含有@全体成员")
    try:
        for qq in sb:
            await bot.set_group_admin(group_id=event.group_id, user_id=int(qq), enable=True)
        await log_fi(matcher, "设置管理员操作成功")
    except ActionFailed:
        await fi(matcher, "权限不足")


unset_g_admin = on_command("管理员-", aliases={"减管理", "管理减", "减管理员", "管理员减"}, priority=2, block=True, permission=SUPERUSER | GROUP_OWNER)


@unset_g_admin.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, sb: list = Depends(msg_at)):
    if not sb or "all" in sb:
        await fi(matcher, "指令不正确 或 不能含有@全体成员")
    try:
        for qq in sb:
            await bot.set_group_admin(group_id=event.group_id, user_id=int(qq), enable=False)
        await log_fi(matcher, "取消管理员操作成功")
    except ActionFailed:
        await fi(matcher, "权限不足")


set_essence = on_command("加精", priority=2, aliases={"set_essence"}, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)


@set_essence.handle()
async def _(bot: Bot, rp=Depends(msg_reply)):
    if rp:
        await bot.call_api(api="set_essence_msg", message_id=rp)


del_essence = on_command("取消精华", priority=2, aliases={"取消加精", "del_essence"}, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)


@del_essence.handle()
async def _(bot: Bot, rp=Depends(msg_reply)):
    if rp:
        await bot.call_api(api="delete_essence_msg", message_id=rp)


msg_recall = on_command("撤回", priority=2, aliases={"recall"}, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN)


@msg_recall.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, msg: str = Depends(msg_text), sb: list = Depends(msg_at), rp=Depends(msg_reply)):
    recall_msg_id = []
    if rp:
        recall_msg_id.append(rp)
    elif sb:
        if len(msg.split(" ")) > 1:
            try:
                counts = int(msg.split(" ")[-1])
            except ValueError:
                counts = 5
        else:
            counts = 5

        seq = None
        try:
            for _ in range(counts):
                await asyncio.sleep(randint(0, 5))
                res = await bot.call_api("get_group_msg_history", group_id=event.group_id, message_seq=seq)
                flag = True
                for message in res["messages"]:
                    if flag:
                        seq = int(message["message_seq"]) - 1
                        flag = False
                    if int(message["user_id"]) in sb:
                        recall_msg_id.append(int(message["message_id"]))
        except ActionFailed as e:
            await log_sd(matcher, "获取群历史消息时发生错误", f"获取群历史消息时发生错误：{e}, seq: {seq}", err=True)
            print_exc()
    else:
        await fi(
            matcher,
            "指令格式：\n/撤回 @user n\n回复指定消息时撤回该条消息；使用艾特时撤回被艾特的人在本群 n*19 历史消息内的所有消息。\n不输入 n 则默认 n = 5",
        )

    if recall_msg_id:
        try:
            for msg_id in recall_msg_id:
                await asyncio.sleep(randint(0, 2))
                await bot.delete_msg(message_id=msg_id)
            await log_fi(matcher, f"操作成功，一共撤回了 {len(recall_msg_id)} 条消息")
        except ActionFailed as e:
            await log_fi(matcher, "撤回失败", f"撤回失败 {e}")
