# from typing import Optional
from nonebot import get_driver
from pydantic import BaseModel, Extra

class Config(BaseModel, extra=Extra.ignore):
    tenid: str = "xxxxxx"
    tenkeys: str = "xxxxxx"
    callback_notice: bool = False # 是否在操作完成后在 QQ 返回提示
    cron_update: bool = True

global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)
