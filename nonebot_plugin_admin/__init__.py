# python3
# -*- coding: utf-8 -*-
# @Time    : 2021/12/23 0:52
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : __init__.py.py
# @Software: PyCharm

import json
import os

import nonebot
from nonebot import logger, on_notice
from nonebot.adapters.onebot.v11 import Bot, NoticeEvent

from . import (
    admin,
    approve,
    auto_ban,
    auto_ban_,
    broadcast,
    func_hook,
    group_request_verify,
    group_recall,
    img_check,
    notice,
    particular_e_notice,
    requests,
    request_manual,
    word_analyze,
    wordcloud,
    switcher,
    utils,
)
from .path import *
from .switcher import switcher_integrity_check
from .utils import At, Reply, MsgText, banSb, change_s_title, log_sd, sd, fi, log_fi, copyFile, mk, \
    dirs, init

if admin_models_path.exists() and admin_models_init_path.exists():
    from . import web
else:
    db_dirs = []
    models_path = Path(__file__).parent / 'web' / 'api' / 'models'
    from pathlib import Path

    if not admin_models_path.exists():
        os.mkdir(admin_models_path)
    if not admin_models_init_path.exists():
        for file in models_path.iterdir():
            if file.is_file():
                db_dirs.append(models_path / file.name)
        for file in db_dirs:
            copyFile(file, admin_models_path / file.name)
        with open(admin_models_init_path, "a+") as f:
            f.write(f"models_version = 0")
    for i in range(5):
        logger.warning("未找到admin_models文件夹，无法使用admin插件的web功能,正在复制模型以解决此问题，请重启程序")
    pid = os.getpid()
    if os.name == 'nt':
        # Windows系统
        cmd = 'taskkill /pid ' + str(pid) + ' /f'
        try:
            os.system(cmd)
            print(pid, 'killed')
        except Exception as e:
            print(e)
    elif os.name == 'posix':
        # Linux系统
        cmd = 'kill ' + str(pid)
        try:
            os.system(cmd)
            print(pid, 'killed')
        except Exception as e:
            print(e)
    else:
        print('Undefined os.name')

from .group_request_verify import verify
from .config import global_config

su = global_config.superusers

driver = nonebot.get_driver()


@driver.on_bot_connect
async def _():
    await init()
    bot = nonebot.get_bot()
    await switcher_integrity_check(bot)




__usage__ = """
【群管】：
权限：permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER
  禁言:
    禁 @某人 时间（s）[1,2591999]
    禁 时间（s）@某人 [1,2591999]
    禁 @某人 缺省时间则随机
    禁 @某人 0 可解禁
    解 @某人
  全群禁言（好像没用？）
    /all 
    /all 解
  改名片
    改 @某人 名片
  改头衔
    头衔 @某人 头衔
    删头衔
  踢出：
    踢 @某人
  踢出并拉黑：
  黑 @某人
  撤回:
  撤回 (回复某条消息即可撤回对应消息)
  撤回 @user [(可选，默认n = 5)历史消息倍数n] (实际检查的历史数为 n*19)

【管理员】permission = SUPERUSER | GROUP_OWNER
  管理员+ @xxx 设置某人为管理员
  管理员- @xxx 取消某人管理员

【加群自动审批】：
群内发送 permission = GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  查看词条 ： 查看本群审批词条   或/审批
  词条+ [词条] ：增加审批词条 或/审批+
  词条- [词条] ：删除审批词条 或/审批-

【superuser】：
  所有词条 ：  查看所有审批词条   或/su审批
  指定词条+ [群号] [词条] ：增加指定群审批词条 或/su审批+
  指定词条- [群号] [词条] ：删除指定群审批词条 或/su审批-
  自动审批处理结果将发送给superuser

【分群管理员设置】*分管：可以接受加群处理结果消息的用户
群内发送 permission = GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  分管+ [user] ：user可用@或qq 添加分群管理员
  分管- [user] ：删除分群管理员
  查看分管 ：查看本群分群管理员

群内或私聊 permission = SUPERUSER
  所有分管 ：查看所有分群管理员
  群管接收 ：打开或关闭超管消息接收（关闭则审批结果不会发送给superusers）

【群词云统计】
该功能所用库 wordcloud 未写入依赖，请自行安装
群内发送：
  记录本群 ： 开始统计聊天记录 permission = GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  停止记录本群 ：停止统计聊天记录
  群词云 ： 发送词云图片

【被动识别】
涩图检测：将禁言随机时间

违禁词检测：
  支持正则表达式(使用用制表符分隔)
  可定义触发违禁词操作(默认为禁言+撤回)
  可定义生效范围(排除某些群 or 仅限某些群生效)
    示例：
      加(群|君\S?羊|羣)\S*\d{6,}      $撤回$禁言$仅限123456789,987654321
      狗群主                          $禁言$排除987654321

【功能开关】
群内发送：
  开关xx : 对某功能进行开/关  permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER
  开关状态 ： 查看各功能的状态
  xx in ：
    ['管理', '踢', '禁', '改', '基础群管']  #基础功能 踢、禁、改、管理员+-
    ['加群', '审批', '加群审批', '自动审批'] #加群审批
    ['词云', '群词云', 'wordcloud'] #群词云
    ['违禁词', '违禁词检测'] #违禁词检测
    ['图片检测', '图片鉴黄', '涩图检测', '色图检测'] #图片检测
所有功能默认开
"""
__help_plugin_name__ = '简易群管'

__permission__ = 1
__help__version__ = '0.2.0'
