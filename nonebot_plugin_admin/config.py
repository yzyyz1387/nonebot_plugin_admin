# from typing import Optional
from nonebot import get_driver
from pydantic import BaseModel, Extra
from typing import List

from nonebot import get_driver
from pydantic import BaseModel


class PluginConfig(BaseModel):
    # 是否自动通过好友请求
    paimon_add_friend: bool = False
    # 是否自动通过群组请求
    paimon_add_group: bool = False
    # 禁用群新成员欢迎语和龙王提醒的群号列表
    paimon_greet_ban: List[int] = []


driver = get_driver()
global_config = driver.config
config: PluginConfig = PluginConfig.parse_obj(global_config.dict())


class Config(BaseModel, extra=Extra.ignore):
    tenid: str = "xxxxxx"  # 腾讯云图片安全，开通地址： https://console.cloud.tencent.com/cms
    tenkeys: str = "xxxxxx"  # 文档： https://cloud.tencent.com/document/product/1125
    callback_notice: bool = True  # 是否在操作完成后在 QQ 返回提示
    cron_update: bool = True  # 是否开通自动更新词库【打开则每周一更新违禁词库】
    ban_rand_time_min: int = 60  # 随机禁言最短时间(s) default: 1分钟
    ban_rand_time_max: int = 2591999  # 随机禁言最长时间(s) default: 30天: 60*60*24*30


global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)
