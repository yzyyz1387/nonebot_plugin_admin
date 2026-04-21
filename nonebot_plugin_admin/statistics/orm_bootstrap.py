from __future__ import annotations

import importlib.util
from pathlib import Path

from nonebot import get_driver, logger, require

from ..core.config import plugin_config

_ORM_BOOTSTRAP_ATTEMPTED = False
_ORM_BOOTSTRAP_READY = False

ORM_REQUIRED_PACKAGE = "nonebot_plugin_tortoise_orm"
ORM_ENABLE_HINTS = [
    "statistics_orm_enabled=true",
    "statistics_orm_capture_message_content=true",
    "tortoise_orm_db_url=sqlite:///data/admin3-statistics.db",
]


def _normalize_sqlite_path(db_url: str) -> Path | None:
    """
    规范化sqlite路径
    :param db_url: db_url 参数
    :return: Path | None
    """
    if not db_url.startswith("sqlite://"):
        return None

    raw_path = db_url[len("sqlite://") :]
    if not raw_path or raw_path == ":memory:":
        return None

    if raw_path.startswith("////"):
        sqlite_path = Path(raw_path[3:])
    elif raw_path.startswith("///"):
        sqlite_path = Path(raw_path[2:])
    elif raw_path.startswith("//"):
        sqlite_path = Path(raw_path[1:])
    else:
        sqlite_path = Path(raw_path)

    if not sqlite_path.is_absolute():
        sqlite_path = Path.cwd() / sqlite_path
    return sqlite_path


def ensure_statistics_orm_directory() -> Path | None:
    """
    确保statisticsORMdirectory
    :return: Path | None
    """
    db_url = str(getattr(get_driver().config, "tortoise_orm_db_url", "") or "").strip()
    sqlite_path = _normalize_sqlite_path(db_url)
    if sqlite_path is None:
        return None

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite_path


_DASHBOARD_ORM_ATTEMPTED = False
_DASHBOARD_ORM_READY = False


def ensure_dashboard_orm_support() -> bool:
    """
    确保面板ORMsupport
    :return: bool
    """
    global _DASHBOARD_ORM_ATTEMPTED, _DASHBOARD_ORM_READY

    if _DASHBOARD_ORM_READY:
        return True

    if _DASHBOARD_ORM_ATTEMPTED:
        return _DASHBOARD_ORM_READY

    _DASHBOARD_ORM_ATTEMPTED = True

    try:
        ensure_statistics_orm_directory()
        if importlib.util.find_spec(ORM_REQUIRED_PACKAGE) is None:
            return False
        require(ORM_REQUIRED_PACKAGE)
        from . import models

        if not models.ORM_MODELS_AVAILABLE:
            return False
    except Exception as err:
        logger.debug(f"Dashboard ORM 初始化跳过：{type(err).__name__}: {err}")
        return False

    _DASHBOARD_ORM_READY = True
    logger.debug("Dashboard ORM 已就绪，操作日志功能可用")
    return True


def get_statistics_orm_bootstrap_state() -> dict[str, object]:
    """
    获取statisticsORMbootstrap状态
    :return: dict[str, object]
    """
    return {
        "attempted": _ORM_BOOTSTRAP_ATTEMPTED,
        "ready": _ORM_BOOTSTRAP_READY,
        "enabled": plugin_config.statistics_orm_enabled,
        "required_package": ORM_REQUIRED_PACKAGE,
        "env_hints": list(ORM_ENABLE_HINTS),
    }


def ensure_statistics_orm_support() -> bool:
    """
    确保statisticsORMsupport
    :return: bool
    """
    global _ORM_BOOTSTRAP_ATTEMPTED, _ORM_BOOTSTRAP_READY

    if _ORM_BOOTSTRAP_ATTEMPTED:
        return _ORM_BOOTSTRAP_READY

    _ORM_BOOTSTRAP_ATTEMPTED = True
    if not plugin_config.statistics_orm_enabled:
        return False

    sqlite_path: Path | None = None
    try:
        sqlite_path = ensure_statistics_orm_directory()
        if importlib.util.find_spec(ORM_REQUIRED_PACKAGE) is None:
            raise ModuleNotFoundError(ORM_REQUIRED_PACKAGE)
        require(ORM_REQUIRED_PACKAGE)
        from . import models

        if not models.ORM_MODELS_AVAILABLE:
            raise RuntimeError(models.ORM_IMPORT_ERROR or "statistics orm models are unavailable")
    except Exception as err:
        logger.warning(
            f"统计 ORM 已配置开启，但未能成功接入数据库写入，将继续使用文件存储：{type(err).__name__}: {err}"
        )
        logger.warning(
            "如需启用统计 ORM，请确认已安装 nonebot-plugin-tortoise-orm，并在 .env 中配置："
            + " | ".join(ORM_ENABLE_HINTS)
        )
        return False

    _ORM_BOOTSTRAP_READY = True
    logger.opt(colors=True).success(
        "<green>统计 ORM 已启用：消息会同时写入数据库，群聊工作台可显示发送者、时间和实时分页。</green>"
    )
    logger.info("统计 ORM 当前配置：" + " | ".join(ORM_ENABLE_HINTS))
    if sqlite_path is not None:
        logger.info(f"统计 ORM SQLite 数据库路径：{sqlite_path}")
    return True
