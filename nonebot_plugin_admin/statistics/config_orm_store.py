from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from nonebot import logger

from ..core.config import plugin_config
from .models import (
    ORM_MODELS_AVAILABLE,
    ApprovalBlacklistTerm,
    ApprovalTerm,
    AIVerifyConfig,
    BroadcastExclusion,
    ContentGuardRule,
    DeputyAdmin,
    GlobalConfig,
    GroupFeatureSwitch,
    StatisticsDailyMessageStat,
    StatisticsGroupRecordSetting,
    StatisticsHistoryMessageStat,
    UserViolation,
    ViolationRecord,
)


def _is_orm_enabled() -> bool:
    """
    处理 _is_orm_enabled 的业务逻辑
    :return: bool
    """
    return plugin_config.statistics_orm_enabled and ORM_MODELS_AVAILABLE


def _normalize_content_guard_rule_entry(rule: Any) -> tuple[str, str] | None:
    """
    规范化内容审核规则entry
    :param rule: rule 参数
    :return: tuple[str, str] | None
    """
    if isinstance(rule, str):
        pattern = rule.strip()
        options = ""
    elif isinstance(rule, (list, tuple)):
        if not rule:
            return None
        pattern = str(rule[0]).strip()
        options = str(rule[1]).strip() if len(rule) > 1 else ""
    else:
        return None

    if not pattern:
        return None
    return pattern, options


async def orm_load_switcher() -> Dict[str, Dict[str, bool]]:
    """
    处理 orm_load_switcher 的业务逻辑
    :return: Dict[str, Dict[str, bool]]
    """
    if not _is_orm_enabled():
        return {}
    try:
        rows = await GroupFeatureSwitch.all()
        result: Dict[str, Dict[str, bool]] = {}
        for row in rows:
            result.setdefault(row.group_id, {})[row.func_name] = row.enabled
        return result
    except Exception as e:
        logger.error(f"ORM 读取开关失败: {e}")
        return {}


async def orm_save_switcher_group(gid: str, funcs: Dict[str, bool]) -> bool:
    """
    处理 orm_save_switcher_group 的业务逻辑
    :param gid: 群号
    :param funcs: 功能映射
    :return: bool
    """
    if not _is_orm_enabled():
        return False
    try:
        for func_name, enabled in funcs.items():
            await GroupFeatureSwitch.update_or_create(
                group_id=gid, func_name=func_name, defaults={"enabled": enabled}
            )
        return True
    except Exception as e:
        logger.error(f"ORM 保存开关失败: {e}")
        return False


async def orm_toggle_switch(gid: str, func_name: str) -> Optional[bool]:
    """
    处理 orm_toggle_switch 的业务逻辑
    :param gid: 群号
    :param func_name: 功能名
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None
    try:
        row, created = await GroupFeatureSwitch.get_or_create(
            group_id=gid, func_name=func_name, defaults={"enabled": False}
        )
        row.enabled = not row.enabled
        await row.save()
        return row.enabled
    except Exception as e:
        logger.error(f"ORM 切换开关失败: {e}")
        return None


async def orm_load_approval_terms() -> Optional[Dict[str, List[str]]]:
    """
    处理 orm_load_approval_terms 的业务逻辑
    :return: Optional[Dict[str, List[str]]]
    """
    if not _is_orm_enabled():
        return None
    try:
        rows = await ApprovalTerm.all()
        result: Dict[str, List[str]] = {}
        for row in rows:
            result.setdefault(row.group_id, []).append(row.term)
        return result
    except Exception as e:
        logger.error(f"ORM 读取审批词条失败: {e}")
        return {}


async def orm_add_approval_term(gid: str, term: str) -> Optional[bool]:
    """
    处理 orm_add_approval_term 的业务逻辑
    :param gid: 群号
    :param term: term 参数
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None
    try:
        _, created = await ApprovalTerm.get_or_create(group_id=gid, term=term)
        return created
    except Exception as e:
        logger.error(f"ORM 添加审批词条失败: {e}")
        return False


async def orm_delete_approval_term(gid: str, term: str) -> Optional[bool]:
    """
    处理 orm_delete_approval_term 的业务逻辑
    :param gid: 群号
    :param term: term 参数
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None
    try:
        deleted = await ApprovalTerm.filter(group_id=gid, term=term).delete()
        return deleted > 0
    except Exception as e:
        logger.error(f"ORM 删除审批词条失败: {e}")
        return False


async def orm_load_deputy_admins() -> Optional[Dict[str, List[int]]]:
    """
    处理 orm_load_deputy_admins 的业务逻辑
    :return: Optional[Dict[str, List[int]]]
    """
    if not _is_orm_enabled():
        return None
    try:
        rows = await DeputyAdmin.all()
        result: Dict[str, List[int]] = {}
        for row in rows:
            result.setdefault(row.group_id, []).append(int(row.user_id))
        return result
    except Exception as e:
        logger.error(f"ORM 读取分管列表失败: {e}")
        return {}


async def orm_add_deputy_admin(gid: str, qq: int) -> Optional[bool]:
    """
    处理 orm_add_deputy_admin 的业务逻辑
    :param gid: 群号
    :param qq: QQ 号
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None
    try:
        _, created = await DeputyAdmin.get_or_create(
            group_id=gid, user_id=str(qq)
        )
        return created
    except Exception as e:
        logger.error(f"ORM 添加分管失败: {e}")
        return False


async def orm_delete_deputy_admin(gid: str, qq: int) -> Optional[bool]:
    """
    处理 orm_delete_deputy_admin 的业务逻辑
    :param gid: 群号
    :param qq: QQ 号
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None
    try:
        deleted = await DeputyAdmin.filter(group_id=gid, user_id=str(qq)).delete()
        return deleted > 0
    except Exception as e:
        logger.error(f"ORM 删除分管失败: {e}")
        return False


async def orm_get_global_config(key: str, default: str = "") -> str:
    """
    处理 orm_get_global_config 的业务逻辑
    :param key: key 参数
    :param default: default 参数
    :return: str
    """
    if not _is_orm_enabled():
        return default
    try:
        row = await GlobalConfig.filter(key=key).first()
        return row.value if row else default
    except Exception as e:
        logger.error(f"ORM 读取全局配置失败: {e}")
        return default


async def orm_set_global_config(key: str, value: str) -> None:
    """
    处理 orm_set_global_config 的业务逻辑
    :param key: key 参数
    :param value: 值
    :return: None
    """
    if not _is_orm_enabled():
        return
    try:
        await GlobalConfig.update_or_create(key=key, defaults={"value": value})
    except Exception as e:
        logger.error(f"ORM 保存全局配置失败: {e}")


async def orm_load_approval_blacklist() -> Optional[Dict[str, List[str]]]:
    """
    处理 orm_load_approval_blacklist 的业务逻辑
    :return: Optional[Dict[str, List[str]]]
    """
    if not _is_orm_enabled():
        return None
    try:
        rows = await ApprovalBlacklistTerm.all()
        result: Dict[str, List[str]] = {}
        for row in rows:
            result.setdefault(row.group_id, []).append(row.term)
        return result
    except Exception as e:
        logger.error(f"ORM 读取审批黑名单失败: {e}")
        return {}


async def orm_add_blacklist_term(gid: str, term: str) -> Optional[bool]:
    """
    处理 orm_add_blacklist_term 的业务逻辑
    :param gid: 群号
    :param term: term 参数
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None
    try:
        _, created = await ApprovalBlacklistTerm.get_or_create(group_id=gid, term=term)
        return created
    except Exception as e:
        logger.error(f"ORM 添加黑名单词条失败: {e}")
        return False


async def orm_delete_blacklist_term(gid: str, term: str) -> Optional[bool]:
    """
    处理 orm_delete_blacklist_term 的业务逻辑
    :param gid: 群号
    :param term: term 参数
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None
    try:
        deleted = await ApprovalBlacklistTerm.filter(group_id=gid, term=term).delete()
        return deleted > 0
    except Exception as e:
        logger.error(f"ORM 删除黑名单词条失败: {e}")
        return False


async def orm_load_content_guard_rules() -> Optional[List[List[str]]]:
    """
    处理 orm_load_content_guard_rules 的业务逻辑
    :return: Optional[List[List[str]]]
    """
    if not _is_orm_enabled():
        return None
    try:
        rows = await ContentGuardRule.all()
        sorted_rows = sorted(rows, key=lambda row: (row.order_index, row.id))
        return [[row.pattern, row.options] if row.options else [row.pattern] for row in sorted_rows if row.enabled]
    except Exception as e:
        logger.error(f"ORM 读取违禁词规则失败: {e}")
        return []


async def orm_replace_content_guard_rules(rules: List[Any]) -> Optional[bool]:
    """
    处理 orm_replace_content_guard_rules 的业务逻辑
    :param rules: rules 参数
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None

    normalized_rules: List[tuple[str, str]] = []
    seen_rules: set[tuple[str, str]] = set()
    for rule in rules:
        normalized = _normalize_content_guard_rule_entry(rule)
        if normalized is None or normalized in seen_rules:
            continue
        seen_rules.add(normalized)
        normalized_rules.append(normalized)

    try:
        await ContentGuardRule.filter().delete()
        if normalized_rules:
            await ContentGuardRule.bulk_create(
                [
                    ContentGuardRule(
                        pattern=pattern,
                        options=options,
                        order_index=index,
                        enabled=True,
                    )
                    for index, (pattern, options) in enumerate(normalized_rules)
                ]
            )
        return True
    except Exception as e:
        logger.error(f"ORM 替换违禁词规则失败: {e}")
        return False


async def orm_add_content_guard_rule(pattern: str, options: str = "") -> Optional[bool]:
    """
    处理 orm_add_content_guard_rule 的业务逻辑
    :param pattern: pattern 参数
    :param options: options 参数
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None

    normalized = _normalize_content_guard_rule_entry([pattern, options])
    if normalized is None:
        return False

    normalized_pattern, normalized_options = normalized
    try:
        row = await ContentGuardRule.filter(pattern=normalized_pattern, options=normalized_options).first()
        if row is not None:
            if not row.enabled:
                row.enabled = True
                await row.save()
                return True
            return False

        rows = await ContentGuardRule.all()
        next_order = max((int(getattr(existing, "order_index", 0)) for existing in rows), default=-1) + 1
        await ContentGuardRule.create(
            pattern=normalized_pattern,
            options=normalized_options,
            order_index=next_order,
            enabled=True,
        )
        return True
    except Exception as e:
        logger.error(f"ORM 添加违禁词规则失败: {e}")
        return False


async def orm_delete_content_guard_rule(pattern: str, options: str = "") -> Optional[bool]:
    """
    处理 orm_delete_content_guard_rule 的业务逻辑
    :param pattern: pattern 参数
    :param options: options 参数
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None

    normalized = _normalize_content_guard_rule_entry([pattern, options])
    if normalized is None:
        return False

    normalized_pattern, normalized_options = normalized
    try:
        deleted = await ContentGuardRule.filter(
            pattern=normalized_pattern,
            options=normalized_options,
        ).delete()
        return deleted > 0
    except Exception as e:
        logger.error(f"ORM 删除违禁词规则失败: {e}")
        return False


async def orm_load_ai_verify_config() -> Optional[Dict[str, Dict]]:
    """
    处理 orm_load_ai_verify_config 的业务逻辑
    :return: Optional[Dict[str, Dict]]
    """
    if not _is_orm_enabled():
        return None
    try:
        rows = await AIVerifyConfig.all()
        result: Dict[str, Dict] = {}
        for row in rows:
            result[row.group_id] = {"enabled": row.enabled, "prompt": row.prompt}
        return result
    except Exception as e:
        logger.error(f"ORM 读取AI审核配置失败: {e}")
        return {}


async def orm_save_ai_verify_config(gid: str, enabled: bool, prompt: str) -> None:
    """
    处理 orm_save_ai_verify_config 的业务逻辑
    :param gid: 群号
    :param enabled: 开关状态
    :param prompt: prompt 参数
    :return: None
    """
    if not _is_orm_enabled():
        return
    try:
        await AIVerifyConfig.update_or_create(
            group_id=gid, defaults={"enabled": enabled, "prompt": prompt}
        )
    except Exception as e:
        logger.error(f"ORM 保存AI审核配置失败: {e}")


async def orm_delete_ai_verify_config(gid: str) -> None:
    """
    处理 orm_delete_ai_verify_config 的业务逻辑
    :param gid: 群号
    :return: None
    """
    if not _is_orm_enabled():
        return
    try:
        await AIVerifyConfig.filter(group_id=gid).delete()
    except Exception as e:
        logger.error(f"ORM 删除AI审核配置失败: {e}")


async def orm_load_broadcast_exclusions() -> Optional[Dict[str, List[str]]]:
    """
    处理 orm_load_broadcast_exclusions 的业务逻辑
    :return: Optional[Dict[str, List[str]]]
    """
    if not _is_orm_enabled():
        return None
    try:
        rows = await BroadcastExclusion.all()
        result: Dict[str, List[str]] = {}
        for row in rows:
            result.setdefault(row.user_id, []).append(row.group_id)
        return result
    except Exception as e:
        logger.error(f"ORM 读取广播排除失败: {e}")
        return {}


async def orm_add_broadcast_exclusion(user_id: str, group_id: str) -> Optional[bool]:
    """
    处理 orm_add_broadcast_exclusion 的业务逻辑
    :param user_id: 用户号
    :param group_id: 群号
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None
    try:
        _, created = await BroadcastExclusion.get_or_create(
            user_id=user_id, group_id=group_id
        )
        return created
    except Exception as e:
        logger.error(f"ORM 添加广播排除失败: {e}")
        return False


async def orm_remove_broadcast_exclusion(user_id: str, group_id: str) -> Optional[bool]:
    """
    处理 orm_remove_broadcast_exclusion 的业务逻辑
    :param user_id: 用户号
    :param group_id: 群号
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None
    try:
        deleted = await BroadcastExclusion.filter(user_id=user_id, group_id=group_id).delete()
        return deleted > 0
    except Exception as e:
        logger.error(f"ORM 删除广播排除失败: {e}")
        return False


async def orm_load_user_violations() -> Dict[str, Dict[str, Dict]]:
    """
    处理 orm_load_user_violations 的业务逻辑
    :return: Dict[str, Dict[str, Dict]]
    """
    if not _is_orm_enabled():
        return {}
    try:
        rows = await UserViolation.all()
        result: Dict[str, Dict[str, Dict]] = {}
        for row in rows:
            result.setdefault(row.group_id, {})[row.user_id] = {"level": row.level}
        return result
    except Exception as e:
        logger.error(f"ORM 读取违规信息失败: {e}")
        return {}


async def orm_save_user_violation(gid: str, uid: str, level: int) -> None:
    """
    处理 orm_save_user_violation 的业务逻辑
    :param gid: 群号
    :param uid: 用户号
    :param level: level 参数
    :return: None
    """
    if not _is_orm_enabled():
        return
    try:
        await UserViolation.update_or_create(
            group_id=gid, user_id=uid, defaults={"level": level}
        )
    except Exception as e:
        logger.error(f"ORM 保存违规信息失败: {e}")


async def orm_get_user_violation_level(gid: str, uid: str) -> Optional[int]:
    """
    处理 orm_get_user_violation_level 的业务逻辑
    :param gid: 群号
    :param uid: 用户号
    :return: Optional[int]
    """
    if not _is_orm_enabled():
        return None
    try:
        row = await UserViolation.filter(group_id=gid, user_id=uid).first()
        if row is None:
            return None
        return int(row.level)
    except Exception as e:
        logger.error(f"ORM 读取用户违规等级失败: {e}")
        return None


async def orm_load_violation_records(gid: str, uid: str) -> List[Dict]:
    """
    处理 orm_load_violation_records 的业务逻辑
    :param gid: 群号
    :param uid: 用户号
    :return: List[Dict]
    """
    if not _is_orm_enabled():
        return []
    try:
        rows = await ViolationRecord.filter(group_id=gid, user_id=uid).all()
        return [{"timestamp": r.timestamp, "label": r.label, "content": r.content} for r in rows]
    except Exception as e:
        logger.error(f"ORM 读取违规记录失败: {e}")
        return []


async def orm_load_group_violation_snapshot(gid: str) -> List[Dict]:
    """
    处理 orm_load_group_violation_snapshot 的业务逻辑
    :param gid: 群号
    :return: List[Dict]
    """
    if not _is_orm_enabled():
        return []
    try:
        violation_rows = await UserViolation.filter(group_id=gid).all()
        level_map: Dict[str, int] = {r.user_id: r.level for r in violation_rows}
        record_rows = await ViolationRecord.filter(group_id=gid).all()
        entries: List[Dict] = []
        for r in record_rows:
            entries.append({
                "group_id": gid,
                "user_id": r.user_id,
                "level": level_map.get(r.user_id, 0),
                "timestamp": r.timestamp,
                "label": r.label,
                "content": r.content,
            })
        return sorted(entries, key=lambda x: x["timestamp"], reverse=True)
    except Exception as e:
        logger.error(f"ORM 读取群违规快照失败: {e}")
        return []


async def orm_add_violation_record(gid: str, uid: str, timestamp: str, label: str, content: str) -> None:
    """
    记录ORMadd违规
    :param gid: 群号
    :param uid: 用户号
    :param timestamp: timestamp 参数
    :param label: label 参数
    :param content: 内容
    :return: None
    """
    if not _is_orm_enabled():
        return
    try:
        await ViolationRecord.create(
            group_id=gid, user_id=uid, timestamp=timestamp, label=label, content=content
        )
    except Exception as e:
        logger.error(f"ORM 添加违规记录失败: {e}")


async def orm_load_disabled_groups() -> List[str]:
    """
    处理 orm_load_disabled_groups 的业务逻辑
    :return: List[str]
    """
    if not _is_orm_enabled():
        return []
    try:
        rows = await StatisticsGroupRecordSetting.filter(enabled=False).all()
        return [r.group_id for r in rows]
    except Exception as e:
        logger.error(f"ORM 读取禁用记录群列表失败: {e}")
        return []


async def orm_load_record_setting_groups() -> List[str]:
    """
    处理 orm_load_record_setting_groups 的业务逻辑
    :return: List[str]
    """
    if not _is_orm_enabled():
        return []
    try:
        rows = await StatisticsGroupRecordSetting.all()
        return [r.group_id for r in rows]
    except Exception as e:
        logger.error(f"ORM 读取记录配置群列表失败: {e}")
        return []


async def orm_is_group_record_enabled(gid: str) -> Optional[bool]:
    """
    处理 orm_is_group_record_enabled 的业务逻辑
    :param gid: 群号
    :return: Optional[bool]
    """
    if not _is_orm_enabled():
        return None
    try:
        row = await StatisticsGroupRecordSetting.filter(group_id=gid).first()
        if row is None:
            return None
        return row.enabled
    except Exception as e:
        logger.error(f"ORM 读取群记录状态失败: {e}")
        return None


async def orm_enable_group_record(gid: str) -> bool:
    """
    记录ORMenable群
    :param gid: 群号
    :return: bool
    """
    if not _is_orm_enabled():
        return False
    try:
        row, created = await StatisticsGroupRecordSetting.get_or_create(
            group_id=gid, defaults={"enabled": True}
        )
        if created:
            return True
        if not row.enabled:
            row.enabled = True
            await row.save()
            return True
        return False
    except Exception as e:
        logger.error(f"ORM 启用群记录失败: {e}")
        return False


async def orm_disable_group_record(gid: str) -> bool:
    """
    记录ORMdisable群
    :param gid: 群号
    :return: bool
    """
    if not _is_orm_enabled():
        return False
    try:
        row, created = await StatisticsGroupRecordSetting.get_or_create(
            group_id=gid, defaults={"enabled": False}
        )
        if created:
            return True
        if row.enabled:
            row.enabled = False
            await row.save()
            return True
        return False
    except Exception as e:
        logger.error(f"ORM 禁用群记录失败: {e}")
        return False


async def orm_load_daily_message_stats(gid: str, stat_date: str) -> Dict[str, int]:
    """
    处理 orm_load_daily_message_stats 的业务逻辑
    :param gid: 群号
    :param stat_date: stat_date 参数
    :return: Dict[str, int]
    """
    if not _is_orm_enabled():
        return {}
    try:
        normalized_stat_date: datetime.date | str = stat_date
        try:
            normalized_stat_date = datetime.date.fromisoformat(stat_date)
        except (TypeError, ValueError):
            normalized_stat_date = stat_date
        rows = await StatisticsDailyMessageStat.filter(group_id=gid, stat_date=normalized_stat_date).all()
        return {r.user_id: r.message_count for r in rows}
    except Exception as e:
        logger.error(f"ORM 读取每日消息统计失败: {e}")
        return {}


async def orm_load_history_message_stats(gid: str) -> Dict[str, int]:
    """
    处理 orm_load_history_message_stats 的业务逻辑
    :param gid: 群号
    :return: Dict[str, int]
    """
    if not _is_orm_enabled():
        return {}
    try:
        rows = await StatisticsHistoryMessageStat.filter(group_id=gid).all()
        return {r.user_id: r.message_count for r in rows}
    except Exception as e:
        logger.error(f"ORM 读取历史消息统计失败: {e}")
        return {}


async def orm_load_daily_trend(gid: str, limit: int = 14) -> List[Dict]:
    """
    处理 orm_load_daily_trend 的业务逻辑
    :param gid: 群号
    :param limit: 数量限制
    :return: List[Dict]
    """
    if not _is_orm_enabled():
        return []
    try:
        rows = (
            await StatisticsDailyMessageStat
            .filter(group_id=gid)
            .order_by("-stat_date")
            .limit(limit * 50)
            .all()
        )
        date_map: Dict[str, Dict] = {}
        for r in rows:
            date_key = str(r.stat_date)
            entry = date_map.setdefault(date_key, {"date": date_key, "message_count": 0, "active_members": 0})
            entry["message_count"] += r.message_count
            entry["active_members"] += 1
        sorted_items = sorted(date_map.values(), key=lambda x: x["date"])
        return sorted_items[-limit:]
    except Exception as e:
        logger.error(f"ORM 读取每日趋势失败: {e}")
        return []
