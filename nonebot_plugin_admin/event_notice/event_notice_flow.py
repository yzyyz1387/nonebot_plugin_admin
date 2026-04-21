from __future__ import annotations

import asyncio
from datetime import datetime

from nonebot.adapters.onebot.v11 import (
    Bot,
    Event,
    GroupAdminNoticeEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupUploadNoticeEvent,
    HonorNotifyEvent,
    LuckyKingNotifyEvent,
    Message,
    MessageSegment,
    PokeNotifyEvent,
)
from nonebot.typing import T_State


async def is_poke(_: Bot, event: Event, __: T_State) -> bool:
    """
    处理 is_poke 的业务逻辑
    :param _: _ 参数
    :param event: 事件对象
    :param __: __ 参数
    :return: bool
    """
    return isinstance(event, PokeNotifyEvent) and event.is_tome()


async def is_honor(_: Bot, event: Event, __: T_State) -> bool:
    """
    处理 is_honor 的业务逻辑
    :param _: _ 参数
    :param event: 事件对象
    :param __: __ 参数
    :return: bool
    """
    return isinstance(event, HonorNotifyEvent)


async def is_upload(_: Bot, event: Event, __: T_State) -> bool:
    """
    处理 is_upload 的业务逻辑
    :param _: _ 参数
    :param event: 事件对象
    :param __: __ 参数
    :return: bool
    """
    return isinstance(event, GroupUploadNoticeEvent)


async def is_user_decrease(_: Bot, event: Event, __: T_State) -> bool:
    """
    处理 is_user_decrease 的业务逻辑
    :param _: _ 参数
    :param event: 事件对象
    :param __: __ 参数
    :return: bool
    """
    return isinstance(event, GroupDecreaseNoticeEvent)


async def is_user_increase(_: Bot, event: Event, __: T_State) -> bool:
    """
    处理 is_user_increase 的业务逻辑
    :param _: _ 参数
    :param event: 事件对象
    :param __: __ 参数
    :return: bool
    """
    return isinstance(event, GroupIncreaseNoticeEvent)


async def is_admin_change(_: Bot, event: Event, __: T_State) -> bool:
    """
    处理 is_admin_change 的业务逻辑
    :param _: _ 参数
    :param event: 事件对象
    :param __: __ 参数
    :return: bool
    """
    return isinstance(event, GroupAdminNoticeEvent)


async def is_red_packet(_: Bot, event: Event, __: T_State) -> bool:
    """
    处理 is_red_packet 的业务逻辑
    :param _: _ 参数
    :param event: 事件对象
    :param __: __ 参数
    :return: bool
    """
    return isinstance(event, LuckyKingNotifyEvent)


def get_avatar_url(user_id: int) -> str:
    """
    获取avatar地址
    :param user_id: 用户号
    :return: str
    """
    return f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"


async def build_honor_message(bot: Bot, event: HonorNotifyEvent) -> str:
    """
    构建honor消息
    :param bot: Bot 实例
    :param event: 事件对象
    :return: str
    """
    honor_labels = {
        "performer": "群聊之火",
        "emotion": "快乐源泉",
    }
    member = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
    name = member.get("card") or member.get("nickname") or str(event.user_id)
    if event.honor_type == "talkative":
        return "新龙王诞生，原来是我自己~" if int(event.user_id) == int(bot.self_id) else f"恭喜 {name} 获得龙王标识"
    label = honor_labels.get(event.honor_type)
    return f"恭喜 {name} 获得【{label}】标识" if label else ""


async def build_member_decrease_message(bot: Bot, event: GroupDecreaseNoticeEvent) -> Message:
    """
    构建成员decrease消息
    :param bot: Bot 实例
    :param event: 事件对象
    :return: Message
    """
    user_info = await bot.get_stranger_info(user_id=event.user_id)
    user_name = user_info.get("nickname") or str(event.user_id)
    if int(event.operator_id or 0) <= 0 or int(event.operator_id) == int(event.user_id):
        return Message([MessageSegment.text(f"成员变动\n{user_name} 离开了本群")])

    operator = await bot.get_group_member_info(group_id=event.group_id, user_id=event.operator_id)
    operator_name = operator.get("card") or operator.get("nickname") or str(event.operator_id)
    event_time = datetime.fromtimestamp(event.time).strftime("%Y-%m-%d %H:%M:%S")

    if event.operator_id != event.user_id:
        return Message(
            [
                MessageSegment.text(f"成员变动\n{operator_name} 送走了 {user_name}\n{event_time}\n"),
                MessageSegment.image(get_avatar_url(event.user_id)),
            ]
        )

    return Message([MessageSegment.text(f"成员变动\n{user_name} 离开了本群")])


async def build_member_increase_message(bot: Bot, event: GroupIncreaseNoticeEvent) -> Message:
    """
    构建成员increase消息
    :param bot: Bot 实例
    :param event: 事件对象
    :return: Message
    """
    await asyncio.sleep(1)
    member = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
    name = member.get("card") or member.get("nickname") or str(event.user_id)
    return Message(
        [
            MessageSegment.text("成员变动\n欢迎 "),
            MessageSegment.at(event.user_id),
            MessageSegment.text(f" 加入，{name}\n"),
            MessageSegment.image(get_avatar_url(event.user_id)),
        ]
    )


async def build_admin_change_message(bot: Bot, event: GroupAdminNoticeEvent) -> str:
    """
    构建管理员change消息
    :param bot: Bot 实例
    :param event: 事件对象
    :return: str
    """
    member = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
    name = member.get("card") or member.get("nickname") or str(event.user_id)
    if int(event.user_id) == int(bot.self_id):
        name = "我"
    if event.sub_type == "set":
        return f"管理员变动\n恭喜 {name} 成为管理员"
    return f"管理员变动\n{name} 不再是本群管理员"
