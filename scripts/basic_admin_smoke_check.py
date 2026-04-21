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


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "nonebot_plugin_admin"
PKG_NAME = "_basic_admin_smoke_pkg"

warnings.filterwarnings(
    "ignore",
    message="You seem to already have a custom sys.excepthook handler installed.*",
    category=RuntimeWarning,
)



def bootstrap_package():
    nonebot.init(superusers={"10000"}, host="127.0.0.1", port=8080)
    if not hasattr(nonebot, "get_plugin_config"):
        def _compat_get_plugin_config(config_cls):
            return config_cls()

        nonebot.get_plugin_config = _compat_get_plugin_config

    package = types.ModuleType(PKG_NAME)
    package.__path__ = [str(PACKAGE_DIR)]
    sys.modules[PKG_NAME] = package

    util_package = types.ModuleType(f"{PKG_NAME}.util")
    util_package.__path__ = [str(PACKAGE_DIR / "util")]
    sys.modules[f"{PKG_NAME}.util"] = util_package

    core_package = types.ModuleType(f"{PKG_NAME}.core")
    core_package.__path__ = [str(PACKAGE_DIR / "core")]
    sys.modules[f"{PKG_NAME}.core"] = core_package

    approval_package = types.ModuleType(f"{PKG_NAME}.approval")
    approval_package.__path__ = [str(PACKAGE_DIR / "approval")]
    sys.modules[f"{PKG_NAME}.approval"] = approval_package

    basic_admin_package = types.ModuleType(f"{PKG_NAME}.basic_group_admin")
    basic_admin_package.__path__ = [str(PACKAGE_DIR / "basic_group_admin")]
    sys.modules[f"{PKG_NAME}.basic_group_admin"] = basic_admin_package



def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module



def load_basic_admin_modules():
    bootstrap_package()
    modules = {}
    modules["util.time_util"] = load_module(f"{PKG_NAME}.util.time_util", PACKAGE_DIR / "util" / "time_util.py")
    modules["util.file_util"] = load_module(f"{PKG_NAME}.util.file_util", PACKAGE_DIR / "util" / "file_util.py")
    modules["config"] = load_module(f"{PKG_NAME}.core.config", PACKAGE_DIR / "core" / "config.py")
    modules["path"] = load_module(f"{PKG_NAME}.core.path", PACKAGE_DIR / "core" / "path.py")
    modules["utils"] = load_module(f"{PKG_NAME}.core.utils", PACKAGE_DIR / "core" / "utils.py")
    modules["approval_store"] = load_module(f"{PKG_NAME}.approval.approval_store", PACKAGE_DIR / "approval" / "approval_store.py")
    modules["admin_role"] = load_module(f"{PKG_NAME}.basic_group_admin.admin_role", PACKAGE_DIR / "basic_group_admin" / "admin_role.py")
    modules["message"] = load_module(f"{PKG_NAME}.core.message", PACKAGE_DIR / "core" / "message.py")
    modules["group_admin_flow"] = load_module(f"{PKG_NAME}.basic_group_admin.group_admin_flow", PACKAGE_DIR / "basic_group_admin" / "group_admin_flow.py")
    modules["group_admin_text"] = load_module(f"{PKG_NAME}.basic_group_admin.group_admin_text", PACKAGE_DIR / "basic_group_admin" / "group_admin_text.py")
    modules["group_recall_flow"] = load_module(f"{PKG_NAME}.basic_group_admin.group_recall_flow", PACKAGE_DIR / "basic_group_admin" / "group_recall_flow.py")
    modules["admin"] = load_module(f"{PKG_NAME}.basic_group_admin.admin", PACKAGE_DIR / "basic_group_admin" / "admin.py")
    return modules



def patch_paths(modules: dict, temp_root: Path):
    config_dir = temp_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    group_admin_path = config_dir / "group_admin.json"
    group_admin_path.write_text('{"su": "True"}', encoding="utf-8")
    modules["path"].config_path = config_dir
    modules["path"].config_group_admin = group_admin_path
    modules["approval_store"].config_group_admin = group_admin_path


class FakeGroupBot:
    def __init__(self):
        self.kicks = []
        self.group_admin_ops = []
        self.deleted_messages = []
        self.history_calls = []
        self.api_calls = []

    async def set_group_kick(self, group_id: int, user_id: int, reject_add_request: bool = False):
        self.kicks.append((group_id, user_id, reject_add_request))

    async def set_group_admin(self, group_id: int, user_id: int, enable: bool):
        self.group_admin_ops.append((group_id, user_id, enable))

    async def delete_msg(self, message_id: int):
        self.deleted_messages.append(message_id)

    async def call_api(self, api: str, **kwargs):
        self.api_calls.append((api, kwargs))
        if api == "get_group_msg_history":
            self.history_calls.append(kwargs.get("message_seq"))
            if kwargs.get("message_seq") is None:
                return {
                    "messages": [
                        {"message_seq": 9, "user_id": 20001, "message_id": 9001},
                        {"message_seq": 8, "user_id": 20002, "message_id": 9002},
                    ]
                }
            return {
                "messages": [
                    {"message_seq": 7, "user_id": 20001, "message_id": 9003},
                    {"message_seq": 6, "user_id": 20003, "message_id": 9004},
                ]
            }



def assert_matcher_registered(matcher, *, matcher_type: str, priority: int, block: bool, module_suffix: str):
    assert matcher.type == matcher_type
    assert matcher.priority == priority
    assert matcher.block is block
    assert len(matcher.handlers) >= 1
    assert matcher.module_name.endswith(module_suffix)


async def immediate_sleep(_: float):
    return None



def fixed_randint(_: int, __: int) -> int:
    return 0


async def run_checks():
    modules = load_basic_admin_modules()
    with tempfile.TemporaryDirectory() as temp_dir:
        patch_paths(modules, Path(temp_dir))

        group_admin_flow = modules["group_admin_flow"]
        group_recall_flow = modules["group_recall_flow"]
        admin = modules["admin"]

        assert group_admin_flow.parse_mute_duration("禁60") == 60
        assert group_admin_flow.parse_mute_duration("禁") is None
        assert group_admin_flow.contains_all_target(["all"]) is True
        assert group_admin_flow.contains_all_target(["10001"]) is False
        assert group_admin_flow.is_superuser("10000", {"10000"}) is True

        targets, error = group_admin_flow.resolve_special_title_targets(10000, None, {"10000"})
        assert targets == [10000] and error is None
        targets, error = group_admin_flow.resolve_special_title_targets(20000, ["all"], {"10000"})
        assert targets == [] and error == "all"
        targets, error = group_admin_flow.resolve_special_title_targets(20000, ["20001"], {"10000"})
        assert targets == [] and error == "permission"
        targets, error = group_admin_flow.resolve_special_title_targets(10000, ["20001", "20002"], {"10000"})
        assert targets == [20001, 20002] and error is None

        fake_mute_calls = []

        async def fake_mute_sb(bot, gid, lst, time=None, scope=None):
            fake_mute_calls.append((gid, lst, time, scope))
            yield None
            yield immediate_sleep(0)

        original_mute_sb = group_admin_flow.mute_sb
        group_admin_flow.mute_sb = fake_mute_sb
        try:
            await group_admin_flow.execute_mute(FakeGroupBot(), 12345, ["20001"], 60)
        finally:
            group_admin_flow.mute_sb = original_mute_sb
        assert fake_mute_calls == [(12345, ["20001"], 60, None)]

        fake_bot = FakeGroupBot()
        skipped_self = []
        skipped_superuser = []

        async def on_skip_self(target: str):
            skipped_self.append(target)

        async def on_skip_superuser(target: str):
            skipped_superuser.append(target)

        kicked = await group_admin_flow.execute_group_kick(
            fake_bot,
            12345,
            10000,
            ["10000", "10001", "20001"],
            {"10001"},
            reject_add_request=True,
            on_skip_self=on_skip_self,
            on_skip_superuser=on_skip_superuser,
        )
        assert kicked == [20001]
        assert skipped_self == ["10000"]
        assert skipped_superuser == ["10001"]
        assert fake_bot.kicks == [(12345, 20001, True)]

        await group_admin_flow.toggle_group_admin(fake_bot, 12345, ["20001", "20002"], True)
        assert fake_bot.group_admin_ops == [(12345, 20001, True), (12345, 20002, True)]

        await group_admin_flow.toggle_essence(fake_bot, 7788, True)
        await group_admin_flow.toggle_essence(fake_bot, 8899, False)
        assert fake_bot.api_calls[-2:] == [
            ("set_essence_msg", {"message_id": 7788}),
            ("delete_essence_msg", {"message_id": 8899}),
        ]

        assert group_recall_flow.parse_recall_count("撤回 @user 2") == 2
        assert group_recall_flow.parse_recall_count("撤回 @user x") == 5
        assert group_recall_flow.parse_recall_count("撤回") == 5

        reply_ids, seq = await group_recall_flow.collect_recall_message_ids(
            fake_bot,
            12345,
            "撤回",
            None,
            5566,
            sleep_func=immediate_sleep,
            random_func=fixed_randint,
        )
        assert reply_ids == [5566] and seq is None

        history_ids, seq = await group_recall_flow.collect_recall_message_ids(
            fake_bot,
            12345,
            "撤回 @20001 2",
            ["20001"],
            None,
            sleep_func=immediate_sleep,
            random_func=fixed_randint,
        )
        assert history_ids == [9001, 9003]
        assert seq == 6

        await group_recall_flow.recall_messages(
            fake_bot,
            [9001, 9003],
            sleep_func=immediate_sleep,
            random_func=fixed_randint,
        )
        assert fake_bot.deleted_messages == [9001, 9003]

        assert_matcher_registered(admin.ban, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.unban, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.ban_all, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.change, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.title, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.title_, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.kick, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.kick_, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.set_g_admin, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.unset_g_admin, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.set_essence, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.del_essence, matcher_type="message", priority=2, block=True, module_suffix="admin")
        assert_matcher_registered(admin.msg_recall, matcher_type="message", priority=2, block=True, module_suffix="admin")


if __name__ == "__main__":
    asyncio.run(run_checks())
    print("basic admin smoke check passed")
