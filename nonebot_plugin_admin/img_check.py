# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/2/5 16:25
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : img_check.py
# @Software: PyCharm
from nonebot import logger, on_message
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.matcher import Matcher
from nonebot.params import Depends

from .message import *
from .path import *
from .utils import mute_sb, image_moderation_async, get_user_violation, sd, fi

find_pic = on_message(priority=2, block=False)
@find_pic.handle()
async def check_pic(bot: Bot, matcher: Matcher, event: GroupMessageEvent, img_lst: list = Depends(msg_img)):
    uid = [event.get_user_id()]
    gid = event.group_id
    for img in img_lst:
        # result = await pic_ban_cof(url = img)
        result = await image_moderation_async(img)
        try:
            if result and result['Suggestion'] != 'Pass':
                if result['Score'] >= 90:
                    if result['Label'] == 'Porn':
                        level = await get_user_violation(gid, event.user_id, 'Porn', event.raw_message)
                        await sd(matcher, f"你的违规等级为{level}，色色不规范，群主两行泪，请群友小心驾驶")
                        await send_pics_ban(bot, event, time_scop_map[level])
                    else:
                        level = (await get_user_violation(gid, event.user_id, 'Porn', event.raw_message, add_=False))
                        logger.info(f"{uid}发送的内容涉及{result['Label']}, 分值{result['Score']}, 违规等级{level}级")
                        # await sd(find_pic, f"你发送的内容涉及{result['Label']}\n你的违规等级为{level}级，网络并非法外之地，请谨言慎行！", True)
                        # await send_pics_ban(bot, event, scope = time_scop_map[level])
                        # FIXME 上面的发送出来有点烦，下面：90分以上除了色图在此处理
                elif result['Score'] <= 90 and result['Label'] == 'Porn':
                    # 地低于90分的色色内容
                    await fi(matcher, '色色不规范，群主两行泪，请群友小心驾驶')
                else:
                    # 低于90的其他内容
                    pass
        except TypeError:
            logger.error("请求图片安全接口失败")

async def send_pics_ban(bot: Bot, event: GroupMessageEvent, scope: list = None):
    """
    发送违规图片，禁言用户
    :param bot:
    :param event:
    :param scope: 时间范围
    """
    gid = event.group_id
    uid = [event.user_id]
    eid = event.message_id
    try:
        await bot.delete_msg(message_id=eid)
        logger.info('检测到违规图片，撤回成功')
    except ActionFailed:
        logger.info('检测到违规图片，但权限不足，撤回失败')
    baning = mute_sb(bot, gid, lst=uid, scope=scope)
    async for baned in baning:
        if baned:
            try:
                await baned
                await bot.send(event=event, message='发送了违规图片,现对你进行处罚,有异议请联系管理员', at_sender=True)
                logger.info(f"检测到违规图片，禁言操作成功，用户: {uid[0]}")
            except ActionFailed:
                logger.info('检测到违规图片，但权限不足，禁言失败')
