#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import importlib.util
import json
import sys
import tempfile
import types
import warnings
from pathlib import Path

import nonebot

from _fake_orm import install_fake_orm_modules


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "nonebot_plugin_admin"
PKG_NAME = "_final_acceptance_pkg"

warnings.filterwarnings(
    "ignore",
    message="You seem to already have a custom sys.excepthook handler installed.*",
    category=RuntimeWarning,
)


class FakeBot:
    def __init__(self):
        self.self_id = 10000
        self.sent_messages = []
        self._groups = [
            {
                "group_id": 12345,
                "group_name": "迁移测试群",
                "member_count": 88,
                "max_member_count": 500,
            },
            {
                "group_id": 23456,
                "group_name": "运行时默认群",
                "member_count": 42,
                "max_member_count": 200,
            },
        ]

    async def get_group_list(self):
        return [dict(item) for item in self._groups]

    async def send_msg(self, **kwargs):
        self.sent_messages.append(kwargs)
        return kwargs

    async def send_group_msg(self, **kwargs):
        return kwargs


def bootstrap_package():
    nonebot.init(
        superusers={"10000"},
        host="127.0.0.1",
        port=8080,
        send_group_id='["12345"]',
        send_switch_morning=False,
        send_switch_night=False,
        statistics_orm_enabled=True,
        statistics_orm_capture_message_content=True,
    )
    nonebot.require = lambda name: None
    install_fake_orm_modules()

    if not hasattr(nonebot, "get_plugin_config"):
        def _compat_get_plugin_config(config_cls):
            return config_cls()

        nonebot.get_plugin_config = _compat_get_plugin_config

    if "pyppeteer" not in sys.modules:
        pyppeteer = types.ModuleType("pyppeteer")

        async def _fake_launch(*args, **kwargs):
            raise RuntimeError("pyppeteer is not available in final acceptance check")

        pyppeteer.launch = _fake_launch
        sys.modules["pyppeteer"] = pyppeteer

    package = types.ModuleType(PKG_NAME)
    package.__path__ = [str(PACKAGE_DIR)]
    sys.modules[PKG_NAME] = package

    util_package = types.ModuleType(f"{PKG_NAME}.util")
    util_package.__path__ = [str(PACKAGE_DIR / "util")]
    sys.modules[f"{PKG_NAME}.util"] = util_package

    core_package = types.ModuleType(f"{PKG_NAME}.core")
    core_package.__path__ = [str(PACKAGE_DIR / "core")]
    sys.modules[f"{PKG_NAME}.core"] = core_package


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_package():
    spec = importlib.util.spec_from_file_location(
        PKG_NAME,
        PACKAGE_DIR / "__init__.py",
        submodule_search_locations=[str(PACKAGE_DIR)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PKG_NAME] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def patch_paths(path_module, temp_root: Path):
    config_path = temp_root / "config"
    res_path = temp_root / "resource"

    path_module.config_path = config_path
    path_module.legacy_backup_path = config_path / "legacy_backup"
    path_module.config_admin = config_path / "admin.json"
    path_module.config_group_admin = config_path / "group_admin.json"
    path_module.word_path = config_path / "word_config.txt"
    path_module.statistics_record_state_path = config_path / "statistics_record_state.json"
    path_module.words_contents_path = config_path / "words"
    path_module.res_path = res_path
    path_module.re_img_path = res_path / "imgs"
    path_module.ttf_name = res_path / "msyhblod.ttf"
    path_module.ttf_path = res_path / "msyhblod.ttf"
    path_module.limit_word_path = config_path / "违禁词.txt"
    path_module.switcher_path = config_path / "开关.json"
    path_module.template_path = config_path / "template"
    path_module.stop_words_path = config_path / "stop_words"
    path_module.wordcloud_bg_path = config_path / "wordcloud_bg"
    path_module.user_violation_info_path = config_path / "群内用户违规信息"
    path_module.group_message_data_path = config_path / "群消息数据"
    path_module.error_path = config_path / "admin插件错误数据"
    path_module.broadcast_avoid_path = config_path / "广播排除群聊.json"
    path_module.summary_path = config_path / "summary"
    path_module.kick_lock_path = config_path / "kick_lock"
    path_module.appr_bk = config_path / "加群验证信息黑名单.json"


async def fake_mk(type_, path_, *mode, **kwargs):
    path = Path(path_)
    if type_ == "dir":
        path.mkdir(parents=True, exist_ok=True)
        return

    if type_ != "file":
        raise ValueError(type_)

    path.parent.mkdir(parents=True, exist_ok=True)
    file_mode = mode[0] if mode else "w"
    if "url" in kwargs:
        if file_mode == "wb":
            path.write_bytes(b"dummy")
        else:
            default_text = kwargs.get("content") or "placeholder\n"
            path.write_text(default_text, encoding="utf-8")
        return

    content = kwargs.get("content", b"" if file_mode == "wb" else "")
    if file_mode == "wb":
        data = content if isinstance(content, (bytes, bytearray)) else str(content).encode("utf-8")
        path.write_bytes(data)
    else:
        path.write_text(str(content), encoding="utf-8")


def seed_admin2_legacy_data(path_module) -> None:
    path_module.config_path.mkdir(parents=True, exist_ok=True)
    path_module.words_contents_path.mkdir(parents=True, exist_ok=True)
    path_module.stop_words_path.mkdir(parents=True, exist_ok=True)
    path_module.group_message_data_path.mkdir(parents=True, exist_ok=True)
    path_module.user_violation_info_path.mkdir(parents=True, exist_ok=True)

    path_module.config_admin.write_text(
        json.dumps(
            {
                "12345": ["诚朴勇毅", "园林2502"],
                "34567": ["老群审批词"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    path_module.config_group_admin.write_text(
        json.dumps(
            {
                "su": "False",
                "12345": [20001, 20002],
                "34567": [30001],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (path_module.config_path / "ai_verify_config.json").write_text(
        json.dumps(
            {
                "12345": {"enabled": True, "prompt": "严格审核"},
                "34567": {"enabled": False, "prompt": "备用规则"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    path_module.appr_bk.write_text(
        json.dumps(
            {
                "12345": ["小号", "广告"],
                "34567": ["测试黑名单"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    path_module.broadcast_avoid_path.write_text(
        json.dumps(
            {
                "10000": ["12345"],
                "20000": ["12345", "34567"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    path_module.switcher_path.write_text(
        json.dumps(
            {
                "12345": {
                    "admin": False,
                    "requests": True,
                    "img_check": True,
                    "group_recall": True,
                },
                "34567": {
                    "requests": False,
                    "particular_e_notice": True,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    path_module.limit_word_path.write_text(
        "广告\t$撤回\n刷单\t$禁言$仅限123456\n",
        encoding="utf-8",
    )
    (path_module.stop_words_path / "12345.txt").write_text(
        "屏蔽词A\n屏蔽词B\n",
        encoding="utf-8",
    )
    (path_module.stop_words_path / "34567.txt").write_text(
        "离线停用词\n",
        encoding="utf-8",
    )

    group_12345_dir = path_module.group_message_data_path / "12345"
    group_12345_dir.mkdir(parents=True, exist_ok=True)
    (group_12345_dir / "2026-04-20.json").write_text(
        json.dumps({"20001": 5, "20002": 2}, ensure_ascii=False),
        encoding="utf-8",
    )
    (group_12345_dir / "history.json").write_text(
        json.dumps({"20001": 8, "20002": 3}, ensure_ascii=False),
        encoding="utf-8",
    )

    group_34567_dir = path_module.group_message_data_path / "34567"
    group_34567_dir.mkdir(parents=True, exist_ok=True)
    (group_34567_dir / "2026-04-20.json").write_text(
        json.dumps({"30001": 1}, ensure_ascii=False),
        encoding="utf-8",
    )
    (group_34567_dir / "history.json").write_text(
        json.dumps({"30001": 1}, ensure_ascii=False),
        encoding="utf-8",
    )

    (path_module.words_contents_path / "12345.txt").write_text(
        "第一条旧词料\n第二条旧词料\n",
        encoding="utf-8",
    )
    (path_module.words_contents_path / "34567.txt").write_text(
        "离线群词料\n",
        encoding="utf-8",
    )
    path_module.word_path.write_text("12345\n", encoding="utf-8")

    legacy_violation_dir = path_module.user_violation_info_path / "12345"
    legacy_violation_dir.mkdir(parents=True, exist_ok=True)
    (legacy_violation_dir / "20001.json").write_text(
        json.dumps(
            {
                "20001": {
                    "level": 2,
                    "info": {
                        "2026-04-20T10:00:00": ["Spam", "legacy violation"],
                    },
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


async def run_checks():
    bootstrap_package()
    path_module = load_module(f"{PKG_NAME}.core.path", PACKAGE_DIR / "core" / "path.py")

    with tempfile.TemporaryDirectory(prefix="final-acceptance-") as temp_dir:
        temp_root = Path(temp_dir)
        patch_paths(path_module, temp_root)
        seed_admin2_legacy_data(path_module)

        package = load_package()
        fake_bot = FakeBot()

        nonebot.get_bots = lambda: {str(fake_bot.self_id): fake_bot}
        package.utils.nonebot.get_bots = nonebot.get_bots
        package.utils.mk = fake_mk

        await package.utils.init()
        await package.switcher.switcher_integrity_check(fake_bot)
        await package.run_migration_check()
        notified = await package.notify_legacy_text_upgrade(fake_bot)

        approval_store = sys.modules[f"{PKG_NAME}.approval.approval_store"]
        approval_blacklist_store = sys.modules[f"{PKG_NAME}.approval.approval_blacklist_store"]
        ai_verify_store = sys.modules[f"{PKG_NAME}.approval.ai_verify_store"]
        broadcast_store = sys.modules[f"{PKG_NAME}.broadcasting.broadcast_store"]
        switcher_module = sys.modules[f"{PKG_NAME}.core.switcher"]
        text_guard_flow = sys.modules[f"{PKG_NAME}.content_guard.text_guard_flow"]
        dashboard_service = sys.modules[f"{PKG_NAME}.dashboard.dashboard_service"]
        statistics_read_service = sys.modules[f"{PKG_NAME}.statistics.statistics_read_service"]
        statistics_store = sys.modules[f"{PKG_NAME}.statistics.statistics_store"]
        config_orm_store = sys.modules[f"{PKG_NAME}.statistics.config_orm_store"]
        orm_models = sys.modules[f"{PKG_NAME}.statistics.models"]

        assert notified is True
        assert len(fake_bot.sent_messages) == 1
        upgrade_notice = str(fake_bot.sent_messages[0]["message"])
        assert "tortoise_orm_db_url" in upgrade_notice
        assert "statistics_orm_enabled=true" in upgrade_notice
        assert "dashboard_enabled=true" in upgrade_notice
        assert "dashboard_frontend_enabled=true" in upgrade_notice
        assert "dashboard_api_token" in upgrade_notice
        assert "X-Admin-Token" in upgrade_notice
        assert "http://127.0.0.1:8080/admin-dashboard" in upgrade_notice

        approval_terms = await config_orm_store.orm_load_approval_terms()
        assert approval_terms == {
            "12345": ["诚朴勇毅", "园林2502"],
            "34567": ["老群审批词"],
        }

        deputy_admins = await approval_store.g_admin_async()
        assert deputy_admins["12345"] == [20001, 20002]
        assert deputy_admins["34567"] == [30001]
        assert deputy_admins["su"] == "False"

        blacklist_terms = await approval_blacklist_store.load_blacklist()
        assert blacklist_terms == {
            "12345": ["小号", "广告"],
            "34567": ["测试黑名单"],
        }

        ai_verify_config = await ai_verify_store.load_config()
        assert ai_verify_config == {
            "12345": {"enabled": True, "prompt": "严格审核"},
            "34567": {"enabled": False, "prompt": "备用规则"},
        }

        broadcast_config = await broadcast_store.load_broadcast_config(["10000"])
        assert broadcast_config == {
            "10000": ["12345"],
            "20000": ["12345", "34567"],
        }

        switcher_12345 = await switcher_module._load_group_switcher("12345")
        assert switcher_12345["admin"] is False
        assert switcher_12345["requests"] is True
        assert switcher_12345["img_check"] is True
        assert switcher_12345["group_recall"] is True

        switcher_34567 = await switcher_module._load_group_switcher("34567")
        assert switcher_34567["requests"] is False
        assert switcher_34567["particular_e_notice"] is True

        assert await text_guard_flow.load_runtime_limit_rules() == [
            ["广告", "$撤回"],
            ["刷单", "$禁言$仅限123456"],
        ]
        assert await text_guard_flow.check_runtime_text_message("这里有广告", 12345) == (True, False, "广告")
        assert await text_guard_flow.check_runtime_text_message("刷单进群", 123456) == (False, True, "刷单")
        assert await text_guard_flow.check_runtime_text_message("刷单进群", 234567) == (False, False, None)

        assert await statistics_read_service.load_group_stop_words_snapshot("12345") == ["屏蔽词A", "屏蔽词B"]
        assert await statistics_read_service.load_group_stop_words_snapshot("34567") == ["离线停用词"]
        assert await statistics_read_service.load_group_word_text_snapshot("12345") == "第一条旧词料\n第二条旧词料\n"
        assert await statistics_read_service.load_group_word_text_snapshot("34567") == "离线群词料\n"
        assert await statistics_read_service.load_daily_message_stats_snapshot("12345", "2026-04-20") == {
            "20001": 5,
            "20002": 2,
        }
        assert await statistics_read_service.load_history_message_stats_snapshot("12345") == {
            "20001": 8,
            "20002": 3,
        }
        assert await statistics_store.is_group_record_enabled("12345") is True
        assert await statistics_store.is_group_record_enabled("34567") is False

        violation_snapshot = await config_orm_store.orm_load_user_violations()
        assert violation_snapshot["12345"]["20001"]["level"] == 2
        assert await config_orm_store.orm_load_violation_records("12345", "20001") == [
            {
                "timestamp": "2026-04-20T10:00:00",
                "label": "Spam",
                "content": "legacy violation",
            }
        ]

        migrated_paths = {record.file_path for record in orm_models.MigrationManifest._records}
        assert migrated_paths == {
            "群消息数据/12345/2026-04-20.json",
            "群消息数据/12345/history.json",
            "群消息数据/34567/2026-04-20.json",
            "群消息数据/34567/history.json",
            "words/12345.txt",
            "words/34567.txt",
            "stop_words/12345.txt",
            "stop_words/34567.txt",
            "违禁词.txt",
            "word_config.txt",
            "开关.json",
            "admin.json",
            "group_admin.json",
            "加群验证信息黑名单.json",
            "ai_verify_config.json",
            "广播排除群聊.json",
            "群内用户违规信息",
        }

        assert not path_module.config_admin.exists()
        assert not path_module.config_group_admin.exists()
        assert not path_module.switcher_path.exists()
        assert not path_module.limit_word_path.exists()
        assert not path_module.word_path.exists()
        assert not path_module.broadcast_avoid_path.exists()
        assert not path_module.appr_bk.exists()
        assert not (path_module.config_path / "ai_verify_config.json").exists()
        assert not path_module.words_contents_path.exists()
        assert not path_module.stop_words_path.exists()
        assert not path_module.group_message_data_path.exists()
        assert not path_module.user_violation_info_path.exists()

        backup_sessions = [item for item in path_module.legacy_backup_path.iterdir() if item.is_dir()]
        assert len(backup_sessions) == 1
        backup_root = backup_sessions[0]
        assert (backup_root / "admin.json").exists()
        assert (backup_root / "group_admin.json").exists()
        assert (backup_root / "开关.json").exists()
        assert (backup_root / "违禁词.txt").exists()
        assert (backup_root / "word_config.txt").exists()
        assert (backup_root / "ai_verify_config.json").exists()
        assert (backup_root / "广播排除群聊.json").exists()
        assert (backup_root / "加群验证信息黑名单.json").exists()
        assert (backup_root / "words" / "12345.txt").exists()
        assert (backup_root / "words" / "34567.txt").exists()
        assert (backup_root / "stop_words" / "12345.txt").exists()
        assert (backup_root / "stop_words" / "34567.txt").exists()
        assert (backup_root / "群消息数据" / "12345" / "history.json").exists()
        assert (backup_root / "群消息数据" / "34567" / "2026-04-20.json").exists()
        assert (backup_root / "群内用户违规信息" / "12345" / "20001.json").exists()

        await package.utils.init()
        assert not path_module.words_contents_path.exists()
        assert not path_module.stop_words_path.exists()
        assert not path_module.group_message_data_path.exists()

        dashboard_group_ids = await dashboard_service.collect_dashboard_group_ids_live()
        assert "12345" in dashboard_group_ids
        assert "23456" in dashboard_group_ids
        assert "34567" in dashboard_group_ids

        group_summaries = await dashboard_service.list_group_summaries_payload()
        summary_map = {item["group_id"]: item for item in group_summaries}
        assert summary_map["12345"]["history_message_count"] == 11
        assert summary_map["12345"]["today_message_count"] == 0
        assert summary_map["12345"]["latest_stat_date"] == "2026-04-20"
        assert summary_map["12345"]["approval_terms_count"] == 2
        assert summary_map["12345"]["approval_blacklist_count"] == 2
        assert summary_map["12345"]["content_guard_rule_count"] == 1
        assert summary_map["12345"]["violation_event_count"] == 1
        assert summary_map["34567"]["history_message_count"] == 1
        assert summary_map["34567"]["today_message_count"] == 0
        assert summary_map["34567"]["latest_stat_date"] == "2026-04-20"
        assert summary_map["34567"]["content_guard_rule_count"] == 1
        assert summary_map["34567"]["record_enabled"] is False

        manifest_count_before = len(orm_models.MigrationManifest._records)
        word_corpus_count_before = len(orm_models.StatisticsWordCorpus._records)
        history_count_before = len(orm_models.StatisticsHistoryMessageStat._records)
        violation_count_before = len(orm_models.ViolationRecord._records)

        await package.run_migration_check()
        notified_again = await package.notify_legacy_text_upgrade(fake_bot)

        assert len(orm_models.MigrationManifest._records) == manifest_count_before
        assert len(orm_models.StatisticsWordCorpus._records) == word_corpus_count_before
        assert len(orm_models.StatisticsHistoryMessageStat._records) == history_count_before
        assert len(orm_models.ViolationRecord._records) == violation_count_before
        assert notified_again is False
        assert len(fake_bot.sent_messages) == 1

    print("final acceptance check passed")


if __name__ == "__main__":
    asyncio.run(run_checks())
