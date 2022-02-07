# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/2/5 16:25
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : r18_pic_ban.py
# @Software: PyCharm
from nonebot import logger, on_message
from nonebot.adapters.cqhttp import Bot, GroupMessageEvent, MessageEvent
from nonebot.adapters.cqhttp.exception import ActionFailed

from .utils import pic_ban_cof, banSb

find_pic = on_message(priority=2, block=False)


@find_pic.handle()
async def check_pic(bot: Bot, event: GroupMessageEvent):
    uid = [event.get_user_id()]
    gid = event.group_id
    eid = event.message_id
    if isinstance(event, MessageEvent):
        for msg in event.message:
            if msg.type == "image":
                url: str = msg.data["url"]
                image_ = url
                result = await pic_ban_cof(url=image_)
                if result:
                    try:
                        await bot.delete_msg(message_id=eid)
                        logger.info('检测到违规图片，撤回')
                    except ActionFailed:
                        logger.info('检测到违规图片，但权限不足，撤回失败')
                    baning = banSb(gid, ban_list=uid)
                    async for baned in baning:
                        if baned:
                            try:
                                await baned
                            except ActionFailed:
                                await find_pic.finish("检测到违规图片，但权限不足")
                                logger.info('检测到违规图片，但权限不足，禁言失败')
                            else:
                                await bot.send(event=event, message="发送了违规图片,现对你进行处罚,有异议请联系管理员", at_sender=True)
                                logger.info(f"检测到违规图片，禁言操作成功，用户: {uid[0]}")
                    logger.info('检测到涩图')
                else:
                    logger.info("图片安全")
