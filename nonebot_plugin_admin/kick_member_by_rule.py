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

from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER
from nonebot.internal.matcher import Matcher
from nonebot.params import ArgStr
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from .config import global_config
from .path import *

su = global_config.superusers
global level_dic, last_send_dict


def make_send(kick_list: list, category: str, data_dict: dict):
    """
    :param kick_list: 踢出列表
    :param category: 踢出条件
    :param data_dict: 踢出列表对应的数据字典
    :return: 生成的发送文本
    根据踢出列表和踢出条件生成发送文本
    """
    kick_c_index = int(category) - 1
    prompt = [["将踢出等级 ≤", " 的成员:\n", "等级:"], ["将踢出在 ", "之后未发言的成员:\n", "最后："]]
    send_text = prompt[kick_c_index][0] + category + prompt[kick_c_index][1]
    if kick_list:
        for qq in kick_list:
            send_text += f"{qq}： {prompt[kick_c_index][2]}{data_dict[qq] if category == '1' else datetime.datetime.fromtimestamp(data_dict[qq])}\n"
    else:
        send_text += "没有满足条件的成员, 已取消操作..."
    return send_text


async def get_qq_lever(bot: Bot, qq: int):
    """
    :param bot: bot
    :param qq: qq号
    :return: qq等级
    获取qq等级
    """
    return (await bot.get_stranger_info(user_id=qq, no_cache=True))['level']


async def finish_Matcher(matcher: Matcher, state: T_State, event: GroupMessageEvent, arg: str):
    """
    :param matcher: Matcher
    :param state: T_State
    :param event: GroupMessageEvent
    :param arg: 输入词
    :return: None
    结束Matcher
    """
    if arg in ["取消", "算了", "退出", "结束"]:
        state['this_lock'].unlink()
        await matcher.finish("已取消操作...")


kick_by_rule = on_command('成员清理', priority=1, block=True,
                          permission=SUPERUSER | GROUP_OWNER)


@kick_by_rule.got('k_category', prompt='请输入要清理方式(数字)：\n1、等级 \n2、最后发言时间 \n输入“取消”取消操作')
async def _(
        event: GroupMessageEvent,
        matcher: Matcher,
        state: T_State,
        k_category=ArgStr(),
):
    this_lock: Path = kick_lock_path / f"{event.group_id}.lock"
    state['this_lock'] = this_lock
    if this_lock.exists():
        await kick_by_rule.finish("当前群组已有成员清理任务正在执行，如需手动解锁，请输入【清理解锁】")
    else:
        this_lock.touch()
        k_category = str(k_category)

        await finish_Matcher(matcher, state, event, k_category)

        k_prompt = ['等级(数字)：\n例如：2 则踢出等级 ≤ 2 的成员 \n★=1 ☾=4 ☀=16\n输入“取消”取消操作\n 请等待...',
                    '最后发言时间(8位日期)：\n例如：20230912 则踢出2023-09-12后未发言的成员 \n输入“取消”取消操作\n 请等待...']
        if k_category in ["1", "2"]:
            await kick_by_rule.send(k_prompt[int(k_category) - 1])
        else:
            await kick_by_rule.reject("输入错误, 请重新输入:")


@kick_by_rule.got('kick_condition', prompt='请输入:')
async def _(
        bot: Bot,
        event: GroupMessageEvent,
        matcher: Matcher,
        state: T_State,
        kick_condition=ArgStr()
):
    global level_dic, last_send_dict
    await kick_by_rule.send("请坐和放宽，轮询成员信息中，这可能会花费几分钟...")
    kick_condition = str(kick_condition)
    kick_list = []

    await finish_Matcher(matcher, state, event, kick_condition)

    member_list = await bot.get_group_member_list(group_id=event.group_id)
    category = str(state['k_category'])
    qq_list = [member['user_id'] for member in member_list]
    if category == "1":
        # 获取所有成员等级
        level_dic = {}
        for qq in qq_list:
            level_dic[qq] = (await get_qq_lever(bot, qq))

        kick_list = [qq for qq, level in level_dic.items() if 0 < level <= int(kick_condition)]
        zero_level_list = [qq for qq, level in level_dic.items() if level == 0]
        state['zero_level_list'] = zero_level_list
        send_0_tips = f"0级成员：\n"
        if zero_level_list:
            for qq in zero_level_list:
                send_0_tips += f"{qq} "
            send_0_tips += "\n0级成员可能是未获取到等级信息，不做处理\n"
            await kick_by_rule.send(send_0_tips)

    elif category == "2":
        last_send_dict = {}
        kick_condition = str(kick_condition)
        for member in member_list:
            last_send_dict[member['user_id']] = member['last_sent_time']
        logger.debug(f"last_send_list: {last_send_dict}")
        try:
            if len(kick_condition) != 8:
                raise ValueError
            input_time = datetime.datetime.strptime(kick_condition, "%Y%m%d")
            now_time = datetime.datetime.now()
            if input_time > now_time:
                await kick_by_rule.reject("日期不能大于当前日期, 请重新输入:")
            for qq, last in last_send_dict.items():
                try:
                    logger.debug(f"{qq}：{datetime.datetime.fromtimestamp(last)}")
                    logger.debug(f"{datetime.datetime.fromtimestamp(last) <= input_time}")
                    if datetime.datetime.fromtimestamp(last) <= input_time:
                        kick_list.append(qq)
                except ValueError as e:
                    logger.error(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]{qq}：{e}")
                    pass
        except ValueError:
            await kick_by_rule.reject("日期格式错误, 请重新输入:")
    else:
        kick_by_rule.reject("输入错误, 请重新输入:")
    if kick_list:
        # 保存踢出列表
        state['kick_list'] = kick_list
        logger.debug(f"kick_list: {kick_list}")
        if len(member_list) - len(kick_list) <= 3:
            state['this_lock'].unlink()
            await kick_by_rule.finish("踢出后群人数将少于3人, 已取消操作...")

        else:
            await kick_by_rule.send(
                make_send(
                    kick_list,
                    category,
                    level_dic if category == "1" else last_send_dict
                ))
    else:
        state['this_lock'].unlink()
        await kick_by_rule.finish("没有满足条件的成员, 已取消操作...")


@kick_by_rule.got('confirm', prompt='确定执行吗:\n1：确定\n2: 取消')
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, state: T_State):
    confirm = str(state['confirm'])
    if confirm == "1":
        await kick_by_rule.send("正准备执行...")
    else:
        await finish_Matcher(matcher, state, event, '取消')


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
                logger.debug(f"踢出{qq},操作者：{event.user_id},群：{event.group_id}")
                # await bot.send_group_msg(group_id=event.group_id, message=f"T{qq}") # 测试用
                success.append(qq)
            except ActionFailed as e:
                logger.error(f"{qq}-踢出失败：{e}")
                fail.append(qq)
        if success:
            await kick_by_rule.send(f"踢出成功：{success}")
        if fail:
            await kick_by_rule.send(f"踢出失败：{fail}")

    else:
        await kick_by_rule.send("没有需要踢出的成员, 已取消操作...")


delete_lock_manually = on_command('清理解锁', priority=1, block=True, permission=SUPERUSER | GROUP_OWNER)


@delete_lock_manually.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    this_lock: Path = kick_lock_path / f"{event.group_id}.lock"
    if this_lock.exists():
        this_lock.unlink()
        await delete_lock_manually.finish("已解锁")
    else:
        await delete_lock_manually.finish("当前群组没有成员清理任务正在执行")

# 测试
# get_by_qq = on_command("/get", priority=1, permission=GROUP_OWNER | SUPERUSER)
# @get_by_qq.handle()
# async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
#     if qq := args.extract_plain_text():
#         info = await bot.get_stranger_info(user_id=int(qq))
#         await get_by_qq.finish(str(info))
#     else:
#         await get_by_qq.finish("PSE INPUT ARG")
