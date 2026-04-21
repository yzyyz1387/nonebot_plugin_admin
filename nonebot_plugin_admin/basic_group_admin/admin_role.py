# python3
# -*- coding: utf-8 -*-

from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.permission import Permission

from ..approval.approval_store import g_admin_async


async def _deputy_admin(event: GroupMessageEvent) -> bool:
    """
    处理 _deputy_admin 的业务逻辑
    :param event: 事件对象
    :return: bool
    """
    admins = await g_admin_async()
    gid = str(event.group_id)
    if admins.get(gid):
        return event.user_id in admins[gid]
    return False


DEPUTY_ADMIN: Permission = Permission(_deputy_admin)
TITLE_SELF_SERVICE: Permission = Permission(lambda: True)
