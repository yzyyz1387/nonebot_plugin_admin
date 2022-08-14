"""OneBot v11 权限辅助。

FrontMatter:
    sidebar_position: 6
    description: onebot.v11.permission 模块
"""

from nonebot.permission import Permission

from .event import GroupMessageEvent, PrivateMessageEvent


async def _private(event: PrivateMessageEvent) -> bool:
    return True


async def _private_friend(event: PrivateMessageEvent) -> bool:
    return event.sub_type == "friend"


async def _private_group(event: PrivateMessageEvent) -> bool:
    return event.sub_type == "group"


async def _private_other(event: PrivateMessageEvent) -> bool:
    return event.sub_type == "other"


PRIVATE: Permission = Permission(_private)
""" 匹配任意私聊消息类型事件"""
PRIVATE_FRIEND: Permission = Permission(_private_friend)
"""匹配任意好友私聊消息类型事件"""
PRIVATE_GROUP: Permission = Permission(_private_group)
"""匹配任意群临时私聊消息类型事件"""
PRIVATE_OTHER: Permission = Permission(_private_other)
"""匹配任意其他私聊消息类型事件"""


async def _group(event: GroupMessageEvent) -> bool:
    return True


async def _group_member(event: GroupMessageEvent) -> bool:
    return event.sender.role == "member"


async def _group_admin(event: GroupMessageEvent) -> bool:
    return event.sender.role == "admin"


async def _group_owner(event: GroupMessageEvent) -> bool:
    return event.sender.role == "owner"


GROUP: Permission = Permission(_group)
"""匹配任意群聊消息类型事件"""
GROUP_MEMBER: Permission = Permission(_group_member)
"""匹配任意群员群聊消息类型事件

:::warning 警告
该权限通过 event.sender 进行判断且不包含管理员以及群主！
:::
"""
GROUP_ADMIN: Permission = Permission(_group_admin)
"""匹配任意群管理员群聊消息类型事件"""
GROUP_OWNER: Permission = Permission(_group_owner)
"""匹配任意群主群聊消息类型事件"""

__all__ = [
    "PRIVATE",
    "PRIVATE_FRIEND",
    "PRIVATE_GROUP",
    "PRIVATE_OTHER",
    "GROUP",
    "GROUP_MEMBER",
    "GROUP_ADMIN",
    "GROUP_OWNER",
]
