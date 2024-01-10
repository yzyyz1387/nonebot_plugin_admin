# python3
# -*- coding: utf-8 -*-
# @Time    : 2021/12/23 0:52
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : __init__.py.py
# @Software: PyCharm

import nonebot

from . import (
    admin,
    approve,
    auto_ban,
    auto_ban_,
    broadcast,
    func_hook,
    group_msg,
    group_request_verify,
    group_recall,
    img_check,
    kick_member_by_rule,
    notice,
    particular_e_notice,
    requests,
    request_manual,
    word_analyze,
    wordcloud,
    switcher,
    utils,
)
from nonebot.plugin import PluginMetadata
from .config import global_config, Config
from .path import *
from .switcher import switcher_integrity_check
from .utils import At, Reply, MsgText, banSb, change_s_title, log_sd, fi, log_fi, sd, init

su = global_config.superusers
driver = nonebot.get_driver()


@driver.on_bot_connect
async def _(bot: nonebot.adapters.Bot):
    await init()
    await switcher_integrity_check(bot)


__plugin_meta__ = PluginMetadata(
    name="不简易群管",
    description="Nonebot2 群管插件 插件",
    usage="包含踢改禁，头衔，精华操作，图片安全，违禁词识别，发言记录等功能等你探索",
    type="application",
    homepage="https://github.com/yzyyz1387/nonebot_plugin_admin",
    config=Config,
    supported_adapters=None,
)

"""
! 消息防撤回模块，默认不开启，有需要的自行开启，想对部分群生效也需自行实现(可以并入本插件的开关系统内，也可控制 go-cqhttp 的事件过滤器)

如果在 go-cqhttp 开启了事件过滤器，请确保允许 post_type = notice 通行
【至少也得允许 notice_type = group_recall 通行】
"""

__usage__ = """
【初始化】：
  群管初始化 ：初始化插件

【群管】：
权限：permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER
  禁言:
    禁 @某人 时间（s）[1,2591999]
    禁 时间（s）@某人 [1,2591999]
    禁 @某人 缺省时间则随机
    禁 @某人 0 可解禁
    解 @某人
    禁言时，该条消息中所有数字都会组合作为禁言时间，如：‘禁@某人 1哈2哈0哈’，则禁言120s
    
  全群禁言 若命令前缀不为空，请使用//all,若为空，需用 /all 来触发
    /all 
    /all 解
    
  改名片
    改 @某人 名片
    
  踢出：
    踢 @某人
  踢出并拉黑：
   黑 @某人
   
  撤回:
   撤回 (回复某条消息即可撤回对应消息)
   撤回 @user [(可选，默认n=5)历史消息倍数n] (实际检查的历史数为 n*19)
   
  设置精华
    回复某条消息 + 加精
  取消精华
    回复某条消息 + 取消精华
    
【头衔】
  改头衔
    自助领取：头衔 xxx 
    自助删头衔：删头衔
    超级用户更改他人头衔：头衔 @某人 头衔
    超级用户删他人头衔：删头衔 @某人

【管理员】permission=SUPERUSER | GROUP_OWNER
  管理员+ @xxx 设置某人为管理员
  管理员- @xxx 取消某人管理员
  
【加群自动审批】：
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  查看词条 ： 查看本群审批词条   或/审批
  词条+ [词条] ：增加审批词条 或/审批+
  词条- [词条] ：删除审批词条 或/审批-

【superuser】：
  所有词条 ：  查看所有审批词条   或/su审批
  指定词条+ [群号] [词条] ：增加指定群审批词条 或/su审批+
  指定词条- [群号] [词条] ：删除指定群审批词条 或/su审批-
  自动审批处理结果将发送给superuser

【分群管理员设置】*分管：可以接受加群处理结果消息的用户
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  分管+ [user] ：user可用@或qq 添加分群管理员
  分管- [user] ：删除分群管理员
  查看分管 ：查看本群分群管理员

群内或私聊 permission=SUPERUSER
  所有分管 ：查看所有分群管理员
  群管接收 ：打开或关闭超管消息接收（关闭则审批结果不会发送给superusers）
  
【群词云统计】
该功能所用库 wordcloud 未写入依赖，请自行安装
群内发送：
  记录本群 ： 开始统计聊天记录 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  停止记录本群 ：停止统计聊天记录
  群词云 ： 发送词云图片
  更新mask : 更新mask图片
  增加停用词 停用词1 停用词2 ...
  删除停用词 停用词1 停用词2 ...
  停用词列表 ： 查看停用词列表

群发言排行
 - 日:
  - 日榜首：今日榜首, aliases={'今天谁话多', '今儿谁话多', '今天谁屁话最多'}
  - 日排行：今日发言排行, aliases={'今日排行榜', '今日发言排行榜', '今日排行'}
  - 昨日排行
 - 总
  - 总排行：排行, aliases={'谁话多', '谁屁话最多', '排行', '排行榜'}
 - 某人发言数
  - 日：今日发言数@xxx, aliases={'今日发言数', '今日发言', '今日发言量'}
  - 总：发言数@xxx, aliases={'发言数', '发言', '发言量'}
    
  
【被动识别】
涩图检测：
 - 图片检测偏向于涩图检测，90分以上色图禁言，其他基本不处理
 - 用户违禁一次等级+1 最高7级
 - 禁言时间（s）：
  - time_scop_map = {
        0: [0, 5*60],
        1: [5*60, 10*60],
        2: [10*60, 30*60],
        3: [30*60, 10*60*60],
        4: [10*60*60, 24*60*60],
        5: [24*60*60, 7*24*60*60],
        6: [7*24*60*60, 14*24*60*60],
        7: [14*24*60*60, 2591999]
    }

违禁词检测：
 - 支持正则表达式(使用用制表符分隔)
 - 可定义触发违禁词操作(默认为禁言+撤回)
 - 可定义生效范围(排除某些群 or 仅限某些群生效)
 - 示例：
  - 加(群|君\S?羊|羣)\S*\d{6,}		$撤回$禁言$仅限123456789,987654321
  - 狗群主				$禁言$排除987654321

【功能开关】
群内发送：
  开关xx : 对某功能进行开/关  permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER
  开关状态 ： 查看各功能的状态
  xx in ：
    ['管理', '踢', '禁', '改', '基础群管']  #基础功能 踢、禁、改、管理员+-
    ['加群', '审批', '加群审批', '自动审批'] #加群审批
    ['词云', '群词云', 'wordcloud'] #群词云
    ['违禁词', '违禁词检测'] #违禁词检测
    ['图片检测', '图片鉴黄', '涩图检测', '色图检测'] #图片检测
    ['消息记录', '群消息记录', '发言记录'],
    ['早安晚安', '早安', '晚安'],
    ['广播消息', '群广播', '广播'],
    ['事件通知', '变动通知', '事件提醒'],
     ['防撤回', '防止撤回']
图片检测和违禁词检测默认关,其他默认开

【广播】permission = SUPERUSER
本功能默认关闭
   "发送【广播】/【广播+[消息]】可广播消息" 
   "发送【群列表】可查看能广播到的所有群" 
   "发送【排除列表】可查看已排除的群" 
   "发送【广播排除+】可添加群到广播排除列表" 
   "发送【广播排除-】可从广播排除列表删除群"
   "发送【广播帮助】可查看广播帮助"
   发送【开关广播】来开启/关闭（意义不大）
   
【特殊事件提醒】
包括管理员变动，加群退群等...
待完善
  发送【开关事件通知】来开启/关闭功能 permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER


【防撤回】
默认关闭
 发送【开关防撤回】开启或关闭功能 permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER

【群员清理】
群内发送 permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER | DEPUTY_ADMIN
该功能暂不被开关控制
发送【群员清理】可根据[等级] 或 [发言时间] 清理群员
在执行此命令时，当前群会对此操作加锁，防止其他人同时操作，如果出现问题，可执行【清理解锁】来手动解锁

"""
__help_plugin_name__ = '简易群管'

__permission__ = 1
__help__version__ = '0.2.0'
