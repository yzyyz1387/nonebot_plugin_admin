#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import importlib.util
import sys
import tempfile
import types
import warnings
from pathlib import Path

import nonebot
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent
from nonebot.consts import CMD_ARG_KEY, CMD_KEY, PREFIX_KEY, RAW_CMD_KEY, SHELL_ARGS, SHELL_ARGV

from _fake_orm import install_fake_orm_modules


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "nonebot_plugin_admin"
PKG_NAME = "_integration_smoke_pkg"

warnings.filterwarnings(
    "ignore",
    message="You seem to already have a custom sys.excepthook handler installed.*",
    category=RuntimeWarning,
)


class FakeBot:
    def __init__(self):
        self.self_id = 10000
        self.sent_messages = []

    async def get_group_list(self):
        return [{"group_id": 12345}, {"group_id": 23456}]

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
        send_group_id="[""12345""]",
        send_switch_morning=False,
        send_switch_night=False,
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
            raise RuntimeError("pyppeteer is not available in integration smoke check")

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
    path_module.limit_word_path = config_path / "违禁词.txt"
    path_module.switcher_path = config_path / "开关.json"
    path_module.template_path = config_path / "template"
    path_module.stop_words_path = config_path / "stop_words"
    path_module.wordcloud_bg_path = config_path / "wordcloud_bg"
    path_module.user_violation_info_path = config_path / "群内用户违规信息"
    path_module.group_message_data_path = config_path / "群消息数据"
    path_module.error_path = config_path / "admin插件错误数据"
    path_module.broadcast_avoid_path = config_path / "广播排除群聊.json"
    path_module.ttf_path = res_path / "msyhblod.ttf"
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


def build_command_state(command: str, arg: str = "") -> dict:
    return {
        PREFIX_KEY: {
            CMD_KEY: (command,),
            RAW_CMD_KEY: command,
            CMD_ARG_KEY: arg,
            SHELL_ARGS: None,
            SHELL_ARGV: None,
        }
    }


def build_group_message_event(raw_message: str, user_id: int, role: str = "member", group_id: int = 12345):
    return OBGroupMessageEvent.parse_obj(
        {
            "time": 0,
            "self_id": 1,
            "post_type": "message",
            "sub_type": "normal",
            "user_id": user_id,
            "message_type": "group",
            "message_id": 1,
            "message": [{"type": "text", "data": {"text": raw_message}}],
            "original_message": [{"type": "text", "data": {"text": raw_message}}],
            "raw_message": raw_message,
            "font": 0,
            "sender": {"user_id": user_id, "nickname": "tester", "card": "", "role": role},
            "to_me": False,
            "group_id": group_id,
            "anonymous": None,
        }
    )


async def run_checks():
    bootstrap_package()
    path_module = load_module(f"{PKG_NAME}.core.path", PACKAGE_DIR / "core" / "path.py")

    with tempfile.TemporaryDirectory(prefix="integration-smoke-") as temp_dir:
        temp_root = Path(temp_dir)
        patch_paths(path_module, temp_root)

        package = load_package()
        fake_bot = FakeBot()

        nonebot.get_bots = lambda: {str(fake_bot.self_id): fake_bot}
        package.utils.nonebot.get_bots = nonebot.get_bots
        package.utils.mk = fake_mk

        package.utils.kick_lock_path.mkdir(parents=True, exist_ok=True)
        stale_lock = package.utils.kick_lock_path / "12345.lock"
        stale_lock.write_text("locked", encoding="utf-8")

        assert package.__plugin_meta__.name == "不简易群管"
        assert package.__help_plugin_name__ == "简易群管"
        assert "广播" in package.__usage__
        assert package.driver is nonebot.get_driver()
        assert not hasattr(package.driver.server_app.state, "admin_dashboard_registered_paths")

        expected_modules = [
            "approval.ai_group_verify",
            "approval.notice",
            "approval.request_manual",
            "approval.requests",
            "basic_group_admin.admin",
            "broadcasting.broadcast",
            "content_guard.auto_ban",
            "content_guard.img_check",
            "core.func_hook",
            "core.switcher",
            "dashboard.dashboard_web",
            "event_notice.group_recall",
            "event_notice.particular_e_notice",
            "member_cleanup.kick_member_by_rule",
            "statistics.group_msg",
            "statistics.word_analyze",
            "statistics.wordcloud",
        ]
        for suffix in expected_modules:
            assert f"{PKG_NAME}.{suffix}" in sys.modules, suffix

        await package.utils.init()
        await package.switcher.switcher_integrity_check(fake_bot)
        await package.run_migration_check()
        notified = await package.notify_legacy_text_upgrade(fake_bot)

        assert package.utils.ttf_name.exists()
        assert notified is False
        assert fake_bot.sent_messages == []
        assert not stale_lock.exists()
        assert not package.utils.config_admin.exists()
        assert not package.utils.config_group_admin.exists()
        assert not package.utils.appr_bk.exists()
        assert not package.utils.switcher_path.exists()
        assert not package.utils.word_path.exists()
        assert not package.utils.limit_word_path.exists()
        assert not package.utils.statistics_record_state_path.exists()
        assert not package.utils.words_contents_path.exists()
        assert not package.utils.stop_words_path.exists()
        assert not package.utils.group_message_data_path.exists()

        assert await sys.modules[f"{PKG_NAME}.dashboard.dashboard_command"].dashboard_url_cmd.check_rule(
            fake_bot,
            build_group_message_event("面板地址123", 10000),
            build_command_state("面板地址"),
        ) is False
        assert await sys.modules[f"{PKG_NAME}.core.db_command"].db_url_cmd.check_rule(
            fake_bot,
            build_group_message_event("数据库地址123", 10000),
            build_command_state("数据库地址"),
        ) is False
        assert await sys.modules[f"{PKG_NAME}.core.menu_command"].menu_cmd.check_rule(
            fake_bot,
            build_group_message_event("群管菜单123", 10000),
            build_command_state("群管菜单"),
        ) is False
        assert await sys.modules[f"{PKG_NAME}.broadcasting.broadcast"].avoided_group_list.check_rule(
            fake_bot,
            build_group_message_event("排除列表123", 10000),
            build_command_state("排除列表"),
        ) is False
        assert await sys.modules[f"{PKG_NAME}.member_cleanup.kick_member_by_rule"].kick_by_rule.check_rule(
            fake_bot,
            build_group_message_event("成员清理123", 10000, role="owner"),
            build_command_state("成员清理"),
        ) is False
        assert await sys.modules[f"{PKG_NAME}.content_guard.auto_ban"].get_custom_limit_words.check_rule(
            fake_bot,
            build_group_message_event("查看违禁词123", 10000, role="admin"),
            build_command_state("查看违禁词"),
        ) is False
        assert await sys.modules[f"{PKG_NAME}.core.switcher"].switcher_html.check_rule(
            fake_bot,
            build_group_message_event("开关状态123", 10000, role="admin"),
            build_command_state("开关状态"),
        ) is False

        switcher_data = await sys.modules[f"{PKG_NAME}.statistics.config_orm_store"].orm_load_switcher()
        for gid in ("12345", "23456"):
            assert gid in switcher_data
            for func_name in package.switcher.admin_funcs:
                assert func_name in switcher_data[gid]

        func_hook = sys.modules[f"{PKG_NAME}.core.func_hook"]
        assert await func_hook.check_func_status("admin", "12345") is True
        assert await func_hook.check_func_status("requests", "12345") is True
        assert await func_hook.check_func_status("img_check", "12345") is False
        assert await func_hook.check_func_status("group_recall", "12345") is False

        assert sys.modules[f"{PKG_NAME}.approval.requests"].group_req.module_name.endswith(".approval.requests")
        assert sys.modules[f"{PKG_NAME}.content_guard.auto_ban"].f_word.module_name.endswith(".content_guard.auto_ban")
        assert sys.modules[f"{PKG_NAME}.event_notice.group_recall"].group_recall.module_name.endswith(".event_notice.group_recall")

    print("integration smoke check passed")


if __name__ == "__main__":
    asyncio.run(run_checks())

