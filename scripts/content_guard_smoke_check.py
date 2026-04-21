#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import importlib.util
import sys
import tempfile
import types
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import nonebot

from _fake_orm import install_fake_orm_modules


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "nonebot_plugin_admin"
PKG_NAME = "_content_guard_smoke_pkg"

warnings.filterwarnings(
    "ignore",
    message="You seem to already have a custom sys.excepthook handler installed.*",
    category=RuntimeWarning,
)



def bootstrap_package():
    nonebot.init(superusers={"10000"}, host="127.0.0.1", port=8080, statistics_orm_enabled=True)
    install_fake_orm_modules()
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

    content_guard_package = types.ModuleType(f"{PKG_NAME}.content_guard")
    content_guard_package.__path__ = [str(PACKAGE_DIR / "content_guard")]
    sys.modules[f"{PKG_NAME}.content_guard"] = content_guard_package

    statistics_package = types.ModuleType(f"{PKG_NAME}.statistics")
    statistics_package.__path__ = [str(PACKAGE_DIR / "statistics")]
    sys.modules[f"{PKG_NAME}.statistics"] = statistics_package



def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module



def load_content_guard_modules():
    bootstrap_package()
    modules = {}
    modules["util.time_util"] = load_module(f"{PKG_NAME}.util.time_util", PACKAGE_DIR / "util" / "time_util.py")
    modules["util.file_util"] = load_module(f"{PKG_NAME}.util.file_util", PACKAGE_DIR / "util" / "file_util.py")
    modules["config"] = load_module(f"{PKG_NAME}.core.config", PACKAGE_DIR / "core" / "config.py")
    modules["path"] = load_module(f"{PKG_NAME}.core.path", PACKAGE_DIR / "core" / "path.py")
    modules["message"] = load_module(f"{PKG_NAME}.core.message", PACKAGE_DIR / "core" / "message.py")
    modules["utils"] = load_module(f"{PKG_NAME}.core.utils", PACKAGE_DIR / "core" / "utils.py")
    modules["statistics.models"] = load_module(
        f"{PKG_NAME}.statistics.models",
        PACKAGE_DIR / "statistics" / "models.py",
    )
    modules["statistics.config_orm_store"] = load_module(
        f"{PKG_NAME}.statistics.config_orm_store",
        PACKAGE_DIR / "statistics" / "config_orm_store.py",
    )
    modules["text_guard_flow"] = load_module(
        f"{PKG_NAME}.content_guard.text_guard_flow",
        PACKAGE_DIR / "content_guard" / "text_guard_flow.py",
    )
    modules["image_guard_flow"] = load_module(
        f"{PKG_NAME}.content_guard.image_guard_flow",
        PACKAGE_DIR / "content_guard" / "image_guard_flow.py",
    )
    modules["auto_ban"] = load_module(
        f"{PKG_NAME}.content_guard.auto_ban",
        PACKAGE_DIR / "content_guard" / "auto_ban.py",
    )
    modules["img_check"] = load_module(
        f"{PKG_NAME}.content_guard.img_check",
        PACKAGE_DIR / "content_guard" / "img_check.py",
    )
    return modules



def patch_paths(modules: dict, temp_root: Path):
    config_dir = temp_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    limit_word_path = config_dir / "违禁词.txt"
    user_violation_info_path = config_dir / "user_violation"
    limit_word_path.write_text("", encoding="utf-8")
    modules["path"].config_path = config_dir
    modules["path"].limit_word_path = limit_word_path
    modules["path"].user_violation_info_path = user_violation_info_path
    modules["utils"].config_path = config_dir
    modules["utils"].limit_word_path = limit_word_path
    modules["utils"].user_violation_info_path = user_violation_info_path
    modules["auto_ban"].limit_word_path = limit_word_path



def assert_matcher_registered(matcher, *, matcher_type: str, priority: int, block: bool, module_suffix: str):
    assert matcher.type == matcher_type
    assert matcher.priority == priority
    assert matcher.block is block
    assert len(matcher.handlers) >= 1
    assert matcher.module_name.endswith(module_suffix)


@dataclass
class FakeMatcher:
    sent: list[tuple[str, str, bool]] = field(default_factory=list)
    finished: list[str] = field(default_factory=list)


@dataclass
class FakeImageEvent:
    group_id: int
    user_id: int
    message_id: int
    raw_message: str = "[image]"

    def get_user_id(self) -> str:
        return str(self.user_id)


class FakeImageBot:
    def __init__(self):
        self.deleted_messages = []
        self.sent_messages = []

    async def delete_msg(self, *, message_id: int):
        self.deleted_messages.append(message_id)

    async def send(self, **kwargs):
        self.sent_messages.append(kwargs)


async def fake_ban_coro():
    return None


async def fake_mute_sb(_bot, _gid, lst=None, time=None, scope=None):
    yield fake_ban_coro()


async def fake_sd(matcher: FakeMatcher, msg: str, at: bool = False):
    matcher.sent.append(("send", msg, at))


async def fake_fi(matcher: FakeMatcher, msg: str):
    matcher.finished.append(msg)


async def run_checks():
    modules = load_content_guard_modules()
    with tempfile.TemporaryDirectory(prefix="content-guard-smoke-") as temp_dir:
        temp_root = Path(temp_dir)
        patch_paths(modules, temp_root)

        text_flow = modules["text_guard_flow"]
        image_flow = modules["image_guard_flow"]
        auto_ban = modules["auto_ban"]
        img_check = modules["img_check"]
        limit_word_path = modules["path"].limit_word_path
        config_orm_store = modules["statistics.config_orm_store"]
        orm_models = modules["statistics.models"]
        utils = modules["utils"]

        limit_word_path.write_text(
            "广告\n"
            "仅撤回\t$撤回\n"
            "仅禁言\t$禁言\n"
            "仅限词\t$禁言$撤回$仅限123456,654321\n"
            "排除词\t$禁言$排除123456\n"
            "坏[正则\t$禁言\n",
            encoding="utf-8",
        )
        await config_orm_store.orm_replace_content_guard_rules(
            [
                ["广告"],
                ["仅撤回", "$撤回"],
                ["仅禁言", "$禁言"],
                ["仅限词", "$禁言$撤回$仅限123456,654321"],
                ["排除词", "$禁言$排除123456"],
                ["坏[正则", "$禁言"],
            ]
        )

        assert_matcher_registered(auto_ban.del_custom_limit_words, matcher_type="message", priority=2, block=True, module_suffix="auto_ban")
        assert_matcher_registered(auto_ban.add_custom_limit_words, matcher_type="message", priority=2, block=True, module_suffix="auto_ban")
        assert_matcher_registered(auto_ban.get_custom_limit_words, matcher_type="message", priority=2, block=True, module_suffix="auto_ban")
        assert_matcher_registered(auto_ban.f_word, matcher_type="message", priority=3, block=False, module_suffix="auto_ban")
        assert_matcher_registered(img_check.find_pic, matcher_type="message", priority=2, block=False, module_suffix="img_check")

        assert text_flow.check_text_message("这里有广告", 10001, limit_word_path) == (True, True, "广告")
        assert text_flow.check_text_message("仅撤回", 10001, limit_word_path) == (True, False, "仅撤回")
        assert text_flow.check_text_message("仅禁言", 10001, limit_word_path) == (False, True, "仅禁言")
        assert text_flow.check_text_message("仅限词", 123456, limit_word_path) == (True, True, "仅限词")
        assert text_flow.check_text_message("仅限词", 999999, limit_word_path) == (False, False, None)
        assert text_flow.check_text_message("排除词", 123456, limit_word_path) == (False, False, None)
        assert text_flow.check_text_message("排除词", 999999, limit_word_path) == (False, True, "排除词")
        assert text_flow.check_text_message("坏[正则", 10001, limit_word_path) == (False, True, "坏[正则")
        assert await text_flow.check_runtime_text_message("这里有广告", 10001) == (True, True, "广告")
        assert await auto_ban.check_msg("这里有广告", 10001) == (True, True, "广告")

        assert await utils.get_user_violation(12345, 20001, "Text", "bad message") == 0
        assert await utils.get_user_violation(12345, 20001, "Text", "spam burst") == 0
        assert {(record.group_id, record.user_id, record.level) for record in orm_models.UserViolation._records} == {
            ("12345", "20001", 1),
        }
        assert len(orm_models.ViolationRecord._records) == 2
        assert not modules["path"].user_violation_info_path.exists()

        pass_result = {"Suggestion": "Pass", "Score": 0, "Label": "Normal"}
        porn_warn = {"Suggestion": "Review", "Score": 89, "Label": "Porn"}
        porn_ban = {"Suggestion": "Block", "Score": 95, "Label": "Porn"}
        other_hit = {"Suggestion": "Block", "Score": 95, "Label": "Politics"}

        assert image_flow.should_process_result(pass_result) is False
        assert image_flow.should_warn_only_porn(porn_warn) is True
        assert image_flow.is_high_score_violation(porn_ban) is True
        assert image_flow.is_porn_violation(porn_ban) is True
        assert image_flow.is_porn_violation(other_hit) is False
        assert image_flow.is_image_guard_suspended() is True
        payload = image_flow.build_image_guard_status_payload(True)
        assert payload["switch_enabled"] is True
        assert payload["processing_enabled"] is False
        assert payload["runtime_status"] == "suspended"
        assert image_flow.build_porn_notice(2)
        assert image_flow.build_porn_notice()

        fake_event = FakeImageEvent(group_id=12345, user_id=20001, message_id=90001)
        await img_check.check_pic(fake_event, [])
        await img_check.check_pic(fake_event, ["img-a"])

    print("content guard smoke check passed")


if __name__ == "__main__":
    asyncio.run(run_checks())

