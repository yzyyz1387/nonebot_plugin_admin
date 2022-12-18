# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/9/9 6:24
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : user_models.py
# @Software: PyCharm

from tortoise import fields
from tortoise.models import Model
from tortoise.exceptions import IntegrityError


class UserBase(Model):
    uid = fields.BigIntField(pk=True, unique=True, description="用户id")
    points = fields.IntField(default=0, description="积分")
    nickname = fields.TextField(description="昵称")
    register_time = fields.DatetimeField(auto_now_add=True, description="注册时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

    @classmethod
    async def add_user(cls, uid: int, nickname: str) -> bool:
        """添加用户"""
        try:
            user = await cls.create(uid=uid, nickname=nickname)
            return True
        except IntegrityError:
            return False

    @classmethod
    async def del_user(cls, uid: int):
        """删除用户"""
        user = await cls.filter(uid=uid).first()
        await user.delete()

    @classmethod
    async def update_user(cls, uid: int, **kwargs):
        """更新用户信息"""
        user = await cls.filter(uid=uid).first()
        for key, value in kwargs.items():
            setattr(user, key, value)
        await user.save()

    @classmethod
    async def get_user(cls, uid: int) -> "UserBase":
        """获取用户"""
        user = await cls.filter(uid=uid).first()
        return user


