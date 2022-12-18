# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/9/15 6:03
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : middleware.py
# @Software: PyCharm
from ..main import app
from fastapi import FastAPI, Request
from tortoise.exceptions import OperationalError
from fastapi.responses import JSONResponse


@app.exception_handler(OperationalError)
async def exception_middleware(request: Request, exc: OperationalError):
    return JSONResponse(content={"error": str(exc)})


@app.exception_handler(Exception)
async def exception_middleware(request: Request, exc: Exception):
    return JSONResponse(content={"error": str(exc)})