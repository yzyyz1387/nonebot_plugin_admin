# python3
# -*- coding: utf-8 -*-

NO_APPROVAL_TERMS_CONFIGURED = "当前没有已配置的审批词条"
SUPER_ADD_USAGE = "输入有误 /susp+ [群号] [词条]"
SUPER_DELETE_USAGE = "输入有误 /susp- [群号] [词条]"
GROUP_TERMS_EMPTY = "当前群从未配置过审批词条"
ADD_TERM_EMPTY = "请输入要添加的审批词条"
DELETE_TERM_EMPTY = "请输入要删除的审批词条"
BLACKLIST_USAGE = "输入有误，请使用：\n拒绝词条 [+/-] [词条]"
BLACKLIST_TERM_EMPTY = "请输入要操作的词条内容"
BLACKLIST_GROUP_EMPTY = "群 {gid} 从未配置过词条"
REQUEST_DENY_REASON = "答案未通过群管验证，可修改答案后再次申请"
REQUEST_BLACKLIST_HIT_LOG = "验证消息【{word}】命中黑名单词条：{matches}"
REQUEST_BLACKLIST_REASON_LOG = "拒绝原因：加群验证消息在黑名单中"
REQUEST_SKIP_LOG = "群 {gid} 未配置审批词条，跳过入群审批自动处理"
GROUP_ADMIN_EXISTS = "{qq} 已经是群 {gid} 的分群管理员"
GROUP_ADMIN_FIRST_ADD = "群 {gid} 首次添加分群管理员"
GROUP_ADMIN_ADDED = "群 {gid} 添加分群管理员：{qq}"
GROUP_ADMIN_UNCONFIGURED = "群 {gid} 还未添加过分群管理员"
GROUP_ADMIN_DELETE_MISSING = "删除失败：群 {gid} 中的 {qq} 还不是分群管理员"
GROUP_ADMIN_DELETED = "已删除群 {gid} 的分群管理员：{qq}"
APPROVAL_NOTICE_ENABLED = "打开审批消息接收"
APPROVAL_NOTICE_DISABLED = "关闭审批消息接收"


def format_group_terms(gid: str, terms) -> str:
    """
    格式化群词条
    :param gid: 群号
    :param terms: terms 参数
    :return: str
    """
    return f"当前群审批词条：{terms}"


def format_term_added(gid: str, term: str) -> str:
    """
    格式化词条added
    :param gid: 群号
    :param term: term 参数
    :return: str
    """
    return f"群 {gid} 添加词条：{term}"


def format_term_exists(gid: str, term: str) -> str:
    """
    格式化词条exists
    :param gid: 群号
    :param term: term 参数
    :return: str
    """
    return f"{term} 已存在于群 {gid} 的词条中"


def format_approval_term_added(gid: str, term: str) -> str:
    """
    格式化审批词条added
    :param gid: 群号
    :param term: term 参数
    :return: str
    """
    return f"群 {gid} 添加入群审批词条：{term}"


def format_approval_term_deleted(gid: str, term: str) -> str:
    """
    格式化审批词条deleted
    :param gid: 群号
    :param term: term 参数
    :return: str
    """
    return f"群 {gid} 删除入群审批词条：{term}"


def format_group_term_missing(gid: str) -> str:
    """
    格式化群词条missing
    :param gid: 群号
    :return: str
    """
    return f"群 {gid} 不存在此词条"


def format_group_term_unconfigured(gid: str) -> str:
    """
    格式化群词条unconfigured
    :param gid: 群号
    :return: str
    """
    return BLACKLIST_GROUP_EMPTY.format(gid=gid)


def format_blacklist_added(gid: str, word: str) -> str:
    """
    格式化黑名单added
    :param gid: 群号
    :param word: word 参数
    :return: str
    """
    return f"群 {gid} 添加自动拒绝词条：{word}"


def format_blacklist_removed(gid: str, word: str) -> str:
    """
    格式化黑名单removed
    :param gid: 群号
    :param word: word 参数
    :return: str
    """
    return f"群 {gid} 删除自动拒绝词条：{word}"


def format_request_approved(uid: int, gid: str, word: str) -> str:
    """
    格式化请求approved
    :param uid: 用户号
    :param gid: 群号
    :param word: word 参数
    :return: str
    """
    return f"同意 {uid} 加入群 {gid}，验证消息为“{word}”"


def format_request_rejected(uid: int, gid: str, word: str) -> str:
    """
    格式化请求rejected
    :param uid: 用户号
    :param gid: 群号
    :param word: word 参数
    :return: str
    """
    return f"拒绝 {uid} 加入群 {gid}，验证消息为“{word}”"


def format_group_admin_exists(gid: str, qq: int) -> str:
    """
    格式化群管理员exists
    :param gid: 群号
    :param qq: QQ 号
    :return: str
    """
    return GROUP_ADMIN_EXISTS.format(gid=gid, qq=qq)


def format_group_admin_first_add(gid: str) -> str:
    """
    格式化群管理员firstadd
    :param gid: 群号
    :return: str
    """
    return GROUP_ADMIN_FIRST_ADD.format(gid=gid)


def format_group_admin_added(gid: str, qq: int) -> str:
    """
    格式化群管理员added
    :param gid: 群号
    :param qq: QQ 号
    :return: str
    """
    return GROUP_ADMIN_ADDED.format(gid=gid, qq=qq)


def format_group_admin_unconfigured(gid: str) -> str:
    """
    格式化群管理员unconfigured
    :param gid: 群号
    :return: str
    """
    return GROUP_ADMIN_UNCONFIGURED.format(gid=gid)


def format_group_admin_delete_missing(gid: str, qq: int) -> str:
    """
    格式化群管理员deletemissing
    :param gid: 群号
    :param qq: QQ 号
    :return: str
    """
    return GROUP_ADMIN_DELETE_MISSING.format(gid=gid, qq=qq)


def format_group_admin_deleted(gid: str, qq: int) -> str:
    """
    格式化群管理员deleted
    :param gid: 群号
    :param qq: QQ 号
    :return: str
    """
    return GROUP_ADMIN_DELETED.format(gid=gid, qq=qq)
