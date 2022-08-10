import random
from asyncio import sleep
from pathlib import Path

from nonebot import get_driver, on_request, on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent, \
    MessageSegment, Message

from nonebot_plugin_admin.hello.utils.config import config
from nonebot_plugin_admin.hello.utils.message_util import MessageBuild

#群欢迎部分


superuser = int(list(get_driver().config.superusers)[0])

requests_handle = on_request(priority=5, block=True)
notice_handle = on_notice(priority=5, block=True)


@notice_handle.handle()
async def GroupNewMember(bot: Bot, event: GroupIncreaseNoticeEvent):
    greet_emoticon = MessageBuild.Image(Path() / 'resources' / 'LittlePaimon' / 'emoticons' / '派蒙-干杯.png', mode='RGBA')
    if event.user_id == event.self_id:
        await sleep(random.randint(4, 8))
        await bot.send_group_msg(group_id=event.group_id, message=Message(
            MessageSegment.text('旅行者们大家好呀~，这里是小派蒙，对我说help查看帮助吧~\n')))
    elif event.group_id not in config.paimon_greet_ban:
        await sleep(random.randint(4, 8))
        await bot.send_group_msg(group_id=event.group_id, message=Message(
            MessageSegment.at(event.user_id) + MessageSegment.text("欢迎新旅行者哦~\n")))
