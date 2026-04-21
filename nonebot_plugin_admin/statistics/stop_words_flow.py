from __future__ import annotations

from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from .orm_store import load_group_stop_words, replace_group_stop_words


def _parse_words(args: Message) -> list[str]:
    """
    解析词料
    :param args: 命令参数
    :return: list[str]
    """
    return [word.strip() for word in str(args).split(" ") if word.strip()]


async def handle_add_group_stop_words(group_id: int | str, matcher: Matcher, args: Message = CommandArg()) -> None:
    """
    处理add群stop词料
    :param group_id: 群号
    :param matcher: Matcher 实例
    :param args: 命令参数
    :return: None
    """
    if not args:
        await matcher.finish("请输入添加内容，多个以空格分隔，例如：\n添加停用词 内容1 内容2")

    new_words = _parse_words(args)
    saved_words = await load_group_stop_words(group_id)
    already_add: list[str] = []
    success_add: list[str] = []

    for word in new_words:
        if word in saved_words:
            already_add.append(word)
            continue
        saved_words.append(word)
        success_add.append(word)

    await replace_group_stop_words(group_id, saved_words)

    if already_add:
        await matcher.send(f"{already_add}已存在")
    if success_add:
        await matcher.send(f"{success_add}添加成功")


async def handle_delete_group_stop_words(group_id: int | str, matcher: Matcher, args: Message = CommandArg()) -> None:
    """
    处理delete群stop词料
    :param group_id: 群号
    :param matcher: Matcher 实例
    :param args: 命令参数
    :return: None
    """
    if not args:
        await matcher.finish("请输入删除内容，多个以空格分隔，例如：\n删除停用词 内容1 内容2")

    delete_words = _parse_words(args)
    saved_words = await load_group_stop_words(group_id)
    success_del: list[str] = []
    already_del: list[str] = []
    filtered_words: list[str] = []

    for word in saved_words:
        if word in delete_words:
            success_del.append(word)
        else:
            filtered_words.append(word)

    for word in delete_words:
        if word not in success_del:
            already_del.append(word)

    await replace_group_stop_words(group_id, filtered_words)

    if success_del:
        await matcher.send(f"{success_del}删除成功")
    if already_del:
        await matcher.send(f"{already_del}还不是停用词")
    await matcher.finish()


async def handle_list_group_stop_words(group_id: int | str, matcher: Matcher) -> None:
    """
    处理list群stop词料
    :param group_id: 群号
    :param matcher: Matcher 实例
    :return: None
    """
    saved_words = await load_group_stop_words(group_id)
    if not saved_words:
        await matcher.finish("该群没有停用词")
    await matcher.finish("\n".join(saved_words))
