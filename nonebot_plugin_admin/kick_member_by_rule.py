# python3
# -*- coding: utf-8 -*-
# @Time    : 2023-09-13 0:05
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : kick_member_by_rule.py
# @Software: PyCharm
import asyncio
import datetime
from random import randint

from nonebot import on_command, logger, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, ArgStr

from nonebot.typing import T_State
from nonebot.permission import SUPERUSER
from .admin_role import DEPUTY_ADMIN

from .config import global_config
from .utils import At, MsgText, banSb, change_s_title, fi, log_fi, sd, Reply, log_sd

su = global_config.superusers

kick_by_rule = on_command('成员清理', priority=1, block=True,
                          permission=SUPERUSER | GROUP_OWNER)


@kick_by_rule.got('k_category', prompt='请输入要清理方式(数字)：\n1、等级 \n2、最后发言时间 \n输入“取消”取消操作')
async def _(
        event: GroupMessageEvent,
        state: T_State,
        k_category=ArgStr(),
):
    k_category = str(k_category)
    if k_category in ["取消", "算了"]:
        await kick_by_rule.finish("已取消操作...")
    k_prompt = ['等级(数字)：\n例如：2 则踢出等级 ≤ 2 的成员 \n★=1 ☾=4 ☀=16\n输入“取消”取消操作',
                '最后发言时间(8位日期)：\n例如：20230912 则踢出2023-09-12后未发言的成员 \n输入“取消”取消操作']
    if k_category in ["1", "2"]:
        await kick_by_rule.send(k_prompt[int(k_category) - 1])
    else:
        await kick_by_rule.reject("输入错误, 请重新输入:")


@kick_by_rule.got('k_level', prompt='请输入（注意，此为危险操作，且不可逆，满足条件会被立刻踢出）：')
async def _(
        bot: Bot,
        event: GroupMessageEvent,
        state: T_State,
        k_level=ArgStr()
):
    await kick_by_rule.send("请坐和放宽，正在查询中，这可能会花费几分钟...")
    k_level = str(k_level)
    kick_list = []
    if k_level in ["取消", "算了"]:
        await kick_by_rule.finish("已取消操作...")
    else:
        member_list = await bot.get_group_member_list(group_id=event.group_id)
        category = str(state['k_category'])
        qq_list = [member['user_id'] for member in member_list]
        if category == "1":
            # 获取所有成员等级
            level_dic = {}
            for qq in qq_list:
                level_dic[qq] = (await get_qq_lever(bot, qq))
            kick_list = [qq for qq, level in level_dic.items() if level <= int(k_level)]

            send_text = f"将踢出等级 ≤ {k_level} 的成员:\n"
            for qq in kick_list:
                send_text += "【" + MessageSegment.at(qq) + f"】【{qq}】【{level_dic[qq]}级】\n"
            await kick_by_rule.send(send_text)
        elif category == "2":
            last_send_list = {}
            k_level = str(k_level)
            for member in member_list:
                last_send_list[member['user_id']] = member['last_sent_time']
            # logger.info(f"last_send_list: {last_send_list}")
            try:
                if len(k_level) != 8:
                    raise ValueError
                input_time = datetime.datetime.strptime(k_level, "%Y%m%d")
                now_time = datetime.datetime.now()
                if input_time > now_time:
                    await kick_by_rule.reject("日期不能大于当前日期, 请重新输入:")
                for qq, last in last_send_list.items():
                    try:
                        if datetime.datetime.fromtimestamp(last) < input_time:
                            kick_list.append(qq)
                    except ValueError:
                        pass
            except ValueError:
                await kick_by_rule.finish("日期格式错误")
        else:
            kick_by_rule.reject("输入错误, 请重新输入:")
        if kick_list:
            # 保存踢出列表
            state['kick_list'] = kick_list
            # logger.info(f"kick_list: {kick_list}")
            if len(member_list) - len(kick_list) <= 3:
                await kick_by_rule.finish("踢出后群人数将少于3人, 已取消操作...")
        else:
            kick_by_rule.finish("没有满足条件的成员")


async def get_qq_lever(bot: Bot, qq: int):
    return (await bot.get_stranger_info(user_id=qq, no_cache=True))['level']


@kick_by_rule.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    kick_list = state['kick_list']
    if kick_list:
        await kick_by_rule.send("尝试采用随机时间间隔清理，执行完毕会发出提示...")
        success = []
        fail = []
        for qq in kick_list:
            try:
                await asyncio.sleep(randint(0, 5))  # 睡眠随机时间，避免黑号
                await bot.set_group_kick(group_id=event.group_id, user_id=qq)
                # await bot.send_group_msg(group_id=event.group_id, message=f"T{qq}") # 测试用
                success.append(qq)
            except ActionFailed as e:
                logger.error(f"{qq}-踢出失败")
                fail.append(qq)
        if success:
            await kick_by_rule.send(f"踢出成功：{success}")
        if fail:
            await kick_by_rule.send(f"踢出失败：{fail}")

    else:
        await kick_by_rule.send("没有需要踢出的成员, 已取消操作...")
