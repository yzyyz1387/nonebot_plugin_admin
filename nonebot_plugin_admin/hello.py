import random
from asyncio import sleep
from pathlib import Path
from nonebot import on_message, on_command
from nonebot import get_driver, on_request, on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent, GroupMessageEvent, \
    MessageSegment, Message

from .config import config
from .message_util import MessageBuild

superuser = int(list(get_driver().config.superusers)[0])

requests_handle = on_request(priority=5, block=True)
notice_handle = on_notice(priority=5, block=True)


@notice_handle.handle()
async def GroupNewMember(bot: Bot, event: GroupIncreaseNoticeEvent):
    greet_emoticon = MessageBuild.Image(Path()/'data'/'img'/'bg.jpg', mode='RGBA')
    if event.user_id == event.self_id:
        await sleep(random.randint(4, 8))
        await bot.send_group_msg(group_id=event.group_id, message=Message(
            MessageSegment.text('这是哪里？哦？让我康康！\n') + greet_emoticon))
    elif event.group_id not in config.paimon_greet_ban:
        await sleep(random.randint(4, 8))
        await bot.send_group_msg(group_id=event.group_id, message=Message(
            MessageSegment.at(event.user_id) + MessageSegment.text("欢迎新群友哦~\n") + greet_emoticon))

caidan = on_command("菜单", aliases={"cd"})

@caidan.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    greet_emoticon = MessageBuild.Image(Path()/'data'/'img'/'bg.jpg', mode='RGBA')
    await sleep(random.randint(4, 8))
    await bot.send_group_msg(group_id=event.group_id, message=Message(
        MessageSegment.at(event.user_id) + MessageSegment.text(__cd__) + greet_emoticon))

version = on_command("群管版本", aliases={"admin -v"})

@version.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    greet_emoticon = MessageBuild.Image(Path()/'data'/'img'/'bg.jpg', mode='RGBA')
    await sleep(random.randint(4, 8))
    await bot.send_group_msg(group_id=event.group_id, message=Message(
        MessageSegment.at(event.user_id) + MessageSegment.text("\n插件名称：" + __help_plugin_name__ + "\n" + "版本：" + __help__version__) + greet_emoticon))

__help_plugin_name__ = "简易群管"

__permission__ = 1
__help__version__ = '0.6'

__cd__ = """
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
   撤回 @user [(可选，默认n=5)历史消息倍数n] (实际检查的历史数为 n*19)
   
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
  
【被动识别】
涩图检测：将禁言随机时间

违禁词检测：已支持正则表达式，可定义触发违禁词操作(默认为禁言+撤回)
定义操作方法：用制表符分隔，左边为触发条件，右边为操作定义($禁言、$撤回)
群内发送：
  简单违禁词 ：简单级别过滤
  严格违禁词 ：严格级别过滤(不建议)
  更新违禁词库 ：手动更新词库
    违禁词库每周一自动更新
    
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
所有功能默认开"
"""
