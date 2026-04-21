import asyncio
from random import randint
from typing import Awaitable, Callable, Optional, Sequence, Union

from nonebot.adapters.onebot.v11 import Bot

Target = Union[str, int]
SleepFunc = Callable[[float], Awaitable[None]]
RandomFunc = Callable[[int, int], int]

DEFAULT_RECALL_COUNT = 5


def normalize_targets(targets: Optional[Sequence[Target]]) -> list[int]:
    """
    规范化targets
    :param targets: targets 参数
    :return: list[int]
    """
    if not targets:
        return []
    return [int(target) for target in targets if str(target) != "all"]


def parse_recall_count(raw_message: str) -> int:
    """
    解析recallcount
    :param raw_message: 原始消息文本
    :return: int
    """
    parts = raw_message.split()
    if len(parts) > 1:
        try:
            return int(parts[-1])
        except ValueError:
            return DEFAULT_RECALL_COUNT
    return DEFAULT_RECALL_COUNT


async def collect_recall_message_ids(
    bot: Bot,
    group_id: int,
    raw_message: str,
    targets: Optional[Sequence[Target]],
    reply_message_id: Optional[int],
    *,
    sleep_func: SleepFunc = asyncio.sleep,
    random_func: RandomFunc = randint,
) -> tuple[list[int], Optional[int]]:
    """
    收集recall消息ids
    :param bot: Bot 实例
    :param group_id: 群号
    :param raw_message: 原始消息文本
    :param targets: targets 参数
    :param reply_message_id: 标识值
    :param sleep_func: sleep_func 参数
    :param random_func: random_func 参数
    :return: tuple[list[int], Optional[int]]
    """
    recall_message_ids: list[int] = []
    if reply_message_id is not None:
        recall_message_ids.append(reply_message_id)
        return recall_message_ids, None

    normalized_targets = normalize_targets(targets)
    if not normalized_targets:
        return recall_message_ids, None

    seq: Optional[int] = None
    for _ in range(parse_recall_count(raw_message)):
        await sleep_func(random_func(0, 5))
        result = await bot.call_api("get_group_msg_history", group_id=group_id, message_seq=seq)
        first_message = True
        for message in result["messages"]:
            if first_message:
                seq = int(message["message_seq"]) - 1
                first_message = False
            if int(message["user_id"]) in normalized_targets:
                recall_message_ids.append(int(message["message_id"]))
    return recall_message_ids, seq


async def recall_messages(
    bot: Bot,
    message_ids: Sequence[int],
    *,
    sleep_func: SleepFunc = asyncio.sleep,
    random_func: RandomFunc = randint,
) -> None:
    """
    处理 recall_messages 的业务逻辑
    :param bot: Bot 实例
    :param message_ids: 标识列表
    :param sleep_func: sleep_func 参数
    :param random_func: random_func 参数
    :return: None
    """
    for message_id in message_ids:
        await sleep_func(random_func(0, 2))
        await bot.delete_msg(message_id=message_id)


