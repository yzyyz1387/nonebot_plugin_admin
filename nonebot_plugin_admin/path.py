# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/2/24 22:23
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : path.py
# @Software: PyCharm
from pathlib import Path

config_path = Path() / "config"
config_admin = config_path / "admin.json"
config_group_admin = config_path / "group_admin.json"
word_path = config_path / "word_config.txt"
words_contents_path = Path() / "config" / "words"
res_path = Path() / "resource"
re_img_path = Path() / "resource" / "imgs"
ttf_name = Path() / "resource" / "msyhblod.ttf"
limit_word_path = config_path / "违禁词.txt"
limit_word_path_easy = config_path / "违禁词_简单.txt"
limit_level = config_path / "违禁词监控等级.json"
switcher_path = config_path / "开关.json"
template_path = config_path / "template"

admin_funcs = {
    "admin": ['管理', '踢', '禁', '改', '基础群管'],
    "requests": ['审批', '加群审批', '加群', '自动审批'],
    "wordcloud": ['群词云', '词云', 'wordcloud'],
    "auto_ban": ['违禁词', '违禁词检测'],
    "img_check": ['图片检测', '图片鉴黄', '涩图检测', '色图检测']
}

funcs_name_cn = ['基础群管', '加群审批', '群词云', '违禁词检测', '图片检测']

