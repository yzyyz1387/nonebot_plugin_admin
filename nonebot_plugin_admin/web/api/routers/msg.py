# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/9/17 13:13
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : msg.py
# @Software: PyCharm
from typing import Optional
from fastapi import APIRouter
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from ..models.group_models import *

router = APIRouter(
    prefix="/msg",
)


@router.get("/")
async def msg_(request: Request, group_id: int = None):
    """
    查询某个群的聊天记录
    """
    if group_id:
        return await Message.get_this_group(group_id=group_id)
    else:
        return await Message.get_all_group()


@router.get("/user")
async def user_msg(request: Request, user: int, sort: str = "no_sort", group_id: int = None):
    """
    查询某个群的某个用户的聊天记录,不带group_id参数则返回用户在所有群的聊天记录
    """
    if user:
        if group_id:
            msg = await Message.get_this_user(user=user, group_id=group_id, sort=sort)
            return msg
        else:
            msg = await Message.get_this_user(user=user, sort=sort)
            return msg


@router.get("/last")
async def last_msg(request: Request, group_id: Optional[int] = None):
    """
    查询某个群的最后一条聊天记录，不带参数则返回所有群的最后一条聊天记录
    """
    if group_id:
        msgData = (await Message.get_this_group(group_id=group_id))
        if msgData:
            msg = msgData[-1]
            return msg
        else:
            return {}
    else:
        return (await Message.get_all_group())[-1]


@router.post("/")
async def add_(request: Request, group_id: int, user: int, msg: str, msg_type: str = "text"):
    """
    聊天记录相关,如果不传user和msg则为获取该群聊天记录
    """
    r = await Message.add_msg(group_id=group_id, msg=msg, user=user, msg_type=msg_type)
    return r
