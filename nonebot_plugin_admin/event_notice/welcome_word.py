from __future__ import annotations

from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from ..statistics.config_orm_store import (
    orm_delete_group_welcome_word,
    orm_get_group_welcome_word,
    orm_save_group_welcome_word,
)


EXIT_WORDS = {"0", "取消", "退出"}
CONFIRM_WORDS = {"1", "确认"}
DATABASE_UNAVAILABLE_MESSAGE = "欢迎词数据库不可用，请检查 ORM 配置后重试。"


async def get_welcome_word(group_id: int) -> str | None:
    return await orm_get_group_welcome_word(str(group_id))


async def save_welcome_word(group_id: int, word: str) -> bool:
    return await orm_save_group_welcome_word(str(group_id), word)


async def delete_welcome_word(group_id: int) -> bool:
    return await orm_delete_group_welcome_word(str(group_id))


welcome_word_set = on_command(
    "欢迎词+",
    priority=2,
    block=True,
    permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
)


@welcome_word_set.handle()
async def _(event: GroupMessageEvent, matcher: Matcher, state: T_State, args: Message = CommandArg()):
    word = str(args).strip()
    if not word:
        await matcher.finish("请输入欢迎词内容。")

    old_word = await get_welcome_word(event.group_id)
    if old_word is None:
        await matcher.finish(DATABASE_UNAVAILABLE_MESSAGE)
    state["welcome_word"] = word
    state["welcome_group_id"] = event.group_id
    if old_word:
        await matcher.send(
            f"本群已有欢迎词“{old_word}”，确认覆盖吗？\n"
            "回复【1 / 确认】以覆盖\n"
            "回复【0 / 取消 / 退出】来退出。"
        )
        await matcher.pause()

    if not await save_welcome_word(event.group_id, word):
        await matcher.finish(DATABASE_UNAVAILABLE_MESSAGE)
    await matcher.finish("本群欢迎词已设置。")


@welcome_word_set.handle()
async def _(event: GroupMessageEvent, matcher: Matcher, state: T_State):
    if "welcome_word" not in state:
        return
    reply = event.get_plaintext().strip()
    if reply in EXIT_WORDS:
        await matcher.finish("已取消设置欢迎词。")
    if reply not in CONFIRM_WORDS:
        await matcher.reject("请回复【1 / 确认】以覆盖，或回复【0 / 取消 / 退出】来退出。")
    if not await save_welcome_word(state["welcome_group_id"], state["welcome_word"]):
        await matcher.finish(DATABASE_UNAVAILABLE_MESSAGE)
    await matcher.finish("本群欢迎词已覆盖。")


welcome_word_delete = on_command(
    "欢迎词-",
    priority=2,
    block=True,
    permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
)


@welcome_word_delete.handle()
async def _(event: GroupMessageEvent, matcher: Matcher, state: T_State):
    word = await get_welcome_word(event.group_id)
    if word is None:
        await matcher.finish(DATABASE_UNAVAILABLE_MESSAGE)
    if not word:
        await matcher.finish("本群尚未设置欢迎词。")
    state["welcome_group_id"] = event.group_id
    await matcher.send(
        f"本群已有欢迎词“{word}”，确认删除吗？\n"
        "回复【1、确认】以删除\n"
        "回复【0 / 取消 / 退出】来退出。"
    )
    await matcher.pause()


@welcome_word_delete.handle()
async def _(event: GroupMessageEvent, matcher: Matcher, state: T_State):
    if "welcome_group_id" not in state:
        return
    reply = event.get_plaintext().strip()
    if reply in EXIT_WORDS:
        await matcher.finish("已取消删除欢迎词。")
    if reply not in CONFIRM_WORDS:
        await matcher.reject("请回复【1、确认】以删除，或回复【0 / 取消 / 退出】来退出。")
    if not await delete_welcome_word(state["welcome_group_id"]):
        await matcher.finish(DATABASE_UNAVAILABLE_MESSAGE)
    await matcher.finish("本群欢迎词已删除。")
