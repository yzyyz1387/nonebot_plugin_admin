# python3
# -*- coding: utf-8 -*-

from nonebot.plugin import on_notice

from ..core.utils import fi
from .event_notice_flow import (
    build_admin_change_message,
    build_honor_message,
    build_member_decrease_message,
    build_member_increase_message,
    is_admin_change,
    is_honor,
    is_poke,
    is_red_packet,
    is_upload,
    is_user_decrease,
    is_user_increase,
)

poke = on_notice(is_poke, priority=50)
honor = on_notice(is_honor, priority=50)
upload_files = on_notice(is_upload, priority=50)
user_decrease = on_notice(is_user_decrease, priority=50)
user_increase = on_notice(is_user_increase, priority=50)
admin_change = on_notice(is_admin_change, priority=50)
red_packet = on_notice(is_red_packet, priority=50)


@poke.handle()
async def _():
    return


@honor.handle()
async def _(bot, event, matcher):
    message = await build_honor_message(bot, event)
    if message:
        await fi(matcher, message)


@upload_files.handle()
async def _():
    return


@user_decrease.handle()
async def _(bot, event, matcher):
    await fi(matcher, await build_member_decrease_message(bot, event))


@user_increase.handle()
async def _(bot, event, matcher):
    await fi(matcher, await build_member_increase_message(bot, event))


@admin_change.handle()
async def _(bot, event, matcher):
    await fi(matcher, await build_admin_change_message(bot, event))


@red_packet.handle()
async def _():
    return
