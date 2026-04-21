from __future__ import annotations

from typing import Any, Optional


IMAGE_GUARD_RUNTIME_STATUS = "suspended"
IMAGE_GUARD_RUNTIME_LABEL = "已挂起"
IMAGE_GUARD_PROVIDER_LABEL = "腾讯图片审核（预留）"


def is_image_guard_suspended() -> bool:
    """
    处理 is_image_guard_suspended 的业务逻辑
    :return: bool
    """
    return True


def build_image_guard_status_payload(switch_enabled: bool) -> dict[str, Any]:
    """
    构建图片审核statuspayload
    :param switch_enabled: switch_enabled 参数
    :return: dict[str, Any]
    """
    return {
        "switch_enabled": bool(switch_enabled),
        "processing_enabled": bool(switch_enabled) and not is_image_guard_suspended(),
        "runtime_status": IMAGE_GUARD_RUNTIME_STATUS,
        "runtime_label": IMAGE_GUARD_RUNTIME_LABEL,
        "provider": IMAGE_GUARD_PROVIDER_LABEL,
    }


def _get_score(result: Optional[dict]) -> int:
    """
    获取score
    :param result: 结果对象
    :return: int
    """
    if not result:
        return 0
    try:
        return int(result.get("Score", 0) or 0)
    except (TypeError, ValueError):
        return 0


def should_process_result(result: Optional[dict]) -> bool:
    """
    处理 should_process_result 的业务逻辑
    :param result: 结果对象
    :return: bool
    """
    return bool(result) and result.get("Suggestion") != "Pass"


def is_high_score_violation(result: Optional[dict]) -> bool:
    """
    处理 is_high_score_violation 的业务逻辑
    :param result: 结果对象
    :return: bool
    """
    return should_process_result(result) and _get_score(result) >= 90


def is_porn_violation(result: Optional[dict]) -> bool:
    """
    处理 is_porn_violation 的业务逻辑
    :param result: 结果对象
    :return: bool
    """
    return should_process_result(result) and result.get("Label") == "Porn"


def should_warn_only_porn(result: Optional[dict]) -> bool:
    """
    处理 should_warn_only_porn 的业务逻辑
    :param result: 结果对象
    :return: bool
    """
    return is_porn_violation(result) and not is_high_score_violation(result)


def build_porn_notice(level: Optional[int] = None) -> str:
    """
    构建porn通知
    :param level: level 参数
    :return: str
    """
    prefix = f"你的违规等级为{level}，" if level is not None else ""
    return prefix + "涩涩不规范，群主两行泪，请群友小心驾驶"
