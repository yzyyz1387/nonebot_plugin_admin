# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/9/17 13:08
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : group.py
# @Software: PyCharm
from typing import Optional
from pathlib import Path
from nonebot import logger
from fastapi import APIRouter
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from ..models.group_models import *
router = APIRouter(
    prefix="/group",
)


@router.get("/")
async def index(request: Request, group_id: int = None):
    if not group_id:
        group_info = await Group.get_all_group()
    else:
        group_info = await Group.get_this_group(group_id)
        if not group_info:
            group_info = []
    return group_info


@router.post("/add")
async def add(group_id: int, group_name: Optional[str] = None):
    add_group = await Group.add_this_group(group_id=group_id, group_name=group_name)
    if add_group:
        return {"message": "添加成功"}
    else:
        return {"error": "添加失败"}


@router.post("/del")
async def del_(group_id: int):
    result = await Group.del_this_group(group_id)
    if result:
        return {"message": "删除成功"}
    else:
        return {"error": "删除失败"}
