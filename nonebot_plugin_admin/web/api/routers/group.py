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

from admin_db_models import models_version as bot_models_version
from ..utils.tools import copyFile

# FIXME 更改model后这里+1
models_version = 1


def pre_init(enforce: bool = False):
    db_dirs = []
    models_dir = Path(__file__).parent.parent / "models"
    bot_models_dir = Path() / "admin_db_models"

    for file in models_dir.iterdir():
        if file.is_file():
            db_dirs.append(models_dir / file.name)
    if enforce:
        for file in db_dirs:
            copyFile(file, bot_models_dir / file.name)
    else:
        if not Path.exists(bot_models_dir):
            Path.mkdir(bot_models_dir)
            for file in db_dirs:
                copyFile(file, bot_models_dir / file.name)

        if bot_models_dir.iterdir() != models_dir.iterdir():
            for file in db_dirs:
                copyFile(file, bot_models_dir / file.name)
    with open(bot_models_dir / "__init__.py", "a+") as f:
        f.write(f"models_version = {models_version}")
    logger.info("Admin插件 数据库模型初始化完成")


try:
    from admin_db_models.group_models import *
except ModuleNotFoundError:
    pre_init()
    from admin_db_models.group_models import *

if bot_models_version != models_version:
    logger.info("Admin插件 数据库模型版本不一致，正在更新数据库模型")
    pre_init(True)
    from admin_db_models.group_models import *

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
