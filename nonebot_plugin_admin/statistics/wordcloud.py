# python3
# -*- coding: utf-8 -*-

from pathlib import Path

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER

from ..core import path as admin_path
from ..core.exact_command import exact_command
from .wordcloud_generate_flow import prepare_group_wordcloud_payload, render_wordcloud_image
from .wordcloud_resource_flow import build_mask_deprecation_message

CLOUD_ALIASES = {"词云", "wordcloud"}
UPDATE_MASK_ALIASES = {"下载mask"}

cloud = on_command("群词云", aliases=CLOUD_ALIASES, rule=exact_command("群词云", CLOUD_ALIASES), priority=2, block=True)
update_mask = on_command(
    "更新mask",
    aliases=UPDATE_MASK_ALIASES,
    rule=exact_command("更新mask", UPDATE_MASK_ALIASES),
    priority=2,
    block=True,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@update_mask.handle()
async def _(matcher: Matcher):
    await matcher.finish(build_mask_deprecation_message())


@cloud.handle()
async def _(event: GroupMessageEvent):
    try:
        import jieba
    except ModuleNotFoundError:
        await cloud.finish("未安装 jieba 依赖，无法生成词云。")

    group_id = str(event.group_id)
    ok, payload, stop_words = await prepare_group_wordcloud_payload(group_id, jieba)
    if not ok:
        await cloud.finish(payload)

    img_path = Path(admin_path.re_img_path / f"wordcloud_{group_id}.png")
    success, result = await render_wordcloud_image(
        payload,
        stop_words=stop_words,
        img_path=img_path,
        group_id=group_id,
    )
    if success:
        await cloud.send(MessageSegment.image(result))
    else:
        await cloud.send(result)
