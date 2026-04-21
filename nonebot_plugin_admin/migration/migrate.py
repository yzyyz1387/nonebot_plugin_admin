from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from nonebot import logger

from ..core import path as admin_path
from ..core.config import plugin_config

_MIGRATION_VERSION = 1
MigrationResult = tuple[bool, int]


def _hash_file_contents(path: Path, digest: "hashlib._Hash") -> bool:
    """
    处理 _hash_file_contents 的业务逻辑
    :param path: 路径对象
    :param digest: digest 参数
    :return: bool
    """
    try:
        with path.open("rb") as file_obj:
            for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
                digest.update(chunk)
        return True
    except Exception:
        return False


def _file_md5(path: Path) -> str | None:
    """
    处理 _file_md5 的业务逻辑
    :param path: 路径对象
    :return: str | None
    """
    if not path.exists():
        return None
    if path.is_dir():
        digest = hashlib.md5()
        try:
            entries = sorted(
                path.rglob("*"),
                key=lambda entry: entry.relative_to(path).as_posix(),
            )
        except Exception:
            return None

        for entry in entries:
            rel_path = entry.relative_to(path).as_posix()
            digest.update(rel_path.encode("utf-8"))
            if entry.is_dir():
                digest.update(b"\x00dir")
                continue
            digest.update(b"\x00file")
            if not _hash_file_contents(entry, digest):
                return None
        return digest.hexdigest()

    try:
        digest = hashlib.md5()
        if not _hash_file_contents(path, digest):
            return None
        return digest.hexdigest()
    except Exception:
        return None


def _collect_migration_targets() -> list[tuple[str, Path, str]]:
    """
    收集migrationtargets
    :return: list[tuple[str, Path, str]]
    """
    targets: list[tuple[str, Path, str]] = []

    if admin_path.group_message_data_path.exists():
        for group_dir in sorted(admin_path.group_message_data_path.iterdir()):
            if not group_dir.is_dir():
                continue
            group_id = group_dir.name
            for json_file in sorted(group_dir.glob("*.json")):
                rel = f"群消息数据/{group_id}/{json_file.name}"
                targets.append((rel, json_file, "daily_stats"))

    if admin_path.words_contents_path.exists():
        for txt_file in sorted(admin_path.words_contents_path.glob("*.txt")):
            rel = f"words/{txt_file.name}"
            targets.append((rel, txt_file, "words"))

    if admin_path.stop_words_path.exists():
        for txt_file in sorted(admin_path.stop_words_path.glob("*.txt")):
            rel = f"stop_words/{txt_file.name}"
            targets.append((rel, txt_file, "stop_words"))

    if admin_path.limit_word_path.exists():
        targets.append(("违禁词.txt", admin_path.limit_word_path, "content_guard_rules"))

    if admin_path.statistics_record_state_path.exists():
        rel = "statistics_record_state.json"
        targets.append((rel, admin_path.statistics_record_state_path, "record_state"))

    if admin_path.word_path.exists():
        targets.append(("word_config.txt", admin_path.word_path, "word_config"))

    if admin_path.switcher_path.exists():
        targets.append(("开关.json", admin_path.switcher_path, "switcher"))

    if admin_path.config_admin.exists():
        targets.append(("admin.json", admin_path.config_admin, "approval_terms"))

    if admin_path.config_group_admin.exists():
        targets.append(("group_admin.json", admin_path.config_group_admin, "deputy_admins"))

    if admin_path.appr_bk.exists():
        targets.append(("加群验证信息黑名单.json", admin_path.appr_bk, "approval_blacklist"))

    ai_verify_cfg = admin_path.config_path / "ai_verify_config.json"
    if ai_verify_cfg.exists():
        targets.append(("ai_verify_config.json", ai_verify_cfg, "ai_verify_config"))

    if admin_path.broadcast_avoid_path.exists():
        targets.append(("广播排除群聊.json", admin_path.broadcast_avoid_path, "broadcast_exclusion"))

    violation_dir = admin_path.config_path / "群内用户违规信息"
    if violation_dir.exists():
        targets.append(("群内用户违规信息", violation_dir, "user_violations"))

    return targets


def has_legacy_migration_targets() -> bool:
    """
    处理 has_legacy_migration_targets 的业务逻辑
    :return: bool
    """
    return bool(_collect_migration_targets())


def has_isolated_legacy_backup() -> bool:
    """
    处理 has_isolated_legacy_backup 的业务逻辑
    :return: bool
    """
    if not admin_path.legacy_backup_path.exists():
        return False
    try:
        next(admin_path.legacy_backup_path.iterdir())
        return True
    except StopIteration:
        return False
    except Exception:
        return False


def _read_nonempty_lines(file_path: Path) -> list[str] | None:
    """
    读取nonemptylines
    :param file_path: 文件路径
    :return: list[str] | None
    """
    try:
        return [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except Exception:
        return None


def _normalize_group_ids(group_ids: Iterable[int | str]) -> list[str]:
    """
    规范化群ids
    :param group_ids: 群号列表
    :return: list[str]
    """
    normalized: list[str] = []
    seen: set[str] = set()
    for group_id in group_ids:
        normalized_group_id = str(group_id).strip()
        if not normalized_group_id or normalized_group_id in seen:
            continue
        seen.add(normalized_group_id)
        normalized.append(normalized_group_id)
    return normalized


async def _needs_migration(rel_path: str, abs_path: Path) -> bool:
    """
    处理 _needs_migration 的业务逻辑
    :param rel_path: 路径对象
    :param abs_path: 路径对象
    :return: bool
    """
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE or models.MigrationManifest is None:
        return False

    current_md5 = _file_md5(abs_path)
    if current_md5 is None:
        return False

    try:
        record = await models.MigrationManifest.filter(file_path=rel_path).first()
        if record is None:
            return True
        return record.file_md5 != current_md5
    except Exception:
        return True


async def _mark_migrated(rel_path: str, abs_path: Path) -> None:
    """
    处理 _mark_migrated 的业务逻辑
    :param rel_path: 路径对象
    :param abs_path: 路径对象
    :return: None
    """
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE or models.MigrationManifest is None:
        return

    current_md5 = _file_md5(abs_path)
    if current_md5 is None:
        return

    try:
        record = await models.MigrationManifest.filter(file_path=rel_path).first()
        if record is None:
            await models.MigrationManifest.create(
                file_path=rel_path,
                file_md5=current_md5,
                version=_MIGRATION_VERSION,
            )
        else:
            record.file_md5 = current_md5
            record.version = _MIGRATION_VERSION
            await record.save()
    except Exception as err:
        logger.warning(f"迁移记录写入失败 {rel_path}: {type(err).__name__}: {err}")


async def _has_current_manifest(rel_path: str, abs_path: Path) -> bool:
    """
    处理 _has_current_manifest 的业务逻辑
    :param rel_path: 路径对象
    :param abs_path: 路径对象
    :return: bool
    """
    from ..statistics import models

    if not abs_path.exists():
        return False
    if not models.ORM_MODELS_AVAILABLE or models.MigrationManifest is None:
        return False

    current_md5 = _file_md5(abs_path)
    if current_md5 is None:
        return False

    try:
        record = await models.MigrationManifest.filter(file_path=rel_path).first()
    except Exception:
        return False
    return record is not None and record.file_md5 == current_md5


def _build_isolation_session_root() -> Path:
    """
    构建isolationsessionroot
    :return: Path
    """
    return admin_path.legacy_backup_path / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def _resolve_isolation_destination(source_path: Path, session_root: Path) -> Path | None:
    """
    解析isolationdestination
    :param source_path: 路径对象
    :param session_root: session_root 参数
    :return: Path | None
    """
    try:
        relative_path = source_path.relative_to(admin_path.config_path)
    except ValueError:
        return None
    return session_root / relative_path


def _cleanup_empty_legacy_parents(source_path: Path) -> None:
    """
    处理 _cleanup_empty_legacy_parents 的业务逻辑
    :param source_path: 路径对象
    :return: None
    """
    current = source_path.parent
    stop_paths = {admin_path.config_path, admin_path.legacy_backup_path}
    while current not in stop_paths:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def _isolate_legacy_path(source_path: Path, session_root: Path) -> bool:
    """
    处理 _isolate_legacy_path 的业务逻辑
    :param source_path: 路径对象
    :param session_root: session_root 参数
    :return: bool
    """
    if not source_path.exists():
        return False

    destination = _resolve_isolation_destination(source_path, session_root)
    if destination is None:
        logger.warning(f"Skip isolating legacy path outside config root: {source_path}")
        return False

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source_path.rename(destination)
        _cleanup_empty_legacy_parents(source_path)
        return True
    except Exception as err:
        logger.warning(f"Legacy isolation failed for {source_path}: {type(err).__name__}: {err}")
        return False


async def _migrate_daily_stats(group_id: str, file_path: Path) -> MigrationResult:
    """
    迁移每日stats
    :param group_id: 群号
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..statistics.orm_store import set_daily_message_stat, set_history_message_stat
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return False, 0

    if not isinstance(data, dict):
        return False, 0

    count = 0
    file_name = file_path.stem

    if file_name == "history":
        for user_id, message_count in data.items():
            try:
                await set_history_message_stat(group_id, user_id, int(message_count))
                count += 1
            except Exception:
                pass
    else:
        stat_date = file_name
        for user_id, message_count in data.items():
            try:
                await set_daily_message_stat(group_id, user_id, stat_date, int(message_count))
                count += 1
            except Exception:
                pass

    return True, count


async def _migrate_stop_words(group_id: str, file_path: Path) -> MigrationResult:
    """
    迁移stop词料
    :param group_id: 群号
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..statistics.orm_store import replace_group_stop_words
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    words = _read_nonempty_lines(file_path)
    if words is None:
        return False, 0

    try:
        await replace_group_stop_words(group_id, words)
        return True, len(words)
    except Exception:
        return False, 0


async def _migrate_words(group_id: str, file_path: Path) -> MigrationResult:
    """
    迁移词料
    :param group_id: 群号
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..statistics.orm_store import replace_group_word_corpus
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    lines = _read_nonempty_lines(file_path)
    if lines is None:
        return False, 0

    try:
        await replace_group_word_corpus(group_id, lines, source_type="legacy_text")
        return True, len(lines)
    except Exception:
        return False, 0


async def _migrate_content_guard_rules(file_path: Path) -> MigrationResult:
    """
    迁移内容审核规则
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..content_guard.text_guard_flow import load_limit_rules
    from ..statistics.config_orm_store import orm_replace_content_guard_rules
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    try:
        rules = load_limit_rules(file_path)
    except Exception:
        return False, 0

    replaced = await orm_replace_content_guard_rules(rules)
    if replaced is None or replaced is False:
        return False, 0
    return True, len(rules)


async def _migrate_record_state(file_path: Path) -> MigrationResult:
    """
    迁移记录状态
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..statistics.orm_store import sync_group_record_setting
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return False, 0

    if not isinstance(data, dict):
        return False, 0

    disabled_groups = set(data.get("disabled_groups", []))
    count = 0

    from ..core import path as ap
    if ap.group_message_data_path.exists():
        for group_dir in ap.group_message_data_path.iterdir():
            if not group_dir.is_dir():
                continue
            group_id = group_dir.name
            enabled = group_id not in disabled_groups
            try:
                await sync_group_record_setting(group_id, enabled)
                count += 1
            except Exception:
                pass

    return True, count


async def _migrate_word_config(file_path: Path) -> MigrationResult:
    """
    迁移词配置
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..statistics.orm_store import sync_group_record_setting
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    enabled_groups = _read_nonempty_lines(file_path)
    if enabled_groups is None:
        return False, 0

    group_message_groups = (
        [group_dir.name for group_dir in admin_path.group_message_data_path.iterdir() if group_dir.is_dir()]
        if admin_path.group_message_data_path.exists()
        else []
    )
    word_corpus_groups = (
        [txt_file.stem for txt_file in admin_path.words_contents_path.glob("*.txt")]
        if admin_path.words_contents_path.exists()
        else []
    )
    candidate_groups = _normalize_group_ids(
        [
            *enabled_groups,
            *group_message_groups,
            *word_corpus_groups,
        ]
    )
    enabled_set = set(_normalize_group_ids(enabled_groups))

    count = 0
    for group_id in candidate_groups:
        try:
            await sync_group_record_setting(group_id, group_id in enabled_set)
            count += 1
        except Exception:
            pass

    return True, count


async def _migrate_switcher(file_path: Path) -> MigrationResult:
    """
    迁移开关
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..statistics.config_orm_store import orm_save_switcher_group
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return False, 0

    if not isinstance(data, dict):
        return False, 0

    count = 0
    for gid, funcs in data.items():
        if not isinstance(funcs, dict):
            continue
        try:
            saved = await orm_save_switcher_group(gid, funcs)
            if saved:
                count += 1
        except Exception:
            pass

    return count > 0, count


async def _migrate_approval_terms(file_path: Path) -> MigrationResult:
    """
    迁移审批词条
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..statistics.config_orm_store import orm_add_approval_term
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return False, 0

    if not isinstance(data, dict):
        return False, 0

    count = 0
    for gid, terms in data.items():
        if not isinstance(terms, list):
            continue
        for term in terms:
            try:
                await orm_add_approval_term(gid, str(term))
                count += 1
            except Exception:
                pass

    return True, count


async def _migrate_deputy_admins(file_path: Path) -> MigrationResult:
    """
    迁移deputy管理员
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..statistics.config_orm_store import orm_add_deputy_admin, orm_set_global_config
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return False, 0

    if not isinstance(data, dict):
        return False, 0

    count = 0
    for gid, admins in data.items():
        if gid == "su":
            try:
                await orm_set_global_config("approval_su_notice", str(admins))
                count += 1
            except Exception:
                pass
            continue
        if not isinstance(admins, list):
            continue
        for qq in admins:
            try:
                await orm_add_deputy_admin(gid, int(qq))
                count += 1
            except Exception:
                pass

    return True, count


async def _migrate_approval_blacklist(file_path: Path) -> MigrationResult:
    """
    迁移审批黑名单
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..statistics.config_orm_store import orm_add_blacklist_term
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return False, 0

    if not isinstance(data, dict):
        return False, 0

    count = 0
    for gid, terms in data.items():
        if not isinstance(terms, list):
            continue
        for term in terms:
            try:
                await orm_add_blacklist_term(gid, str(term))
                count += 1
            except Exception:
                pass

    return True, count


async def _migrate_ai_verify_config(file_path: Path) -> MigrationResult:
    """
    迁移aiverify配置
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..statistics.config_orm_store import orm_save_ai_verify_config
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return False, 0

    if not isinstance(data, dict):
        return False, 0

    count = 0
    for gid, cfg in data.items():
        if not isinstance(cfg, dict):
            continue
        try:
            await orm_save_ai_verify_config(gid, cfg.get("enabled", False), cfg.get("prompt", ""))
            count += 1
        except Exception:
            pass

    return True, count


async def _migrate_broadcast_exclusion(file_path: Path) -> MigrationResult:
    """
    迁移broadcastexclusion
    :param file_path: 文件路径
    :return: MigrationResult
    """
    from ..statistics.config_orm_store import orm_add_broadcast_exclusion
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return False, 0

    if not isinstance(data, dict):
        return False, 0

    count = 0
    for user_id, group_ids in data.items():
        if not isinstance(group_ids, list):
            continue
        for gid in group_ids:
            try:
                await orm_add_broadcast_exclusion(str(user_id), str(gid))
                count += 1
            except Exception:
                pass

    return True, count


async def _migrate_user_violations(dir_path: Path) -> MigrationResult:
    """
    迁移userviolations
    :param dir_path: 路径对象
    :return: MigrationResult
    """
    from ..statistics.config_orm_store import orm_save_user_violation, orm_add_violation_record
    from ..statistics import models

    if not models.ORM_MODELS_AVAILABLE:
        return False, 0

    if not dir_path.is_dir():
        return False, 0

    count = 0
    for group_dir in dir_path.iterdir():
        if not group_dir.is_dir():
            continue
        gid = group_dir.name
        for user_file in group_dir.glob("*.json"):
            uid = user_file.stem
            try:
                data = json.loads(user_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            if not isinstance(data, dict):
                continue

            level = 0
            info = data.get(uid, data)
            if isinstance(info, dict):
                level = info.get("level", 0)
                await orm_save_user_violation(gid, uid, level)
                count += 1
                records = info.get("info", {})
                if isinstance(records, dict):
                    for ts, details in records.items():
                        if isinstance(details, list) and len(details) >= 2:
                            await orm_add_violation_record(gid, uid, str(ts), str(details[0]), str(details[1]))
                            count += 1

    return True, count


async def _execute_migration(data_type: str, abs_path: Path) -> MigrationResult:
    """
    处理 _execute_migration 的业务逻辑
    :param data_type: data_type 参数
    :param abs_path: 路径对象
    :return: MigrationResult
    """
    if data_type == "daily_stats":
        return await _migrate_daily_stats(abs_path.parent.name, abs_path)
    if data_type == "words":
        return await _migrate_words(abs_path.stem, abs_path)
    if data_type == "stop_words":
        return await _migrate_stop_words(abs_path.stem, abs_path)
    if data_type == "content_guard_rules":
        return await _migrate_content_guard_rules(abs_path)
    if data_type == "record_state":
        return await _migrate_record_state(abs_path)
    if data_type == "word_config":
        return await _migrate_word_config(abs_path)
    if data_type == "switcher":
        return await _migrate_switcher(abs_path)
    if data_type == "approval_terms":
        return await _migrate_approval_terms(abs_path)
    if data_type == "deputy_admins":
        return await _migrate_deputy_admins(abs_path)
    if data_type == "approval_blacklist":
        return await _migrate_approval_blacklist(abs_path)
    if data_type == "ai_verify_config":
        return await _migrate_ai_verify_config(abs_path)
    if data_type == "broadcast_exclusion":
        return await _migrate_broadcast_exclusion(abs_path)
    if data_type == "user_violations":
        return await _migrate_user_violations(abs_path)
    return False, 0


async def run_migration_check() -> None:
    """
    执行migrationcheck
    :return: None
    """
    if not plugin_config.statistics_orm_enabled:
        return

    from ..statistics.orm_bootstrap import ensure_statistics_orm_support
    from ..statistics import models

    if not ensure_statistics_orm_support():
        return

    if not models.ORM_MODELS_AVAILABLE or models.MigrationManifest is None:
        return

    targets = _collect_migration_targets()
    pending: list[tuple[str, Path, str]] = []

    for rel_path, abs_path, data_type in targets:
        if await _needs_migration(rel_path, abs_path):
            pending.append((rel_path, abs_path, data_type))

    total_records = 0
    migrated_files = 0
    isolated_files = 0

    if pending:
        logger.info(f"数据迁移检查：发现 {len(pending)} 个文件需要迁移")
        for rel_path, abs_path, data_type in pending:
            try:
                migrated, records = await _execute_migration(data_type, abs_path)
                if not migrated:
                    logger.warning(f"数据迁移失败 {rel_path}: 未能将旧文件内容写入 ORM")
                    continue

                total_records += records
                await _mark_migrated(rel_path, abs_path)
                migrated_files += 1
            except Exception as err:
                logger.warning(f"数据迁移失败 {rel_path}: {type(err).__name__}: {err}")
    else:
        logger.debug("数据迁移检查完成：无待迁移文件")

    isolation_candidates: list[tuple[str, Path]] = []
    for rel_path, abs_path, _ in targets:
        if await _has_current_manifest(rel_path, abs_path):
            isolation_candidates.append((rel_path, abs_path))

    if isolation_candidates:
        session_root = _build_isolation_session_root()
        for rel_path, abs_path in isolation_candidates:
            if _isolate_legacy_path(abs_path, session_root):
                isolated_files += 1
                logger.info(f"Legacy source isolated: {rel_path}")

    if pending or isolated_files:
        logger.info(
            f"数据迁移完成：{migrated_files}/{len(pending)} 个文件已处理，共 {total_records} 条记录；"
            f"已隔离 {isolated_files} 个旧文件"
        )


async def _legacy_run_migration_check() -> None:
    """
    检查旧版runmigration
    :return: None
    """
    if not plugin_config.statistics_orm_enabled:
        return

    from ..statistics.orm_bootstrap import ensure_statistics_orm_support
    from ..statistics import models

    if not ensure_statistics_orm_support():
        return

    if not models.ORM_MODELS_AVAILABLE or models.MigrationManifest is None:
        return

    targets = _collect_migration_targets()
    pending: list[tuple[str, Path, str]] = []

    for rel_path, abs_path, data_type in targets:
        if await _needs_migration(rel_path, abs_path):
            pending.append((rel_path, abs_path, data_type))

    if not pending:
        logger.debug("数据迁移检查完成：无待迁移文件")
        return

    logger.info(f"数据迁移检查：发现 {len(pending)} 个文件需要迁移")
    total_records = 0
    migrated_files = 0

    for rel_path, abs_path, data_type in pending:
        try:
            migrated, records = await _execute_migration(data_type, abs_path)
            if not migrated:
                logger.warning(f"数据迁移失败 {rel_path}: 未能将旧文件内容写入 ORM")
                continue

            total_records += records
            await _mark_migrated(rel_path, abs_path)
            migrated_files += 1
        except Exception as err:
            logger.warning(f"数据迁移失败 {rel_path}: {type(err).__name__}: {err}")

    logger.info(f"数据迁移完成：{migrated_files}/{len(pending)} 个文件已处理，共 {total_records} 条记录")
