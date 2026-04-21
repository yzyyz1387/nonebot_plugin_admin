# python3
# -*- coding: utf-8 -*-

from nonebot import logger, on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.params import Depends

from ..core.message import msg_img
from .image_guard_flow import is_image_guard_suspended

find_pic = on_message(priority=2, block=False)


@find_pic.handle()
async def check_pic(event: GroupMessageEvent, img_lst: list = Depends(msg_img)):
    """图片审核暂时挂起，仅保留 matcher 注册位。"""
    if not img_lst:
        return

    if is_image_guard_suspended():
        logger.debug(f"图片审核已挂起，跳过本次图片消息处理: group_id={event.group_id} user_id={event.user_id}")
        return
