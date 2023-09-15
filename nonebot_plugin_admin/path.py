# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/2/24 22:23
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : path.py
# @Software: PyCharm
from pathlib import Path

# FIXME 群配置文件目前都以配置文件的类型分文件夹，而不是以群分文件夹，后者是不是会更好，但是目前懒得改了
config_path = Path() / 'config'
config_admin = config_path / 'admin.json'
config_group_admin = config_path / 'group_admin.json'
word_path = config_path / 'word_config.txt'
words_contents_path = Path() / 'config' / 'words'
res_path = Path() / 'resource'
re_img_path = Path() / 'resource' / 'imgs'
ttf_name = Path() / 'resource' / 'msyhblod.ttf'
limit_word_path = config_path / '违禁词.txt'
switcher_path = config_path / '开关.json'
template_path = config_path / 'template'
stop_words_path = config_path / 'stop_words'
wordcloud_bg_path = config_path / 'wordcloud_bg'
user_violation_info_path = config_path / '群内用户违规信息'
group_message_data_path = config_path / '群消息数据'
error_path = config_path / 'admin插件错误数据'
broadcast_avoid_path = config_path / '广播排除群聊.json'
kick_lock_path = config_path / 'kick_lock'

admin_funcs = {
    'admin': ['管理', '踢', '禁', '改', '基础群管'],
    'requests': ['审批', '加群审批', '加群', '自动审批'],
    'wordcloud': ['群词云', '词云', 'wordcloud'],
    'auto_ban': ['违禁词', '违禁词检测'],
    'img_check': ['图片检测', '图片鉴黄', '涩图检测', '色图检测'],
    'word_analyze': ['消息记录', '群消息记录', '发言记录'],
    'group_msg': ['早安晚安', '早安', '晚安'],
    'broadcast': ['广播消息', '群广播', '广播'],
    'particular_e_notice': ['事件通知', '变动通知', '事件提醒'],
    'group_recall': ['防撤回', '防止撤回']
}
# TODO 后续在这里对功能加 {‘default': True} 以便于初始化时自动设置开关状态
funcs_name_cn = ['基础群管', '加群审批', '群词云', '违禁词检测', '图片检测']

# 交给Copilot
# 0到5分钟、5到10分钟、10分钟到30分钟、30分钟到10小时、10到24小时、24小时到7天、7天到14天、14天到2591999秒
time_scop_map = {
    0: [0, 5 * 60],
    1: [5 * 60, 10 * 60],
    2: [10 * 60, 30 * 60],
    3: [30 * 60, 10 * 60 * 60],
    4: [10 * 60 * 60, 24 * 60 * 60],
    5: [24 * 60 * 60, 7 * 24 * 60 * 60],
    6: [7 * 24 * 60 * 60, 14 * 24 * 60 * 60],
    7: [14 * 24 * 60 * 60, 2591999]
}