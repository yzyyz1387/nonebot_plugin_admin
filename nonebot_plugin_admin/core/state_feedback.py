def build_explicit_state_message(
    feature_name: str,
    *,
    enabled: bool,
    enable_command: str,
    disable_command: str,
) -> str:
    """
    构建explicit状态消息
    :param feature_name: feature_name 参数
    :param enabled: 开关状态
    :param enable_command: enable_command 参数
    :param disable_command: disable_command 参数
    :return: str
    """
    state_text = "已开启" if enabled else "已关闭"
    next_action = "关闭" if enabled else "开启"
    next_command = disable_command if enabled else enable_command
    return f"{feature_name}当前状态为：{state_text}\n若要{next_action}，请发送【{next_command}】"


def build_toggle_state_message(feature_name: str, *, enabled: bool, toggle_command: str) -> str:
    """
    构建toggle状态消息
    :param feature_name: feature_name 参数
    :param enabled: 开关状态
    :param toggle_command: toggle_command 参数
    :return: str
    """
    state_text = "已开启" if enabled else "已关闭"
    next_action = "关闭" if enabled else "开启"
    return f"{feature_name}当前状态为：{state_text}\n若要{next_action}，请发送【{toggle_command}】"
