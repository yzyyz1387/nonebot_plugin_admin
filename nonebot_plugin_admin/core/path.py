# python3
# -*- coding: utf-8 -*-

from pathlib import Path

from nonebot import get_driver

from ..util.time_util import TIME_DAY, TIME_HOUR, TIME_MINUS

config_path = Path() / "config"
legacy_backup_path = config_path / "legacy_backup"
config_admin = config_path / "admin.json"
config_group_admin = config_path / "group_admin.json"
word_path = config_path / "word_config.txt"
statistics_record_state_path = config_path / "statistics_record_state.json"
words_contents_path = config_path / "words"
res_path = Path() / "resource"
re_img_path = res_path / "imgs"
ttf_name = res_path / "msyhblod.ttf"
limit_word_path = config_path / "违禁词.txt"
switcher_path = config_path / "开关.json"
template_path = config_path / "template"
stop_words_path = config_path / "stop_words"
wordcloud_bg_path = config_path / "wordcloud_bg"
user_violation_info_path = config_path / "群内用户违规信息"
group_message_data_path = config_path / "群消息数据"
error_path = config_path / "admin插件错误数据"
broadcast_avoid_path = config_path / "广播排除群聊.json"
ttf_path = res_path / "msyhblod.ttf"
summary_path = config_path / "summary"
kick_lock_path = config_path / "kick_lock"
appr_bk = config_path / "加群验证信息黑名单.json"

AI_APPROVAL_SWITCH_KEY = "ai_group_verify"

admin_funcs = {
    "admin": ["管理", "踢", "禁", "撤", "基础群管"],
    "requests": ["审批", "加群审批", "加群", "自动审批"],
    AI_APPROVAL_SWITCH_KEY: ["AI审批", "ai审批", "AI审核", "ai审核", "AI拒绝", "ai拒绝"],
    "wordcloud": ["群词云", "词云", "wordcloud"],
    "auto_ban": ["违禁词", "违禁词检测"],
    "img_check": ["图片检测", "图片鉴黄", "涩图检测", "色图检测"],
    "word_analyze": ["消息记录", "群消息记录", "发言记录"],
    "group_msg": ["早安晚安", "早安", "晚安"],
    "broadcast": ["广播消息", "群广播", "广播"],
    "particular_e_notice": ["事件通知", "变动通知", "事件提醒"],
    "group_recall": ["防撤回", "防止撤回"],
}

funcs_name_cn = ["基础群管", "加群审批", "群词云", "违禁词检测", "图片检测"]

DEFAULT_DISABLED_FUNCS = frozenset(
    {
        "img_check",
        "auto_ban",
        AI_APPROVAL_SWITCH_KEY,
        "group_msg",
        "particular_e_notice",
        "group_recall",
    }
)

SILENT_DISABLED_NOTICE_FUNCS = frozenset(
    {
        "auto_ban",
        "img_check",
        AI_APPROVAL_SWITCH_KEY,
        "particular_e_notice",
        "word_analyze",
        "group_recall",
    }
)


def is_default_enabled(func_name: str) -> bool:
    """
    处理 is_default_enabled 的业务逻辑
    :param func_name: 功能名
    :return: bool
    """
    return func_name not in DEFAULT_DISABLED_FUNCS


def should_notify_when_disabled(func_name: str) -> bool:
    """
    处理 should_notify_when_disabled 的业务逻辑
    :param func_name: 功能名
    :return: bool
    """
    return func_name not in SILENT_DISABLED_NOTICE_FUNCS


def build_default_switchers() -> dict[str, bool]:
    """
    构建defaultswitchers
    :return: dict[str, bool]
    """
    return {func_name: is_default_enabled(func_name) for func_name in admin_funcs}


def get_func_display_name(func_name: str) -> str:
    """
    获取funcdisplayname
    :param func_name: 功能名
    :return: str
    """
    aliases = admin_funcs.get(func_name) or []
    return aliases[0] if aliases else func_name


GROUP_MUTE_MAX_TIME = 30 * TIME_DAY - 1

time_scop_map = {
    0: [0, 5 * TIME_MINUS],
    1: [5 * TIME_MINUS, 10 * TIME_MINUS],
    2: [10 * TIME_MINUS, 30 * TIME_MINUS],
    3: [30 * TIME_MINUS, 10 * TIME_HOUR],
    4: [10 * TIME_HOUR, 1 * TIME_DAY],
    5: [1 * TIME_DAY, 7 * TIME_DAY],
    6: [7 * TIME_DAY, 14 * TIME_DAY],
    7: [14 * TIME_DAY, GROUP_MUTE_MAX_TIME],
}


localhost = f"http://{get_driver().config.host}:{get_driver().config.port}"
