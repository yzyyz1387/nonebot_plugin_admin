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
