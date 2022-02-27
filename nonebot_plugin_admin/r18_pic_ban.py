# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/2/5 16:25
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : r18_pic_ban.py
# @Software: PyCharm
from nonebot import logger, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from .utils import banSb, image_moderation_async, check_func_status

find_pic = on_message(priority=2, block=False)


@find_pic.handle()
async def check_pic(bot: Bot, event: GroupMessageEvent):
    uid = [event.get_user_id()]
    gid = event.group_id
    eid = event.message_id
    if isinstance(event, MessageEvent):
        for msg in event.message:
            if msg.type == "image":
                status = await check_func_status("img_check", str(gid))
                if status:
                    url: str = msg.data["url"]
                    image_ = url
                    # result = await pic_ban_cof(url=image_)
                    result = (await image_moderation_async(image_))
                    if not result["status"]:
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
                        logger.info('检测到违规内容')
                    elif result["status"] == 'error':
                        logger.info(f"图片检测失败{result['message']}")
                    elif result["status"]:
                        logger.info(f"图片安全")
                else:
                    pass
