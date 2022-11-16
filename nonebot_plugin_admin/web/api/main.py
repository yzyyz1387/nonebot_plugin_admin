# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/9/9 3:04
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : main.py
# @Software: PyCharm
import nonebot
from fastapi import FastAPI, Request, Response, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from tortoise.contrib.fastapi import register_tortoise
from tortoise import Tortoise
from tortoise.exceptions import ConfigurationError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pathlib import Path
from .models.group_models import *
from .utils.tools import creatClass, copyFile
from .routers import group, switcher, msg

# app = FastAPI()
app = nonebot.get_app()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# dirs = []
# models_dir = Path(__file__).parent / "models"
# bot_models_dir = Path() / "admin_db_models"
# for file in models_dir.iterdir():
#     if file.is_file():
#         dirs.append(models_dir / file.name)
#
# if not Path.exists(bot_models_dir):
#     Path.mkdir(bot_models_dir)
#     for file in dirs:
#         copyFile(file, bot_models_dir / file.name)
#
# if bot_models_dir.iterdir() != models_dir.iterdir():
#     for file in dirs:
#         copyFile(file, bot_models_dir / file.name)

register_tortoise(
                app,
                # modules={"models": ["admin_db_models.group_models", "admin_db_models.user_models"]},
                # generate_schemas=True,
                # add_exception_handlers=True,
                config={
                  'connections': {
                      'default': "sqlite://admin.db",
                  },
                  'apps': {
                      'models': {
                          "models": ["admin_db_models.group_models", "admin_db_models.user_models"],
                          'default_connection': 'default',
                      }
                  },
                  "use_tz": False,
                  "timezone": "Asia/Shanghai"

                }
            )

app.include_router(group.router)
app.include_router(switcher.router)
app.include_router(msg.router)


@app.get("/")
async def root():
    return {"message": "this server is for nonebot_plugin_admin"}

# import uvicorn
#
# uvicorn.run(app="src.plugins.admin.web.api.main:app",
#             host="127.0.0.1",
#             port=8000,
#             reload=True,
#             debug=True)
