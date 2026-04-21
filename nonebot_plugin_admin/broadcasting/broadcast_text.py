from __future__ import annotations

from collections.abc import Iterable

BROADCAST_INPUT_PROMPT = "请输入要广播的内容，发送“取消”取消。"
BROADCAST_CONFIRM_PROMPT = "发送“确认”开始广播，发送“取消”取消。"
BROADCAST_CONFIRM_INVALID_TEXT = "请发送“确认”或“取消”。"
BROADCAST_CANCELLED_TEXT = "已取消广播。"
BROADCAST_NO_TARGET_TEXT = "没有可广播的群，广播已取消。"
BROADCAST_AVOID_USAGE_TEXT = (
    "请发送【广播排除+ 群号】或【广播排除- 群号】，多个群号用空格分隔。发送【群列表】可查看所有群号。"
)
BROADCAST_AVOID_EMPTY_TEXT = "广播排除列表为空。"
BROADCAST_GROUP_LIST_PROMPT = (
    "现在可以直接发送要加入排除列表的群号，多个群号用空格分隔。"
    "发送“0”表示排除除当前群外的全部群，发送“取消”取消。"
)
BROADCAST_LIST_CANCELLED_TEXT = "已取消添加广播排除群。"
BROADCAST_NOT_IN_GROUP_TEXT = "当前不在群聊中，无法使用“0”快捷排除。"


def _join_group_brief(groups: Iterable[dict], limit: int = 5) -> str:
    """
    处理 _join_group_brief 的业务逻辑
    :param groups: groups 参数
    :param limit: 数量限制
    :return: str
    """
    items = [f"{group['group_name']}({group['group_id']})" for group in list(groups)[:limit]]
    return "、".join(items)


def format_broadcast_preview(
    message_preview: str,
    target_groups: list[dict],
    excluded_groups: list[dict],
) -> str:
    """
    格式化broadcastpreview
    :param message_preview: message_preview 参数
    :param target_groups: target_groups 参数
    :param excluded_groups: excluded_groups 参数
    :return: str
    """
    lines = [
        "广播预览",
        f"目标群数：{len(target_groups)}",
        f"排除群数：{len(excluded_groups)}",
        "内容：",
        message_preview,
    ]
    if target_groups:
        lines.append(f"目标群示例：{_join_group_brief(target_groups)}")
    if excluded_groups:
        lines.append(f"排除群示例：{_join_group_brief(excluded_groups)}")
    lines.append("发送“确认”开始广播，发送“取消”取消。")
    return "\n".join(lines)


def format_broadcast_result(success: list[int], failed: list[int], excluded_count: int) -> str:
    """
    格式化broadcastresult
    :param success: success 参数
    :param failed: failed 参数
    :param excluded_count: excluded_count 参数
    :return: str
    """
    lines = [
        "广播完成",
        f"成功：{len(success)}",
        f"失败：{len(failed)}",
        f"排除：{excluded_count}",
    ]
    if failed:
        lines.append("发送失败的群号：" + " ".join(str(group_id) for group_id in failed))
    return "\n".join(lines)


def format_group_list(groups: list[dict]) -> str:
    """
    格式化群list
    :param groups: groups 参数
    :return: str
    """
    lines = [f"共 {len(groups)} 个群："]
    for group in groups:
        lines.append(f"{group['group_name']}: {group['group_id']}")
    return "\n".join(lines)


def format_excluded_group_list(groups: list[dict]) -> str:
    """
    格式化excluded群list
    :param groups: groups 参数
    :return: str
    """
    if not groups:
        return BROADCAST_AVOID_EMPTY_TEXT
    lines = [f"共 {len(groups)} 个排除群："]
    for group in groups:
        lines.append(f"{group['group_name']}: {group['group_id']}")
    return "\n".join(lines)


def format_add_excluded_result(added: list[str], existed: list[str], invalid: list[str]) -> str:
    """
    格式化addexcludedresult
    :param added: added 参数
    :param existed: existed 参数
    :param invalid: 标识值
    :return: str
    """
    lines: list[str] = []
    if added:
        lines.append("添加成功：" + " ".join(added))
    if existed:
        lines.append("已在排除列表中：" + " ".join(existed))
    if invalid:
        lines.append("机器人不在这些群中：" + " ".join(invalid))
    return "\n".join(lines) if lines else "没有可添加的群号。"


def format_remove_excluded_result(removed: list[str], missing: list[str]) -> str:
    """
    格式化removeexcludedresult
    :param removed: removed 参数
    :param missing: missing 参数
    :return: str
    """
    lines: list[str] = []
    if removed:
        lines.append("已移出排除列表：" + " ".join(removed))
    if missing:
        lines.append("以下群号不在排除列表中：" + " ".join(missing))
    return "\n".join(lines) if lines else BROADCAST_AVOID_EMPTY_TEXT
