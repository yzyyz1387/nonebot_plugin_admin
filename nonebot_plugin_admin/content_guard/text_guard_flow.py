from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from ..statistics.config_orm_store import orm_load_content_guard_rules


GROUP_SCOPE_PATTERN = re.compile(r"\$(仅限|排除)(([0-9]{6,},?)+)")


def load_limit_rules(limit_word_path: Path) -> list[list[str]]:
    """
    加载limit规则
    :param limit_word_path: 路径对象
    :return: list[list[str]]
    """
    if not limit_word_path.exists():
        return []
    return [re.sub(r"\t+", "\t", line).split("\t") for line in limit_word_path.read_text(encoding="utf-8").splitlines()]


async def load_runtime_limit_rules() -> list[list[str]]:
    """
    加载运行时limit规则
    :return: list[list[str]]
    """
    rules = await orm_load_content_guard_rules()
    if not isinstance(rules, list):
        return []
    return [list(rule) for rule in rules if isinstance(rule, list) and rule]


def should_apply_group_scope(options: str, group_id: int) -> bool:
    """
    处理 should_apply_group_scope 的业务逻辑
    :param options: options 参数
    :param group_id: 群号
    :return: bool
    """
    match = GROUP_SCOPE_PATTERN.search(options)
    if not match:
        return True

    mode, groups = match.group(1), match.group(2)
    group_list = groups.split(",")
    gid = str(group_id)
    if mode == "仅限":
        return gid in group_list
    return gid not in group_list


def matches_rule_pattern(pattern: str, text: str) -> bool:
    """
    处理 matches_rule_pattern 的业务逻辑
    :param pattern: pattern 参数
    :param text: 文本内容
    :return: bool
    """
    try:
        return re.search(pattern, text) is not None
    except Exception:
        return pattern in text


def check_text_rule(text: str, group_id: int, rule: list[str]) -> tuple[bool, bool, Optional[str]]:
    """
    检查文本规则
    :param text: 文本内容
    :param group_id: 群号
    :param rule: rule 参数
    :return: tuple[bool, bool, Optional[str]]
    """
    if not rule or not rule[0]:
        return False, False, None

    delete, ban = True, True
    if len(rule) > 1:
        options = rule[1]
        delete = "$撤回" in options
        ban = "$禁言" in options
        if not should_apply_group_scope(options, group_id):
            return False, False, None

    if not matches_rule_pattern(rule[0], text):
        return False, False, None
    return delete, ban, rule[0]



def check_text_message(text: str, group_id: int, limit_word_path: Path) -> tuple[bool, bool, Optional[str]]:
    """
    检查文本消息
    :param text: 文本内容
    :param group_id: 群号
    :param limit_word_path: 路径对象
    :return: tuple[bool, bool, Optional[str]]
    """
    for rule in load_limit_rules(limit_word_path):
        matched = check_text_rule(text, group_id, rule)
        if matched[2]:
            return matched
    return False, False, None


async def check_runtime_text_message(text: str, group_id: int) -> tuple[bool, bool, Optional[str]]:
    """
    检查运行时文本消息
    :param text: 文本内容
    :param group_id: 群号
    :return: tuple[bool, bool, Optional[str]]
    """
    for rule in await load_runtime_limit_rules():
        matched = check_text_rule(text, group_id, rule)
        if matched[2]:
            return matched
    return False, False, None
