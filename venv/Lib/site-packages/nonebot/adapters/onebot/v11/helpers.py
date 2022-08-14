"""OneBot v11 流程辅助。

FrontMatter:
    sidebar_position: 7
    description: onebot.v11.helpers 模块
"""

import re
import asyncio
from enum import IntEnum, auto
from collections import defaultdict
from asyncio import get_running_loop
from typing import Any, Dict, List, Union, Optional, DefaultDict

from nonebot.matcher import Matcher
from nonebot.params import Depends, EventMessage

from .bot import Bot
from .message import Message, MessageSegment
from .event import Event, MessageEvent, GroupMessageEvent


def extract_image_urls(message: Message) -> List[str]:
    """提取消息中的图片链接

    参数:
        message: 消息对象

    返回:
        图片链接列表
    """
    return [
        segment.data["url"]
        for segment in message
        if (segment.type == "image") and ("url" in segment.data)
    ]


def ImageURLs(prompt: Optional[str] = None):
    """提取消息中图片链接`extract_image_urls`的依赖注入版本

    参数:
        prompt: 当不存在图片链接时发送给用户的错误消息. 默认为 `None`.
    """

    async def dependency(
        matcher: Matcher, message: Message = EventMessage()
    ) -> List[str]:
        urls = extract_image_urls(message)
        if not urls and prompt:
            await matcher.finish(prompt)
        return urls

    return Depends(dependency)


NUMBERS_REGEXP = re.compile(r"[+-]?(\d*\.?\d+|\d+\.?\d*)")


def extract_numbers(message: Message) -> List[float]:
    """提取消息中的数字

    参数:
        message: 消息对象

    返回:
        数字列表, 可以是浮点数或整数
    """ """"""
    return [
        float(matched)
        for matched in NUMBERS_REGEXP.findall(message.extract_plain_text())
    ]


def Numbers(prompt: Optional[str] = None) -> List[float]:
    """提取消息中的数字`extract_numbers`的依赖注入版本

    参数:
        prompt: 当不存在数字时发送给用户的错误消息.
    """

    async def dependency(
        matcher: Matcher, message: Message = EventMessage()
    ) -> List[float]:
        numbers = extract_numbers(message)
        if not numbers and prompt:
            await matcher.finish(prompt)
        return numbers

    return Depends(dependency)


CHINESE_AGREE_WORD = {
    "要",
    "用",
    "是",
    "好",
    "对",
    "嗯",
    "行",
    "ok",
    "okay",
    "yeah",
    "yep",
    "当真",
    "当然",
    "必须",
    "可以",
    "肯定",
    "没错",
    "确定",
    "确认",
}
CHINESE_DECLINE_WORD = {
    "不",
    "不要",
    "不用",
    "不是",
    "否",
    "不好",
    "不对",
    "不行",
    "别",
    "no",
    "nono",
    "nonono",
    "nope",
    "不ok",
    "不可以",
    "不能",
}
CHINESE_TRAILING_WORD = ",.!?~，。！？～了的呢吧呀啊呗啦"


def convert_chinese_to_bool(message: Union[Message, str]) -> Optional[bool]:
    """将中文中表示判断的词语转换为布尔值

    参数:
        message: 消息对象或消息文本

    返回:
        是表达同意的布尔值, 如果无法确认判断的词语, 则返回 `None`
    """
    text = message.extract_plain_text() if isinstance(message, Message) else message
    text = text.lower().strip().replace(" ", "").rstrip(CHINESE_TRAILING_WORD)

    if text in CHINESE_AGREE_WORD:
        return True
    if text in CHINESE_DECLINE_WORD:
        return False
    return None


def remove_empty_lines(
    message: Union[Message, str], include_stripped: bool = False
) -> str:
    """移除消息中的空行

    参数:
        message: 消息对象或消息文本
        include_stripped: 是否包含只有空格的行

    返回:
        移除空行后的消息文本
    """ """"""
    text = message.extract_plain_text() if isinstance(message, Message) else message
    return "".join(
        line
        for line in text.splitlines(keepends=False)
        if bool(line.strip() if include_stripped else line)
    )


CHINESE_CANCELLATION_WORDS = {"算", "别", "不", "停", "取消"}
CHINESE_CANCELLATION_REGEX_1 = re.compile(r"^那?[算别不停]\w{0,3}了?吧?$")
CHINESE_CANCELLATION_REGEX_2 = re.compile(r"^那?(?:[给帮]我)?取消了?吧?$")


def is_cancellation(message: Union[Message, str]) -> bool:
    """判断消息是否表示取消

    参数:
        message: 消息对象或消息文本

    返回:
        是否表示取消的布尔值
    """ """"""
    text = message.extract_plain_text() if isinstance(message, Message) else message
    return any(kw in text for kw in CHINESE_CANCELLATION_WORDS) and bool(
        CHINESE_CANCELLATION_REGEX_1.match(text)
        or CHINESE_CANCELLATION_REGEX_2.match(text)
    )


def HandleCancellation(cancel_prompt: Optional[str] = None) -> bool:
    """检查消息是否表示取消`is_cancellation`的依赖注入版本

    参数:
        cancel_prompt: 当消息表示取消时发送给用户的取消消息
    """ """"""

    async def dependency(matcher: Matcher, message: Message = EventMessage()) -> bool:
        cancelled = is_cancellation(message)
        if cancelled and cancel_prompt:
            await matcher.finish(cancel_prompt)
        return not cancelled

    return Depends(dependency)


class CooldownIsolateLevel(IntEnum):
    """命令冷却的隔离级别"""

    GLOBAL = auto()
    """全局使用同一个冷却计时"""
    GROUP = auto()
    """群组内使用同一个冷却计时"""
    USER = auto()
    """按用户使用同一个冷却计时"""
    GROUP_USER = auto()
    """群组内每个用户使用同一个冷却计时"""


def Cooldown(
    cooldown: float = 5,
    *,
    prompt: Optional[str] = None,
    isolate_level: CooldownIsolateLevel = CooldownIsolateLevel.USER,
    parallel: int = 1,
) -> None:
    """依赖注入形式的命令冷却

    用法:
        ```python
        @matcher.handle(parameterless=[Cooldown(cooldown=11.4514, ...)])
        async def handle_command(matcher: Matcher, message: Message):
            ...
        ```

    参数:
        cooldown: 命令冷却间隔
        prompt: 当命令冷却时发送给用户的提示消息
        isolate_level: 命令冷却的隔离级别, 参考 `CooldownIsolateLevel`
        parallel: 并行执行的命令数量
    """
    if not isinstance(isolate_level, CooldownIsolateLevel):
        raise ValueError(
            f"invalid isolate level: {isolate_level!r}, "
            "isolate level must use provided enumerate value."
        )
    running: DefaultDict[str, int] = defaultdict(lambda: parallel)

    def increase(key: str, value: int = 1):
        running[key] += value
        if running[key] >= parallel:
            del running[key]
        return

    async def dependency(matcher: Matcher, event: MessageEvent):
        loop = get_running_loop()

        if isolate_level is CooldownIsolateLevel.GROUP:
            key = str(
                event.group_id
                if isinstance(event, GroupMessageEvent)
                else event.user_id,
            )
        elif isolate_level is CooldownIsolateLevel.USER:
            key = str(event.user_id)
        elif isolate_level is CooldownIsolateLevel.GROUP_USER:
            key = (
                f"{event.group_id}_{event.user_id}"
                if isinstance(event, GroupMessageEvent)
                else str(event.user_id)
            )
        else:
            key = CooldownIsolateLevel.GLOBAL.name

        if running[key] <= 0:
            await matcher.finish(prompt)
        else:
            running[key] -= 1
            loop.call_later(cooldown, lambda: increase(key))
        return

    return Depends(dependency)


async def autorevoke_send(
    bot: Bot,
    event: Event,
    message: Union[str, Message, MessageSegment],
    at_sender: bool = False,
    revoke_interval: int = 60,
    **kwargs,
) -> asyncio.TimerHandle:
    """发出消息指定时间后自动撤回

    参数:
        bot: 实例化的Bot类
        event: 事件对象
        message: 消息对象或消息文本
        at_sender: 是否在消息中添加 @ 用户
        revoke_interval: 撤回消息的间隔时间, 单位为秒

    返回:
        asyncio.TimerHandle: [`TimerHandle`](https://docs.python.org/zh-cn/3/library/asyncio-eventloop.html#asyncio.TimerHandle) 对象, 可以用来取消定时撤回任务
    """
    message_data: Dict[str, Any] = await bot.send(
        event, message, at_sender=at_sender, **kwargs
    )
    message_id: int = message_data["message_id"]

    loop = get_running_loop()
    return loop.call_later(
        revoke_interval,
        lambda: loop.create_task(bot.delete_msg(message_id=message_id)),
    )
