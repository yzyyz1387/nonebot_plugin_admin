"""
额外依赖 pip install nonebot_plugin_apscheduler
定时推送群消息需要在 .env 中配置：
send_group_id = ["xxx", "xxx"]
send_switch_morning = False
send_switch_night = False
send_mode = 1
send_sentence_morning = ["句子1", "句子2", "..."]
send_sentence_night = ["句子1", "句子2", "..."]
send_time_morning = "8 0"
send_time_night = "23 0"
"""

from nonebot import get_driver, require
from nonebot.log import logger
from nonebot.plugin import get_available_plugin_names

from .group_message_config import load_group_message_config
from .group_message_schedule_flow import register_group_message_jobs
from .group_message_send_flow import run_group_message_job

group_message_config = load_group_message_config(get_driver().config)


async def send_morning():
    """
    发送morning
    :return: None
    """
    await run_group_message_job(group_message_config, "morning")


async def send_night():
    """
    发送night
    :return: None
    """
    await run_group_message_job(group_message_config, "night")


try:
    assert "nonebot_plugin_apscheduler" in get_available_plugin_names()
    require("nonebot_plugin_apscheduler")
    from nonebot_plugin_apscheduler import scheduler

    register_group_message_jobs(scheduler, group_message_config, send_morning, send_night)
except Exception:
    logger.error("未检测到软依赖 nonebot_plugin_apscheduler，禁用定时任务功能")
