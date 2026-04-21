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
PKG_NAME = "_member_cleanup_smoke_pkg"

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

    member_cleanup_package = types.ModuleType(f"{PKG_NAME}.member_cleanup")
    member_cleanup_package.__path__ = [str(PACKAGE_DIR / "member_cleanup")]
    sys.modules[f"{PKG_NAME}.member_cleanup"] = member_cleanup_package


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_member_cleanup_modules():
    bootstrap_package()
    modules = {}
    modules["util.time_util"] = load_module(f"{PKG_NAME}.util.time_util", PACKAGE_DIR / "util" / "time_util.py")
    modules["config"] = load_module(f"{PKG_NAME}.core.config", PACKAGE_DIR / "core" / "config.py")
    modules["path"] = load_module(f"{PKG_NAME}.core.path", PACKAGE_DIR / "core" / "path.py")
    modules["member_cleanup_text"] = load_module(f"{PKG_NAME}.member_cleanup.member_cleanup_text", PACKAGE_DIR / "member_cleanup" / "member_cleanup_text.py")
    modules["member_cleanup_lock"] = load_module(f"{PKG_NAME}.member_cleanup.member_cleanup_lock", PACKAGE_DIR / "member_cleanup" / "member_cleanup_lock.py")
    modules["member_cleanup_flow"] = load_module(f"{PKG_NAME}.member_cleanup.member_cleanup_flow", PACKAGE_DIR / "member_cleanup" / "member_cleanup_flow.py")
    modules["kick_member_by_rule"] = load_module(f"{PKG_NAME}.member_cleanup.kick_member_by_rule", PACKAGE_DIR / "member_cleanup" / "kick_member_by_rule.py")
    return modules


def patch_paths(modules: dict, temp_root: Path):
    config_dir = temp_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    kick_lock_dir = config_dir / "kick_lock"
    kick_lock_dir.mkdir(parents=True, exist_ok=True)
    modules["path"].config_path = config_dir
    modules["path"].kick_lock_path = kick_lock_dir
    modules["kick_member_by_rule"].kick_lock_path = kick_lock_dir


class FakeCleanupBot:
    def __init__(self):
        self.kicks = []
        self.stranger_levels = {20001: 1, 20002: 0, 20003: 4}

    async def get_stranger_info(self, user_id: int, no_cache: bool = True):
        return {"level": self.stranger_levels[user_id]}

    async def set_group_kick(self, group_id: int, user_id: int):
        self.kicks.append((group_id, user_id))


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
    modules = load_member_cleanup_modules()
    with tempfile.TemporaryDirectory() as temp_dir:
        patch_paths(modules, Path(temp_dir))

        lock_module = modules["member_cleanup_lock"]
        flow = modules["member_cleanup_flow"]
        cleanup = modules["kick_member_by_rule"]

        lock_path = lock_module.get_cleanup_lock_path(modules["path"].kick_lock_path, 12345)
        assert lock_module.ensure_cleanup_lock(lock_path) is True
        assert lock_module.ensure_cleanup_lock(lock_path) is False
        lock_module.clear_cleanup_lock(lock_path)
        assert lock_path.exists() is False

        assert flow.should_cancel("取消") is True
        assert flow.should_cancel("继续") is False
        assert flow.build_category_prompt("1").startswith("等级")
        assert flow.build_category_prompt("2").startswith("最后发言时间")

        levels = {20001: 1, 20002: 0, 20003: 4}
        kick_list, zero_list = flow.filter_members_by_level(levels, 2)
        assert kick_list == [20001]
        assert zero_list == [20002]
        assert "20002" in flow.build_zero_level_notice(zero_list)

        last_sent_map = {20001: 0, 20002: 172800}
        parsed_date = flow.parse_cleanup_date("19700102")
        assert flow.filter_members_by_last_sent(last_sent_map, parsed_date) == [20001]
        assert flow.should_abort_for_remaining(5, 2) is True
        assert flow.should_abort_for_remaining(8, 2) is False

        fake_bot = FakeCleanupBot()
        levels = await flow.get_member_levels(fake_bot, [20001, 20002, 20003])
        assert levels == {20001: 1, 20002: 0, 20003: 4}

        success, fail = await flow.execute_member_cleanup(
            fake_bot,
            12345,
            10000,
            [20001, 20003],
            sleep_func=immediate_sleep,
            random_func=fixed_randint,
        )
        assert success == [20001, 20003]
        assert fail == []
        assert fake_bot.kicks == [(12345, 20001), (12345, 20003)]

        preview = flow.build_cleanup_preview([20001], "1", {20001: 1})
        assert "20001" in preview

        assert_matcher_registered(cleanup.kick_by_rule, matcher_type="message", priority=2, block=True, module_suffix="kick_member_by_rule")
        assert_matcher_registered(cleanup.delete_lock_manually, matcher_type="message", priority=2, block=True, module_suffix="kick_member_by_rule")


if __name__ == "__main__":
    asyncio.run(run_checks())
    print("member cleanup smoke check passed")
