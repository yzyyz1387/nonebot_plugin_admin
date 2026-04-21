from __future__ import annotations

from nonebot.log import logger

from .group_message_config import GroupMessageConfig


def register_group_message_jobs(scheduler, config: GroupMessageConfig, send_morning_job, send_night_job) -> None:
    """
    注册群消息jobs
    :param scheduler: scheduler 参数
    :param config: 配置字典
    :param send_morning_job: send_morning_job 参数
    :param send_night_job: send_night_job 参数
    :return: None
    """
    scheduler.add_job(send_morning_job, "cron", hour=config.morning_hour, minute=config.morning_minute, id="send_morning")
    scheduler.add_job(send_night_job, "cron", hour=config.night_hour, minute=config.night_minute, id="send_night")
    logger.info("已检测到软依赖 nonebot_plugin_apscheduler，开启定时任务功能")
