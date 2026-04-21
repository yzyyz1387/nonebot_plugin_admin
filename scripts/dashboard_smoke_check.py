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
from fastapi.testclient import TestClient

from _fake_orm import install_fake_orm_modules


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "nonebot_plugin_admin"
PKG_NAME = "_dashboard_smoke_pkg"
ADMIN_WEB_DIST_DIR = PACKAGE_DIR / "admin-web" / "dist"

warnings.filterwarnings(
    "ignore",
    message="You seem to already have a custom sys.excepthook handler installed.*",
    category=RuntimeWarning,
)


class FakeBot:
    def __init__(self):
        self.self_id = 10000
        self.sent_group_messages = []
        self.muted_members = []
        self.kicked_members = []
        self.special_titles = []

    async def get_group_list(self):
        return [
            {"group_id": 12345, "group_name": "Smoke Group", "member_count": 128, "max_member_count": 500},
            {"group_id": 23456, "group_name": "Config Only Group", "member_count": 42, "max_member_count": 200},
        ]

    async def send_msg(self, **kwargs):
        return kwargs

    async def send_group_msg(self, **kwargs):
        self.sent_group_messages.append(kwargs)
        return kwargs

    async def get_group_member_info(self, group_id: int, user_id: int):
        profiles = {
            10000: {"card": "SmokeBot", "nickname": "SmokeBot", "role": "owner", "title": "Bot Owner"},
            20001: {"card": "Alice", "nickname": "Alice", "role": "admin", "title": "Admin"},
            20002: {"card": "", "nickname": "Bob", "role": "member", "title": ""},
        }
        return profiles.get(user_id, {"card": "", "nickname": str(user_id)})

    async def get_group_member_list(self, group_id: int):
        return [
            {
                "user_id": 10000,
                "nickname": "SmokeBot",
                "card": "SmokeBot",
                "role": "owner",
                "title": "Bot Owner",
                "level": 12,
                "last_sent_time": 1710000100,
            },
            {
                "user_id": 20001,
                "nickname": "Alice",
                "card": "Alice",
                "role": "admin",
                "title": "Admin",
                "level": 9,
                "last_sent_time": 1710000200,
            },
            {
                "user_id": 20002,
                "nickname": "Bob",
                "card": "",
                "role": "member",
                "title": "",
                "level": 3,
                "last_sent_time": 1710000300,
            },
        ]

    async def set_group_ban(self, **kwargs):
        self.muted_members.append(kwargs)
        return kwargs

    async def set_group_kick(self, **kwargs):
        self.kicked_members.append(kwargs)
        return kwargs

    async def set_group_special_title(self, **kwargs):
        self.special_titles.append(kwargs)
        return kwargs


def bootstrap_package():
    nonebot.init(
        superusers={"10000"},
        host="127.0.0.1",
        port=8080,
        send_group_id='["12345"]',
        send_switch_morning=False,
        send_switch_night=False,
        dashboard_enabled=True,
        dashboard_frontend_enabled=True,
        dashboard_base_path="/ops",
        dashboard_api_token="smoke-token",
        dashboard_title="Ops Console",
        dashboard_log_file_path="runtime/app.log",
        statistics_orm_enabled=True,
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
            raise RuntimeError("pyppeteer is not available in dashboard smoke check")

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
    path_module.words_contents_path = config_path / "words"
    path_module.res_path = res_path
    path_module.re_img_path = res_path / "imgs"
    path_module.ttf_name = res_path / "msyhblod.ttf"
    path_module.limit_word_path = config_path / "limit_words.txt"
    path_module.switcher_path = config_path / "switcher.json"
    path_module.template_path = config_path / "template"
    path_module.stop_words_path = config_path / "stop_words"
    path_module.wordcloud_bg_path = config_path / "wordcloud_bg"
    path_module.user_violation_info_path = config_path / "user_violation"
    path_module.group_message_data_path = config_path / "group_message_data"
    path_module.error_path = config_path / "error_data"
    path_module.broadcast_avoid_path = config_path / "broadcast_avoid.json"
    path_module.ttf_path = res_path / "msyhblod.ttf"
    path_module.summary_path = config_path / "summary"
    path_module.kick_lock_path = config_path / "kick_lock"
    path_module.appr_bk = config_path / "approval_blacklist.json"


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
            path.write_text(kwargs.get("content") or "placeholder\n", encoding="utf-8")
        return

    content = kwargs.get("content", b"" if file_mode == "wb" else "")
    if file_mode == "wb":
        data = content if isinstance(content, (bytes, bytearray)) else str(content).encode("utf-8")
        path.write_bytes(data)
    else:
        path.write_text(str(content), encoding="utf-8")


async def run_checks():
    bootstrap_package()
    path_module = load_module(f"{PKG_NAME}.core.path", PACKAGE_DIR / "core" / "path.py")

    with tempfile.TemporaryDirectory(prefix="dashboard-smoke-") as temp_dir:
        temp_root = Path(temp_dir)
        patch_paths(path_module, temp_root)

        package = load_package()
        fake_bot = FakeBot()
        runtime_log_path = temp_root / "runtime" / "app.log"
        runtime_log_path.parent.mkdir(parents=True, exist_ok=True)
        runtime_log_path.write_text(
            "\n".join(
                [
                    "2026-04-19 15:20:00 [INFO] runtime | dashboard smoke started",
                    "2026-04-19 15:21:00 [WARNING] runtime | queue is slow",
                    "2026-04-19 15:22:00 [ERROR] runtime | sample crash trace",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        config_module = sys.modules[f"{PKG_NAME}.core.config"]
        config_module.plugin_config.dashboard_log_file_path = str(runtime_log_path)

        nonebot.get_bots = lambda: {str(fake_bot.self_id): fake_bot}
        package.utils.nonebot.get_bots = nonebot.get_bots
        package.utils.mk = fake_mk

        await package.utils.init()
        await package.switcher.switcher_integrity_check(fake_bot)

        statistics_record_flow = sys.modules[f"{PKG_NAME}.statistics.statistics_record_flow"]
        stop_words_flow = sys.modules[f"{PKG_NAME}.statistics.stop_words_flow"]
        approval_store = sys.modules[f"{PKG_NAME}.approval.approval_store"]
        approval_blacklist_store = sys.modules[f"{PKG_NAME}.approval.approval_blacklist_store"]
        ai_verify_store = sys.modules[f"{PKG_NAME}.approval.ai_verify_store"]
        broadcast_store = sys.modules[f"{PKG_NAME}.broadcasting.broadcast_store"]
        config_orm_store = sys.modules[f"{PKG_NAME}.statistics.config_orm_store"]
        dashboard_api = sys.modules[f"{PKG_NAME}.dashboard.dashboard_api"]

        await statistics_record_flow.handle_enable_group_recording("12345")
        await statistics_record_flow.record_group_message(
            "12345",
            "20001",
            "First smoke message",
            "2026-04-18",
            message_id="m1",
            created_at="2026-04-18T10:15:00",
        )
        await statistics_record_flow.record_group_message(
            "12345",
            "20002",
            "Second smoke message",
            "2026-04-18",
            message_id="m2",
            created_at="2026-04-18T11:00:00",
        )
        await statistics_record_flow.record_group_message(
            "12345",
            "20001",
            "Third smoke message",
            "2026-04-17",
            message_id="m3",
            created_at="2026-04-17T21:35:00",
        )
        await statistics_record_flow.record_group_message(
            "12345",
            "20002",
            "链接：https://www.baidu.com 哈哈哈哈哈测试",
            "2026-04-18",
            message_id="m4",
            created_at="2026-04-18T11:30:00",
        )
        await asyncio.sleep(0)

        class FakeMatcher:
            async def send(self, message):
                return message

            async def finish(self, message=None):
                return message

        await stop_words_flow.handle_add_group_stop_words("12345", FakeMatcher(), "shieldA shieldB")
        await approval_store.write("12345", "ready")
        await approval_store.write("12345", "go")
        await approval_store.g_admin_add("12345", 20001)
        await approval_blacklist_store.add_blacklist_term("12345", "adword")

        ai_config = await ai_verify_store.load_config()
        ai_config["12345"] = {"enabled": True, "prompt": "Reject obvious ad accounts."}
        await ai_verify_store.save_config(ai_config)

        await broadcast_store.add_excluded_groups(
            "10000",
            ["12345", "23456"],
            valid_group_ids=["12345", "23456"],
            superusers=["10000"],
        )
        await config_orm_store.orm_replace_content_guard_rules(
            [
                ["广告", "$撤回$禁言"],
                ["测试", "$撤回$仅限12345"],
                ["刷屏", "$禁言$排除23456"],
            ]
        )

        path_module.limit_word_path.parent.mkdir(parents=True, exist_ok=True)
        path_module.limit_word_path.write_text(
            "广告\t$撤回$禁言\n"
            "测试\t$撤回$仅限12345\n"
            "刷屏\t$禁言$排除23456\n",
            encoding="utf-8",
        )

        path_module.error_path.mkdir(parents=True, exist_ok=True)
        (path_module.error_path / "dashboard.json").write_text(
            json.dumps(
                {
                    "12345": {
                        "2026-04-19 15:23:00": ["dashboard", "sample plugin error"],
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        switcher_state = path_module.build_default_switchers()
        switcher_state.update(
            {
                "auto_ban": True,
                "img_check": True,
                "particular_e_notice": True,
                "group_recall": True,
            }
        )
        await config_orm_store.orm_save_switcher_group("12345", switcher_state)

        await config_orm_store.orm_save_user_violation("12345", "20001", 2)
        await config_orm_store.orm_add_violation_record("12345", "20001", "2026-04-18T09:00:00", "违禁词", "bad message")
        await config_orm_store.orm_add_violation_record("12345", "20001", "2026-04-18T09:05:00", "刷屏", "spam burst")
        await config_orm_store.orm_save_user_violation("34567", "30001", 1)
        await config_orm_store.orm_add_violation_record("34567", "30001", "2026-04-18T08:00:00", "违禁词", "offline-only violation")

        path_module.kick_lock_path.mkdir(parents=True, exist_ok=True)
        (path_module.kick_lock_path / "12345.lock").write_text("locked", encoding="utf-8")

        async def fake_render_wordcloud_image(*args, **kwargs):
            return True, b"fake-wordcloud"

        dashboard_api.render_wordcloud_image = fake_render_wordcloud_image

        client = TestClient(package.driver.server_app)
        headers = {"X-Admin-Token": "smoke-token"}

        index_response = client.get("/ops")
        assert index_response.status_code == 200

        if (ADMIN_WEB_DIST_DIR / "index.html").exists():
            assert '<div id="app"></div>' in index_response.text
            assert "Ops Console" in index_response.text
            assert "window.ADMIN_DASHBOARD_BOOTSTRAP" in index_response.text
            assert "/ops/api" in index_response.text

            login_page_response = client.get("/ops/login")
            assert login_page_response.status_code == 200
            assert '<div id="app"></div>' in login_page_response.text
            assert "Ops Console" in login_page_response.text
            assert "/ops/api" in login_page_response.text

            favicon_response = client.get("/ops/favicon.svg")
            assert favicon_response.status_code == 200
        else:
            assert "Ops Console" in index_response.text

            static_js_response = client.get("/ops/static/dashboard.js")
            assert static_js_response.status_code == 200
            assert "ADMIN_DASHBOARD_BOOTSTRAP" in static_js_response.text

        meta_response = client.get("/ops/api/meta")
        assert meta_response.status_code == 200
        meta_payload = meta_response.json()
        assert meta_payload["auth_required"] is True
        assert meta_payload["mode"] == "integrated_web"
        assert meta_payload["frontend_enabled"] is True
        assert meta_payload["frontend_path"] == "/ops"
        assert "statistics" in meta_payload["overview_keys"]
        assert "messages" in meta_payload["group_section_keys"]
        assert "members" in meta_payload["group_section_keys"]
        assert "feature_switches" in meta_payload["group_section_keys"]

        catalog_response = client.get("/ops/api/catalog")
        assert catalog_response.status_code == 200
        catalog_payload = catalog_response.json()
        assert catalog_payload["mode"] == "integrated_web"
        assert catalog_payload["frontend_enabled"] is True
        assert catalog_payload["frontend_path"] == "/ops"
        assert any(item["key"] == "home" for item in catalog_payload["frontend_routes"])
        assert any(item["key"] == "messages" for item in catalog_payload["group_routes"])
        assert any(item["key"] == "members" for item in catalog_payload["group_routes"])
        assert any(item["key"] == "runtime" for item in catalog_payload["overview_routes"])
        assert any(item["key"] == "approval" for item in catalog_payload["group_routes"])

        session_response = client.get("/ops/api/auth/session", headers=headers)
        assert session_response.status_code == 200
        session_payload = session_response.json()
        assert session_payload["title"] == "Ops Console"
        assert session_payload["bot_count"] >= 1

        overview_unauthorized = client.get("/ops/api/overview")
        assert overview_unauthorized.status_code == 401

        overview_response = client.get("/ops/api/overview", headers=headers)
        assert overview_response.status_code == 200
        overview_payload = overview_response.json()
        assert overview_payload["group_count"] >= 2
        assert overview_payload["history_message_count"] >= 3
        assert overview_payload["violation_event_count"] >= 2
        assert overview_payload["cleanup_lock_count"] >= 1
        assert overview_payload["basic_admin_enabled_groups"] >= 1
        assert overview_payload["event_notice_enabled_groups"] >= 1

        operations_overview_response = client.get("/ops/api/operations/overview", headers=headers)
        assert operations_overview_response.status_code == 200
        operations_overview_payload = operations_overview_response.json()
        assert operations_overview_payload["group_count"] >= 2
        assert operations_overview_payload["manageable_group_count"] >= 1
        assert operations_overview_payload["broadcast_target_count"] >= 2
        assert len(operations_overview_payload["top_groups"]) >= 1

        logs_overview_response = client.get("/ops/api/logs/overview", headers=headers)
        assert logs_overview_response.status_code == 200
        logs_overview_payload = logs_overview_response.json()
        assert logs_overview_payload["runtime_log_enabled"] is True
        assert logs_overview_payload["runtime_log_total"] >= 3
        assert logs_overview_payload["plugin_error_total"] >= 1
        assert logs_overview_payload["level_totals"]["ERROR"] >= 1

        logs_response = client.get("/ops/api/logs?page=1&page_size=5&source=runtime_log", headers=headers)
        assert logs_response.status_code == 200
        logs_payload = logs_response.json()
        assert logs_payload["pagination"]["page"] == 1
        assert logs_payload["pagination"]["page_size"] == 5
        assert logs_payload["filters"]["source"] == "runtime_log"
        assert len(logs_payload["items"]) >= 1

        oplog_response = client.get("/ops/api/logs?page=1&page_size=20&source=dashboard_oplog&keyword=baidu.com", headers=headers)
        assert oplog_response.status_code == 200
        oplog_payload = oplog_response.json()
        assert any("https://www.baidu.com" in item["detail"] for item in oplog_payload["items"])

        statistics_overview_response = client.get("/ops/api/statistics/overview", headers=headers)
        assert statistics_overview_response.status_code == 200
        statistics_overview_payload = statistics_overview_response.json()
        assert statistics_overview_payload["group_count"] >= 3
        assert statistics_overview_payload["record_enabled_groups"] >= 1
        assert statistics_overview_payload["wordcloud_available_groups"] >= 1
        assert len(statistics_overview_payload["top_history_groups"]) >= 1

        approval_overview_response = client.get("/ops/api/approval/overview", headers=headers)
        assert approval_overview_response.status_code == 200
        approval_overview_payload = approval_overview_response.json()
        assert approval_overview_payload["group_terms_configured"] >= 1
        assert approval_overview_payload["ai_verify_enabled_groups"] >= 1

        broadcast_overview_response = client.get("/ops/api/broadcast/overview", headers=headers)
        assert broadcast_overview_response.status_code == 200
        broadcast_overview_payload = broadcast_overview_response.json()
        assert broadcast_overview_payload["configured_users"] >= 1
        assert broadcast_overview_payload["excluded_groups"] >= 2

        basic_admin_overview_response = client.get("/ops/api/basic-group-admin/overview", headers=headers)
        assert basic_admin_overview_response.status_code == 200
        basic_admin_overview_payload = basic_admin_overview_response.json()
        assert basic_admin_overview_payload["enabled_groups"] >= 1
        assert basic_admin_overview_payload["deputy_admin_groups"] >= 1
        assert basic_admin_overview_payload["deputy_admin_count"] >= 1
        assert basic_admin_overview_payload["high_risk_command_count"] >= 5

        content_guard_overview_response = client.get("/ops/api/content-guard/overview", headers=headers)
        assert content_guard_overview_response.status_code == 200
        content_guard_overview_payload = content_guard_overview_response.json()
        assert content_guard_overview_payload["rule_count"] >= 3
        assert content_guard_overview_payload["delete_rule_count"] >= 2
        assert content_guard_overview_payload["ban_rule_count"] >= 2
        assert content_guard_overview_payload["violation_group_count"] >= 1
        assert content_guard_overview_payload["text_guard_enabled_groups"] >= 1
        assert content_guard_overview_payload["image_guard_switch_enabled_groups"] >= 1
        assert content_guard_overview_payload["image_guard"]["runtime_status"] == "suspended"
        assert content_guard_overview_payload["image_guard"]["runtime_label"] == "已挂起"
        assert content_guard_overview_payload["image_guard"]["provider"] == "腾讯图片审核（预留）"
        assert len(content_guard_overview_payload["recent_violations"]) >= 2

        member_cleanup_overview_response = client.get("/ops/api/member-cleanup/overview", headers=headers)
        assert member_cleanup_overview_response.status_code == 200
        member_cleanup_overview_payload = member_cleanup_overview_response.json()
        assert member_cleanup_overview_payload["active_lock_count"] >= 1
        assert member_cleanup_overview_payload["active_groups"][0]["group_id"] == "12345"

        event_notice_overview_response = client.get("/ops/api/event-notice/overview", headers=headers)
        assert event_notice_overview_response.status_code == 200
        event_notice_overview_payload = event_notice_overview_response.json()
        assert event_notice_overview_payload["particular_notice_enabled_groups"] >= 1
        assert event_notice_overview_payload["anti_recall_enabled_groups"] >= 1
        assert event_notice_overview_payload["active_notice_types"] >= 4
        assert event_notice_overview_payload["listener_only_types"] >= 3

        switcher_overview_response = client.get("/ops/api/switcher/overview", headers=headers)
        assert switcher_overview_response.status_code == 200
        switcher_overview_payload = switcher_overview_response.json()
        assert switcher_overview_payload["group_count"] >= 2
        assert switcher_overview_payload["feature_count"] >= 5
        admin_feature = next(item for item in switcher_overview_payload["features"] if item["key"] == "admin")
        assert admin_feature["default_enabled"] is True

        runtime_overview_response = client.get("/ops/api/runtime/overview", headers=headers)
        assert runtime_overview_response.status_code == 200
        runtime_overview_payload = runtime_overview_response.json()
        assert runtime_overview_payload["mode"] == "integrated_web"
        assert runtime_overview_payload["dashboard_enabled"] is True
        assert runtime_overview_payload["dashboard_frontend_enabled"] is True
        assert runtime_overview_payload["dashboard_log_file_path"] == str(runtime_log_path)
        assert runtime_overview_payload["statistics_orm_bootstrap"]["enabled"] is True
        assert runtime_overview_payload["statistics_orm_bootstrap"]["ready"] is True
        assert "statistics_orm_enabled=true" in runtime_overview_payload["statistics_orm_bootstrap"]["env_hints"]
        assert any(item["key"] == "jieba" for item in runtime_overview_payload["optional_dependencies"])

        groups_response = client.get("/ops/api/groups", headers=headers)
        assert groups_response.status_code == 200
        groups_payload = groups_response.json()["items"]
        assert any(item["group_id"] == "12345" and item["group_name"] == "Smoke Group" for item in groups_payload)
        assert any(item["group_id"] == "23456" for item in groups_payload)
        assert any(item["group_id"] == "34567" for item in groups_payload)
        assert any(item["group_id"] == "12345" and item["cleanup_lock_active"] for item in groups_payload)
        assert any(item["group_id"] == "12345" and item["event_notice_enabled"] for item in groups_payload)
        assert any(item["group_id"] == "12345" and item["anti_recall_enabled"] for item in groups_payload)
        assert any(item["group_id"] == "12345" and item["basic_admin_enabled"] for item in groups_payload)
        assert any(item["group_id"] == "12345" and item["deputy_admin_count"] >= 1 for item in groups_payload)

        detail_response = client.get("/ops/api/groups/12345", headers=headers)
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()
        assert detail_payload["summary"]["history_message_count"] >= 3
        assert detail_payload["summary"]["violation_event_count"] >= 2
        assert detail_payload["summary"]["cleanup_lock_active"] is True
        assert len(detail_payload["wordcloud_keywords"]) >= 1
        assert len(detail_payload["recent_messages"]) >= 2
        assert detail_payload["approval"]["ai_verify_enabled"] is True
        assert len(detail_payload["approval"]["terms"]) == 2
        assert len(detail_payload["approval"]["group_admins"]) == 1
        assert detail_payload["broadcast"]["excluded_by"][0]["user_id"] == "10000"
        assert detail_payload["basic_group_admin"]["feature_enabled"] is True
        assert detail_payload["basic_group_admin"]["command_count"] >= 10
        assert detail_payload["basic_group_admin"]["high_risk_command_count"] >= 5
        assert len(detail_payload["basic_group_admin"]["deputy_admins"]) == 1
        assert detail_payload["basic_group_admin"]["deputy_admins"][0]["display_name"] == "Alice"
        assert detail_payload["content_guard"]["rule_count"] >= 2
        assert detail_payload["content_guard"]["delete_rule_count"] >= 1
        assert detail_payload["content_guard"]["ban_rule_count"] >= 1
        assert detail_payload["content_guard"]["text_guard_enabled"] is True
        assert detail_payload["content_guard"]["image_guard_enabled"] is False
        assert detail_payload["content_guard"]["image_guard_switch_enabled"] is True
        assert detail_payload["content_guard"]["image_guard"]["runtime_status"] == "suspended"
        assert detail_payload["content_guard"]["image_guard"]["runtime_label"] == "已挂起"
        assert len(detail_payload["content_guard"]["recent_violations"]) >= 2
        assert detail_payload["member_cleanup"]["lock_active"] is True
        assert len(detail_payload["member_cleanup"]["supported_modes"]) == 2
        assert detail_payload["event_notice"]["particular_notice_enabled"] is True
        assert detail_payload["event_notice"]["anti_recall_enabled"] is True
        assert detail_payload["event_notice"]["active_notice_types"] >= 4
        assert len(detail_payload["event_notice"]["event_types"]) >= 7
        assert detail_payload["statistics"]["history_message_count"] >= 3
        assert detail_payload["feature_switches_summary"]["enabled_count"] >= 1

        statistics_group_response = client.get("/ops/api/groups/12345/statistics", headers=headers)
        assert statistics_group_response.status_code == 200
        statistics_group_payload = statistics_group_response.json()
        assert statistics_group_payload["history_message_count"] >= 3
        assert statistics_group_payload["wordcloud_available"] is True

        message_group_response = client.get("/ops/api/groups/12345/messages?limit=2", headers=headers)
        assert message_group_response.status_code == 200
        message_group_payload = message_group_response.json()
        assert message_group_payload["mode"] in {"orm", "text_fallback"}
        assert len(message_group_payload["items"]) >= 2
        assert message_group_payload["pagination"]["latest_id"] is not None

        member_group_response = client.get("/ops/api/groups/12345/members?page=1&page_size=2", headers=headers)
        assert member_group_response.status_code == 200
        member_group_payload = member_group_response.json()
        assert len(member_group_payload["items"]) == 2
        assert member_group_payload["pagination"]["total"] >= 3
        assert member_group_payload["bot_profile"]["role"] == "owner"
        assert member_group_payload["bot_profile"]["capabilities"]["can_set_special_title"] is True

        feature_switch_group_response = client.get("/ops/api/groups/12345/feature-switches", headers=headers)
        assert feature_switch_group_response.status_code == 200
        feature_switch_group_payload = feature_switch_group_response.json()
        assert feature_switch_group_payload["enabled_count"] >= 1
        assert any(item["key"] == "admin" for item in feature_switch_group_payload["switches"])

        toggle_feature_response = client.post(
            "/ops/api/groups/12345/feature-switches/admin",
            headers=headers,
            json={"enabled": False},
        )
        assert toggle_feature_response.status_code == 200
        assert toggle_feature_response.json()["enabled"] is False

        bot_profile_response = client.get("/ops/api/groups/12345/bot-profile", headers=headers)
        assert bot_profile_response.status_code == 200
        assert bot_profile_response.json()["role"] == "owner"

        approval_group_response = client.get("/ops/api/groups/12345/approval", headers=headers)
        assert approval_group_response.status_code == 200
        assert len(approval_group_response.json()["terms"]) == 2

        broadcast_group_response = client.get("/ops/api/groups/12345/broadcast", headers=headers)
        assert broadcast_group_response.status_code == 200
        assert broadcast_group_response.json()["excluded_by"][0]["user_id"] == "10000"

        basic_admin_group_response = client.get("/ops/api/groups/12345/basic-group-admin", headers=headers)
        assert basic_admin_group_response.status_code == 200
        assert basic_admin_group_response.json()["high_risk_command_count"] >= 5

        content_guard_group_response = client.get("/ops/api/groups/12345/content-guard", headers=headers)
        assert content_guard_group_response.status_code == 200
        assert content_guard_group_response.json()["image_guard"]["runtime_status"] == "suspended"

        member_cleanup_group_response = client.get("/ops/api/groups/12345/member-cleanup", headers=headers)
        assert member_cleanup_group_response.status_code == 200
        assert member_cleanup_group_response.json()["lock_active"] is True

        event_notice_group_response = client.get("/ops/api/groups/12345/event-notice", headers=headers)
        assert event_notice_group_response.status_code == 200
        assert event_notice_group_response.json()["anti_recall_enabled"] is True

        image_response = client.get("/ops/api/groups/12345/wordcloud-card", headers=headers)
        assert image_response.status_code == 200
        assert image_response.content == b"fake-wordcloud"

        send_message_response = client.post(
            "/ops/api/groups/12345/messages",
            headers=headers,
            json={"message": "hello dashboard"},
        )
        assert send_message_response.status_code == 200
        assert fake_bot.sent_group_messages[-1]["message"] == "hello dashboard"

        broadcast_response = client.post(
            "/ops/api/broadcast/send",
            headers=headers,
            json={"message": "broadcast test", "include_group_ids": ["12345"]},
        )
        assert broadcast_response.status_code == 200
        broadcast_payload = broadcast_response.json()
        assert broadcast_payload["success_count"] >= 1
        assert "12345" in broadcast_payload["success_group_ids"]
        assert fake_bot.sent_group_messages[-1]["message"] == "broadcast test"

        mute_response = client.post(
            "/ops/api/groups/12345/actions/mute",
            headers=headers,
            json={"user_id": "20002", "duration": 120},
        )
        assert mute_response.status_code == 200
        assert fake_bot.muted_members[-1]["user_id"] == 20002

        kick_response = client.post(
            "/ops/api/groups/12345/actions/kick",
            headers=headers,
            json={"user_id": "20002", "reject_add_request": True},
        )
        assert kick_response.status_code == 200
        assert fake_bot.kicked_members[-1]["reject_add_request"] is True

        special_title_response = client.post(
            "/ops/api/groups/12345/actions/special-title",
            headers=headers,
            json={"user_id": "20002", "special_title": "老兵"},
        )
        assert special_title_response.status_code == 200
        assert fake_bot.special_titles[-1]["special_title"] == "老兵"

    print("dashboard smoke check passed")


if __name__ == "__main__":
    asyncio.run(run_checks())
