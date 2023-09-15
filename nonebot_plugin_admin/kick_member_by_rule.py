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
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment, MessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, ArgStr, CommandArg

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
    k_prompt = ['等级(数字)：\n例如：2 则踢出等级 ≤ 2 的成员 \n★=1 ☾=4 ☀=16\n输入“取消”取消操作\n 请等待...',
                '最后发言时间(8位日期)：\n例如：20230912 则踢出2023-09-12后未发言的成员 \n输入“取消”取消操作\n 请等待...']
    if k_category in ["1", "2"]:
        await kick_by_rule.send(k_prompt[int(k_category) - 1])
    else:
        await kick_by_rule.reject("输入错误, 请重新输入:")


@kick_by_rule.got('k_level', prompt='请输入:')
async def _(
        bot: Bot,
        event: GroupMessageEvent,
        state: T_State,
        k_level=ArgStr()
):
    await kick_by_rule.send("请坐和放宽，轮询成员信息中，这可能会花费几分钟...")
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

            kick_list = [qq for qq, level in level_dic.items() if 0 < level <= int(k_level)]
            zero_level_list = [qq for qq, level in level_dic.items() if level == 0]
            state['zero_level_list'] = zero_level_list
            send_0_tips = f"0级成员：\n"
            for qq in zero_level_list:
                send_0_tips += f"{qq} "
            send_0_tips += "\n0级成员可能是未获取到等级信息，不做处理\n"
            await kick_by_rule.send(send_0_tips)

            # for qq, level in level_dic.items():
            #     logger.info(f"{qq}:{level}级")
            #     if level <= int(k_level):
            #         kick_list.append(qq)
            #         logger.info(qq <= level)

            send_text = f"将踢出等级 ≤ {k_level} 的成员:\n"
            for qq in kick_list:
                send_text += f"【{qq}】 【{level_dic[qq]}级】\n"
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


@kick_by_rule.got('confirm', prompt='确定执行吗:\n1：确定\n2: 取消')
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    confirm = str(state['confirm'])
    if confirm == "1":
        await kick_by_rule.send("正在踢出...")
    else:
        await kick_by_rule.finish("已取消操作...")


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


get_by_qq = on_command("/get", priority=1, permission=GROUP_OWNER | SUPERUSER)


# 测试
# @get_by_qq.handle()
# async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
#     if qq := args.extract_plain_text():
#         info = await bot.get_stranger_info(user_id=int(qq))
#         await get_by_qq.finish(str(info))
#     else:
#         await get_by_qq.finish("PSE INPUT ARG")


async def get_qq_lever(bot: Bot, qq: int):
    return (await bot.get_stranger_info(user_id=qq, no_cache=True))['level']


# TODO 踢出确认（got('comfirm')）、0级如何处理
