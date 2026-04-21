from __future__ import annotations

import asyncio
import json
import random
from typing import Awaitable, Callable, Literal

import requests
from nonebot import get_bots
from nonebot.log import logger

from ..core.func_hook import check_func_status
from .group_message_config import GroupMessageConfig

Period = Literal["morning", "night"]


def fetch_hitokoto_message(request_get: Callable[[str], object] = requests.get) -> str:
    """
    拉取hitokoto消息
    :param request_get: request_get 参数
    :return: str
    """
    response = request_get("https://v1.hitokoto.cn?c=a&c=b&c=c&c=d&c=h")
    data = json.loads(response.text)
    message = data["hitokoto"]
    suffix = ""
    if works := data.get("from"):
        suffix += f"《{works}》"
    if from_who := data.get("from_who"):
        suffix += f"{from_who}"
    if suffix:
        message += f"\n——{suffix}"
    return message


def build_group_message_content(
    config: GroupMessageConfig,
    period: Period,
    *,
    choice_func: Callable[[list[str]], str] = random.choice,
    hitokoto_fetcher: Callable[[], str] = fetch_hitokoto_message,
) -> str | None:
    """
    构建群消息内容
    :param config: 配置字典
    :param period: period 参数
    :param choice_func: choice_func 参数
    :param hitokoto_fetcher: hitokoto_fetcher 参数
    :return: str | None
    """
    if config.mode == 1:
        sentences = config.morning_sentences if period == "morning" else config.night_sentences
        if not sentences:
            logger.error(f"{period} 自定义消息为空，跳过发送")
            return None
        return choice_func(sentences)
    return hitokoto_fetcher()


async def send_group_messages_once(
    config: GroupMessageConfig,
    period: Period,
    *,
    bots_provider: Callable[[], dict] = get_bots,
    status_checker: Callable[[str, str], Awaitable[bool]] = check_func_status,
    choice_func: Callable[[list[str]], str] = random.choice,
    hitokoto_fetcher: Callable[[], str] = fetch_hitokoto_message,
) -> int:
    """
    发送群消息once
    :param config: 配置字典
    :param period: period 参数
    :param bots_provider: bots_provider 参数
    :param status_checker: status_checker 参数
    :param choice_func: choice_func 参数
    :param hitokoto_fetcher: hitokoto_fetcher 参数
    :return: int
    """
    content = build_group_message_content(config, period, choice_func=choice_func, hitokoto_fetcher=hitokoto_fetcher)
    if content is None:
        return 0

    sent_count = 0
    for bot in bots_provider().values():
        for group_id in config.group_ids:
            if not await status_checker("group_msg", group_id):
                continue
            try:
                await bot.send_group_msg(group_id=group_id, message=content)
                sent_count += 1
            except Exception:
                pass
    return sent_count


async def run_group_message_job(
    config: GroupMessageConfig,
    period: Period,
    *,
    bots_provider: Callable[[], dict] = get_bots,
    status_checker: Callable[[str, str], Awaitable[bool]] = check_func_status,
    choice_func: Callable[[list[str]], str] = random.choice,
    hitokoto_fetcher: Callable[[], str] = fetch_hitokoto_message,
    sleep_func: Callable[[float], Awaitable[None]] = asyncio.sleep,
    delay_func: Callable[[], int] = lambda: random.randint(1, 10),
) -> bool:
    """
    执行群消息job
    :param config: 配置字典
    :param period: period 参数
    :param bots_provider: bots_provider 参数
    :param status_checker: status_checker 参数
    :param choice_func: choice_func 参数
    :param hitokoto_fetcher: hitokoto_fetcher 参数
    :param sleep_func: sleep_func 参数
    :param delay_func: delay_func 参数
    :return: bool
    """
    enabled = config.morning_enabled if period == "morning" else config.night_enabled
    if not enabled:
        logger.info(f"send_{period}()关闭，跳出函数")
        return False

    send_success = False
    while not send_success:
        try:
            await sleep_func(delay_func())
            await send_group_messages_once(
                config,
                period,
                bots_provider=bots_provider,
                status_checker=status_checker,
                choice_func=choice_func,
                hitokoto_fetcher=hitokoto_fetcher,
            )
            logger.info("群聊推送消息")
            send_success = True
        except ValueError as err:
            logger.error("ValueError:{}", err)
            logger.error("群聊推送消息插件获取 bot 失败，1s 后重试")
            await sleep_func(1)
    return True
