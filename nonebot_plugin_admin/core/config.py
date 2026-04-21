import json

from nonebot import get_driver, get_plugin_config
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    tenid: str = "xxxxxx"
    tenkeys: str = "xxxxxx"
    callback_notice: bool = True
    ban_rand_time_min: int = 60
    ban_rand_time_max: int = 2591999
    ai_verify_proxy: str = ""
    ai_verify_use_proxy: bool = True
    statistics_orm_enabled: bool = False
    statistics_orm_capture_message_content: bool = True
    dashboard_enabled: bool = False
    dashboard_frontend_enabled: bool = False
    dashboard_base_path: str = "/admin-dashboard"
    dashboard_api_token: str = ""
    dashboard_title: str = "Admin Dashboard"
    dashboard_log_file_path: str = ""
    dashboard_cors_allow_origins: str = ""
    dashboard_cors_allow_credentials: bool = False


driver = get_driver()
global_config = driver.config


def _model_dump(instance: BaseModel) -> dict:
    """
    处理 _model_dump 的业务逻辑
    :param instance: instance 参数
    :return: dict
    """
    if hasattr(instance, "model_dump"):
        return instance.model_dump()
    return instance.dict()


def parse_string_list(raw_value: object) -> list[str]:
    """
    解析stringlist
    :param raw_value: raw_value 参数
    :return: list[str]
    """
    if raw_value is None:
        return []

    if isinstance(raw_value, (list, tuple, set)):
        return [str(item).strip() for item in raw_value if str(item).strip()]

    value = str(raw_value).strip()
    if not value:
        return []

    if value.startswith("["):
        try:
            payload = json.loads(value)
        except Exception:
            payload = None
        if isinstance(payload, list):
            return [str(item).strip() for item in payload if str(item).strip()]

    return [item.strip() for item in value.split(",") if item.strip()]


def load_plugin_config() -> Config:
    """
    加载plugin配置
    :return: Config
    """
    field_names = list(getattr(Config, "__fields__", {}).keys())
    merged: dict = {}

    for field_name in field_names:
        if hasattr(global_config, field_name):
            merged[field_name] = getattr(global_config, field_name)

    try:
        config_from_nonebot = get_plugin_config(Config)
    except Exception:
        config_from_nonebot = Config()

    merged = {
        **_model_dump(config_from_nonebot),
        **merged,
    }

    db_url = str(merged.get("tortoise_orm_db_url", "") or "").strip()
    if db_url and not merged.get("statistics_orm_enabled"):
        merged["statistics_orm_enabled"] = True

    return Config(**merged)


plugin_config = load_plugin_config()
