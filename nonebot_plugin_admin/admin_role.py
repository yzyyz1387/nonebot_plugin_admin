# python3
# -*- coding: utf-8 -*-
# @Time    : 2023/1/19 3:34
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : admin_role.py
# @Software: PyCharm


from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.internal.permission import Permission as Permission

from .approve import g_admin


async def _deputy_admin(event: GroupMessageEvent) -> bool:
    admins = g_admin()
    gid = str(event.group_id)
    if admins.get(gid):
        return event.user_id in admins[gid]

DEPUTY_ADMIN: Permission = Permission(_deputy_admin)
"""匹配分管事件"""
