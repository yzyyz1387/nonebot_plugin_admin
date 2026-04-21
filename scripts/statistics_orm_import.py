#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import nonebot

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def bootstrap() -> None:
    nonebot.init(
        statistics_orm_enabled=_env_bool("statistics_orm_enabled", True),
        statistics_orm_capture_message_content=_env_bool(
            "statistics_orm_capture_message_content", True
        ),
        tortoise_orm_db_url=os.getenv(
            "tortoise_orm_db_url",
            "sqlite:///data/admin3-statistics.db",
        ),
    )
    nonebot.load_plugin("nonebot_plugin_tortoise_orm")
    if not hasattr(nonebot, "get_plugin_config"):
        def _compat_get_plugin_config(config_cls):
            return config_cls()

        nonebot.get_plugin_config = _compat_get_plugin_config


def load_stop_words(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


async def run_import() -> None:
    bootstrap()

    from nonebot_plugin_admin.core import path as admin_path
    from nonebot_plugin_admin.core.utils import json_load_or_default
    from nonebot_plugin_admin.statistics.orm_bootstrap import ensure_statistics_orm_support
    from nonebot_plugin_admin.statistics.orm_store import (
        replace_group_stop_words,
        set_daily_message_stat,
        set_history_message_stat,
        sync_group_record_setting,
    )
    from nonebot_plugin_admin.statistics.legacy_store import (
        load_legacy_record_enabled_groups,
        load_record_disabled_groups,
    )

    if not ensure_statistics_orm_support():
        raise RuntimeError("ORM 未启用，请先确认已安装 nonebot_plugin_tortoise_orm，并在环境中开启 statistics_orm_enabled")

    legacy_enabled_groups = set(load_legacy_record_enabled_groups())
    disabled_groups = set(load_record_disabled_groups())
    discovered_groups = set(legacy_enabled_groups)
    discovered_groups.update(disabled_groups)
    imported_daily = 0
    imported_history = 0
    imported_stop_words = 0

    if admin_path.group_message_data_path.exists():
        for group_dir in sorted(admin_path.group_message_data_path.iterdir()):
            if not group_dir.is_dir():
                continue
            group_id = group_dir.name
            discovered_groups.add(group_id)

            history_stats = json_load_or_default(group_dir / "history.json", {})
            for user_id, message_count in history_stats.items():
                await set_history_message_stat(group_id, user_id, int(message_count))
                imported_history += 1

            for daily_file in sorted(group_dir.glob("*.json")):
                if daily_file.name == "history.json":
                    continue
                stat_date = daily_file.stem
                daily_stats = json_load_or_default(daily_file, {})
                for user_id, message_count in daily_stats.items():
                    await set_daily_message_stat(group_id, user_id, stat_date, int(message_count))
                    imported_daily += 1

    if admin_path.stop_words_path.exists():
        for stop_word_file in sorted(admin_path.stop_words_path.glob("*.txt")):
            group_id = stop_word_file.stem
            discovered_groups.add(group_id)
            stop_words = load_stop_words(stop_word_file)
            await replace_group_stop_words(group_id, stop_words)
            imported_stop_words += len(stop_words)

    if admin_path.words_contents_path.exists():
        for words_file in sorted(admin_path.words_contents_path.glob("*.txt")):
            discovered_groups.add(words_file.stem)

    for group_id in sorted(discovered_groups):
        await sync_group_record_setting(group_id, group_id not in disabled_groups)

    print("statistics orm import finished")
    print(
        f"groups={len(discovered_groups)} "
        f"daily_stats={imported_daily} "
        f"history_stats={imported_history} "
        f"stop_words={imported_stop_words}"
    )
    print("note: 已同步记录开关、停用词、每日统计和历史统计。")
    print("note: 旧的 config/words/*.txt 不包含用户、消息 ID 和精确时间，无法无损导入消息明细表。")


if __name__ == "__main__":
    asyncio.run(run_import())
