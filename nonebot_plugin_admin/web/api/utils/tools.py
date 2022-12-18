# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/9/15 5:56
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : tools.py
# @Software: PyCharm

async def creatClass(prefix, group_id, extend_class):
    this_Message = type(f"{prefix}{group_id}", (extend_class,), {})
    this_msg_obj = this_Message()
    return this_msg_obj


def copyFile(origin, target):
    with open(origin, "rb") as f, open(target, "wb") as f2:
            f2.write(f.read())
