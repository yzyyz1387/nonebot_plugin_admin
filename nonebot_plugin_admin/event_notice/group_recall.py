from __future__ import annotations

from nonebot import logger, on_message, on_notice
from nonebot.adapters.onebot.v11 import GroupMessageEvent, GroupRecallNoticeEvent

from ..core.config import global_config
from .anti_recall_flow import build_recall_message, should_forward_recall
from .recall_archive_store import archive_group_message_snapshot, load_recalled_message_snapshot

su = global_config.superusers

group_recall = on_notice(priority=5)
group_recall_archive = on_message(priority=4, block=False)


async def resolve_recalled_message(bot, group_id: int, message_id: int):
    """
    解析recalled消息
    :param bot: Bot 实例
    :param group_id: 群号
    :param message_id: 标识值
    :return: None
    """
    recalled_message = await load_recalled_message_snapshot(group_id, message_id)
    if recalled_message is not None:
        return recalled_message
    return await bot.get_msg(message_id=message_id)


@group_recall_archive.handle()
async def _(event: GroupMessageEvent):
    await archive_group_message_snapshot(event)


@group_recall.handle()
async def _(bot, event: GroupRecallNoticeEvent):
    operator_info = await bot.get_group_member_info(group_id=event.group_id, user_id=event.operator_id, no_cache=True)
    if not should_forward_recall(event.user_id, event.operator_id, operator_info["role"], su):
        return

    try:
        recalled_message = await resolve_recalled_message(bot, event.group_id, event.message_id)
    except Exception as err:
        logger.warning(f"防撤回：获取消息内容失败 message_id={event.message_id}: {type(err).__name__}: {err}")
        operator_name = operator_info.get("card") or operator_info.get("nickname") or str(operator_info["user_id"])
        await bot.send_group_msg(
            group_id=event.group_id,
            message=f"检测到 {operator_name}({operator_info['user_id']}) 撤回了一条消息（消息内容获取失败：{type(err).__name__}）",
        )
        return

    if not recalled_message:
        logger.warning(f"防撤回：get_msg 返回空数据 message_id={event.message_id}")
        operator_name = operator_info.get("card") or operator_info.get("nickname") or str(operator_info["user_id"])
        await bot.send_group_msg(
            group_id=event.group_id,
            message=f"检测到 {operator_name}({operator_info['user_id']}) 撤回了一条消息（消息内容获取失败）",
        )
        return

    await bot.send_group_msg(
        group_id=event.group_id,
        message=build_recall_message(operator_info, recalled_message),
    )
