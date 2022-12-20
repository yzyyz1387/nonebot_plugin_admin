# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/9/9 3:01
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : group_models.py
# @Software: PyCharm
from typing import Optional

from tortoise import fields
from tortoise.models import Model
from tortoise.exceptions import IntegrityError, OperationalError

from pydantic import BaseModel


class Group(Model):
    """群聊类基础模型"""
    group_id = fields.BigIntField(pk=True, unique=True, description="群号")
    group_name = fields.TextField(default="", description="群名")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

    class Base(BaseModel):
        group_id: int
        group_name: Optional[str] = None
        create_time: str = None
        update_time: str = None

    @classmethod
    async def add_this_group(cls, group_id: int, group_name: Optional[str]) -> bool:
        """添加当前群聊"""
        if not group_name:
            group_name = ""
        try:
            group = await cls.create(group_id=group_id, group_name=group_name)
            return True
        except IntegrityError:
            return False

    @classmethod
    async def del_this_group(cls, group_id: int):
        """删除当前群聊"""
        group = await cls.filter(group_id=group_id).first()
        await group.delete()

    @classmethod
    async def update_this_group(cls, group_id: int, group_name: Optional[str] = None):
        """更新群信息"""
        if group_name:
            group = await cls.filter(group_id=group_id).first()
            group.group_name = group_name
            await group.save()

    @classmethod
    async def get_this_group(cls, group_id: int) -> "Group":
        """获取当前群聊"""
        group = await cls.filter(group_id=group_id).first()
        return group

    @classmethod
    async def get_all_group(cls):
        """获取所有群聊"""
        group = await cls.all()
        return group


class Switcher(Group):
    """开关"""
    admin = fields.BooleanField(default=True)
    requests = fields.BooleanField(default=True)
    wordcloud = fields.BooleanField(default=True)
    auto_ban = fields.BooleanField(default=False)
    img_check = fields.BooleanField(default=False)
    word_analyze = fields.BooleanField(default=True)

    class Base(BaseModel):
        admin: bool = True
        requests: bool = True
        wordcloud: bool = True
        auto_ban: bool = False
        img_check: bool = False
        word_analyze: bool = True

    @classmethod
    async def add_this_group(cls, group_id: int, group_name: str, admin: bool = True, requests: bool = True,
                             wordcloud: bool = True, auto_ban: bool = False, img_check: bool = False,
                             word_analyze: bool = True) -> bool:
        """添加当前群聊"""
        if not group_name:
            group_name = ""
        try:
            group = await cls.create(group_id=group_id, group_name=group_name, admin=admin, requests=requests,
                                     wordcloud=wordcloud, auto_ban=auto_ban, img_check=img_check,
                                     word_analyze=word_analyze)
            return True
        except IntegrityError:
            return False

    @classmethod
    async def update_this_group(cls, group_id: int, group_name: Optional[str] = None, **kwargs):
        """更新群信息"""
        group = await cls.filter(group_id=group_id).first()
        if not group_name:
            group_name = ""
        if group:
            group.group_name = group_name
            for key, value in kwargs.items():
                setattr(group, key, value)
            await group.save()
        else:
            await cls.add_this_group(group_id, group_name)


class Message(Group):
    id = fields.IntField(pk=True, unique=True)
    group_id = fields.IntField(pk=False, unique=False, description="群号")
    msg = fields.TextField(default="", description="消息")
    user = fields.IntField(default=0, description="发送者")
    msg_type = fields.TextField(default="text", description="消息类型")

    @classmethod
    async def get_this_group(cls, group_id: int):
        """获取当前群聊"""
        group = await cls.filter(group_id=group_id).all()
        return group

    @classmethod
    async def get_this_user(cls, user: int, group_id: int = None, sort: str = "no_sort"):
        """
        获取当前用户所有消息记录
        :param user: 用户id
        :param group_id: 群号
        :param sort: 排序方式 [no_sort, default, reverse]
        :return:
        """
        user_msg = await cls.filter(user=user).all()
        if sort:
            if sort not in ["no_sort", "default", "reverse"]:
                raise ValueError("sort参数错误")
        if group_id:
            if sort == "no_sort":
                user_msg = await cls.filter(user=user, group_id=group_id).all()
            elif sort == "default":
                user_msg = await cls.filter(user=user, group_id=group_id).all().order_by("update_time")
            elif sort == "reverse":
                user_msg = await cls.filter(user=user, group_id=group_id).all().order_by("-update_time")
        else:
            if sort == "default":
                user_msg = await cls.filter(user=user).all().order_by("update_time")
            elif sort == "reverse":
                user_msg = await cls.filter(user=user).all().order_by("-update_time")
        return user_msg

    @classmethod
    async def add_msg(cls, group_id: int, msg: str, user: int, msg_type: str):
        """添加消息"""
        try:
            await cls.create(group_id=group_id, msg=msg, user=user, msg_type=msg_type)
            return True
        except IntegrityError:
            return False
