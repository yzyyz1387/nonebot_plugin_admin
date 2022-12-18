# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/9/17 13:12
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : switcher.py
# @Software: PyCharm
from typing import Optional

from fastapi import APIRouter
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from admin_db_models.group_models import *

router = APIRouter(
    prefix="/switcher",
)


@router.get("/")
async def add(group_id: Optional[int] = None):
    """
    查询某 group_id 的开关状态 或 所有群的开关状态
    """
    if group_id:
        switcher = await Switcher.get_this_group(group_id=group_id)
    else:
        switcher = await Switcher.all()
    return switcher


@router.post("/")
async def update(group_id, switch: Switcher.Base, group_name: Optional[str] = None):
    """
    添加或更改群管插件功能开关
    """
    temp_dic = switch.dict()
    try:
        await Switcher.update_this_group(group_id, group_name, **temp_dic)
        status = await Switcher.get_this_group(group_id=group_id)
        return {"message": "操作成功", "status": status}
    except Exception as e:
        return {"message": "操作失败", "error": e}


