#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import importlib.util
import inspect
import sys
import tempfile
import types
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import nonebot
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent
from nonebot.adapters.onebot.v11 import GroupRequestEvent as OBGroupRequestEvent
from nonebot.consts import CMD_ARG_KEY, CMD_KEY, PREFIX_KEY, RAW_CMD_KEY, SHELL_ARGS, SHELL_ARGV

from _fake_orm import install_fake_orm_modules


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "nonebot_plugin_admin"
PKG_NAME = "_approval_smoke_pkg"

warnings.filterwarnings(
    "ignore",
    message="You seem to already have a custom sys.excepthook handler installed.*",
    category=RuntimeWarning,
)


def bootstrap_package():
    nonebot.init(superusers={"10000"}, host="127.0.0.1", port=8080, statistics_orm_enabled=True)
    nonebot.require = lambda name: None
    install_fake_orm_modules()
    if not hasattr(nonebot, "get_plugin_config"):
        def _compat_get_plugin_config(config_cls):
            return config_cls()

        nonebot.get_plugin_config = _compat_get_plugin_config

    if "pyppeteer" not in sys.modules:
        pyppeteer = types.ModuleType("pyppeteer")

        async def _fake_launch(*args, **kwargs):
            raise RuntimeError("pyppeteer is not available in approval smoke check")

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

    statistics_package = types.ModuleType(f"{PKG_NAME}.statistics")
    statistics_package.__path__ = [str(PACKAGE_DIR / "statistics")]
    sys.modules[f"{PKG_NAME}.statistics"] = statistics_package

    approval_package = types.ModuleType(f"{PKG_NAME}.approval")
    approval_package.__path__ = [str(PACKAGE_DIR / "approval")]
    sys.modules[f"{PKG_NAME}.approval"] = approval_package


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_approval_modules():
    bootstrap_package()
    modules = {}
    modules["util.time_util"] = load_module(
        f"{PKG_NAME}.util.time_util",
        PACKAGE_DIR / "util" / "time_util.py",
    )
    modules["util.file_util"] = load_module(
        f"{PKG_NAME}.util.file_util",
        PACKAGE_DIR / "util" / "file_util.py",
    )
    modules["config"] = load_module(f"{PKG_NAME}.core.config", PACKAGE_DIR / "core" / "config.py")
    modules["config"].plugin_config.statistics_orm_enabled = True
    modules["path"] = load_module(f"{PKG_NAME}.core.path", PACKAGE_DIR / "core" / "path.py")
    modules["utils"] = load_module(f"{PKG_NAME}.core.utils", PACKAGE_DIR / "core" / "utils.py")
    modules["message"] = load_module(f"{PKG_NAME}.core.message", PACKAGE_DIR / "core" / "message.py")
    modules["models"] = load_module(
        f"{PKG_NAME}.statistics.models",
        PACKAGE_DIR / "statistics" / "models.py",
    )
    modules["config_orm_store"] = load_module(
        f"{PKG_NAME}.statistics.config_orm_store",
        PACKAGE_DIR / "statistics" / "config_orm_store.py",
    )
    modules["switcher"] = load_module(f"{PKG_NAME}.core.switcher", PACKAGE_DIR / "core" / "switcher.py")
    modules["func_hook"] = load_module(f"{PKG_NAME}.core.func_hook", PACKAGE_DIR / "core" / "func_hook.py")
    modules["approval_text"] = load_module(
        f"{PKG_NAME}.approval.approval_text",
        PACKAGE_DIR / "approval" / "approval_text.py",
    )
    modules["approval_store"] = load_module(
        f"{PKG_NAME}.approval.approval_store",
        PACKAGE_DIR / "approval" / "approval_store.py",
    )
    modules["approval_blacklist_store"] = load_module(
        f"{PKG_NAME}.approval.approval_blacklist_store",
        PACKAGE_DIR / "approval" / "approval_blacklist_store.py",
    )
    modules["approval_verify"] = load_module(
        f"{PKG_NAME}.approval.approval_verify",
        PACKAGE_DIR / "approval" / "approval_verify.py",
    )
    modules["approval_command_flow"] = load_module(
        f"{PKG_NAME}.approval.approval_command_flow",
        PACKAGE_DIR / "approval" / "approval_command_flow.py",
    )
    modules["approval_request_flow"] = load_module(
        f"{PKG_NAME}.approval.approval_request_flow",
        PACKAGE_DIR / "approval" / "approval_request_flow.py",
    )
    modules["group_admin_command_flow"] = load_module(
        f"{PKG_NAME}.approval.group_admin_command_flow",
        PACKAGE_DIR / "approval" / "group_admin_command_flow.py",
    )
    modules["ai_verify_store"] = load_module(
        f"{PKG_NAME}.approval.ai_verify_store",
        PACKAGE_DIR / "approval" / "ai_verify_store.py",
    )
    modules["ai_verify_command_flow"] = load_module(
        f"{PKG_NAME}.approval.ai_verify_command_flow",
        PACKAGE_DIR / "approval" / "ai_verify_command_flow.py",
    )
    modules["ai_group_verify"] = load_module(
        f"{PKG_NAME}.approval.ai_group_verify",
        PACKAGE_DIR / "approval" / "ai_group_verify.py",
    )
    modules["notice"] = load_module(f"{PKG_NAME}.approval.notice", PACKAGE_DIR / "approval" / "notice.py")
    modules["requests"] = load_module(f"{PKG_NAME}.approval.requests", PACKAGE_DIR / "approval" / "requests.py")
    return modules


def patch_paths(modules: dict, temp_root: Path):
    config_dir = temp_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_admin = config_dir / "admin.json"
    config_group_admin = config_dir / "group_admin.json"
    approval_blacklist = config_dir / "approval_blacklist.json"
    ai_verify_config = config_dir / "ai_verify_config.json"

    modules["path"].config_path = config_dir
    modules["path"].config_admin = config_admin
    modules["path"].config_group_admin = config_group_admin
    modules["path"].appr_bk = approval_blacklist

    modules["approval_store"].config_admin = config_admin
    modules["approval_store"].config_group_admin = config_group_admin
    modules["approval_blacklist_store"].appr_bk = approval_blacklist
    modules["approval_verify"].config_admin = config_admin
    modules["approval_command_flow"].config_admin = config_admin
    modules["ai_verify_store"].CONFIG_FILE = ai_verify_config
    modules["utils"].config_admin = config_admin
    modules["utils"].config_group_admin = config_group_admin
    modules["utils"].appr_bk = approval_blacklist


class MatcherFinished(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(str(message))


class FakeMatcher:
    def __init__(self):
        self.sent = []

    async def send(self, message, **kwargs):
        self.sent.append(("send", message, kwargs))

    async def finish(self, message=None, **kwargs):
        self.sent.append(("finish", message, kwargs))
        raise MatcherFinished(message)


@dataclass
class FakeGroupEvent:
    group_id: int


class FakeMessageEvent:
    def __init__(self, message: str):
        self._message = message

    def get_message(self):
        return self._message


@dataclass
class FakeGroupRequestEvent:
    group_id: int
    flag: str
    user_id: int
    comment: str
    sub_type: str = "add"


class FakeBot:
    def __init__(self):
        self.requests = []
        self.private_messages = []

    async def set_group_add_request(self, **kwargs):
        self.requests.append(kwargs)

    async def send_msg(self, **kwargs):
        self.private_messages.append(kwargs)


class FakePermissionConfig:
    def __init__(self, superusers):
        self.superusers = {str(user_id) for user_id in superusers}


class FakePermissionAdapter:
    @staticmethod
    def get_name() -> str:
        return "OneBot V11"


class FakePermissionBot:
    def __init__(self, superusers):
        self.config = FakePermissionConfig(superusers)
        self.adapter = FakePermissionAdapter()


def assert_matcher_registered(
    matcher,
    *,
    matcher_type: str,
    priority: int,
    block: bool,
    module_suffix: str,
    rule_contains: Optional[List[str]] = None,
):
    assert matcher.type == matcher_type
    assert matcher.priority == priority
    assert matcher.block is block
    assert len(matcher.handlers) >= 1
    assert matcher.module_name.endswith(module_suffix)
    if rule_contains:
        rule_repr = repr(matcher.rule)
        for pattern in rule_contains:
            assert pattern in rule_repr, f"{pattern!r} not found in {rule_repr!r}"


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


def build_group_request_event(comment: str, user_id: int = 20000, group_id: int = 12345, sub_type: str = "add"):
    return OBGroupRequestEvent.parse_obj(
        {
            "time": 0,
            "self_id": 1,
            "post_type": "request",
            "request_type": "group",
            "sub_type": sub_type,
            "group_id": group_id,
            "user_id": user_id,
            "comment": comment,
            "flag": "request-flag",
        }
    )


async def assert_matcher_runtime(
    matcher,
    *,
    bot,
    event,
    state: Optional[dict] = None,
    rule_expected: bool = True,
    perm_expected: Optional[bool] = None,
):
    state = state or {}
    assert await matcher.check_rule(bot, event, state) is rule_expected
    if perm_expected is not None:
        assert await evaluate_permission(matcher.permission, bot, event) is perm_expected


async def evaluate_permission(permission, bot, event) -> bool:
    if not permission.checkers:
        return True

    for checker in permission.checkers:
        try:
            result = checker.call(bot, event)
        except TypeError:
            result = checker.call(event)
        if inspect.isawaitable(result):
            result = await result
        if result:
            return True
    return False


async def capture_finish(coro):
    try:
        await coro
    except MatcherFinished as finished:
        return finished.message
    raise AssertionError("matcher.finish 未被调用")


async def run_checks():
    modules = load_approval_modules()
    with tempfile.TemporaryDirectory(prefix="approval-smoke-") as temp_dir:
        temp_root = Path(temp_dir)
        patch_paths(modules, temp_root)

        approval_store = modules["approval_store"]
        approval_blacklist_store = modules["approval_blacklist_store"]
        approval_command_flow = modules["approval_command_flow"]
        approval_request_flow = modules["approval_request_flow"]
        group_admin_command_flow = modules["group_admin_command_flow"]
        ai_verify_store = modules["ai_verify_store"]
        ai_verify_command_flow = modules["ai_verify_command_flow"]
        ai_group_verify = modules["ai_group_verify"]
        notice = modules["notice"]
        requests = modules["requests"]

        gid = "10001"
        superusers = ["10000"]
        permission_bot = FakePermissionBot(superusers)

        assert_matcher_registered(
            notice.gad,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".notice",
            rule_contains=["分管", "/gad", "/分群管理"],
        )
        assert_matcher_registered(
            notice.su_g_admin,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".notice",
            rule_contains=["所有分管", "/sugad", "/su分群管理"],
        )
        assert_matcher_registered(
            notice.g_admin,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".notice",
            rule_contains=["分管+", "/gad+", "分群管理+", "分管加", "分群管理加"],
        )
        assert_matcher_registered(
            notice.su_gad,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".notice",
            rule_contains=["接收"],
        )
        assert_matcher_registered(
            notice.g_admin_,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".notice",
            rule_contains=["分管-", "/gad-", "分群管理-", "分管减", "分群管理减"],
        )

        assert_matcher_registered(
            ai_group_verify.ai_switch,
            matcher_type="message",
            priority=5,
            block=True,
            module_suffix=".ai_group_verify",
            rule_contains=["ai拒绝"],
        )
        assert_matcher_registered(
            ai_group_verify.ai_prompt_set,
            matcher_type="message",
            priority=5,
            block=True,
            module_suffix=".ai_group_verify",
            rule_contains=["ai拒绝prompt"],
        )
        assert_matcher_registered(
            ai_group_verify.ai_req_check,
            matcher_type="request",
            priority=1,
            block=False,
            module_suffix=".ai_group_verify",
        )

        assert_matcher_registered(
            requests.super_sp,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".requests",
            rule_contains=["所有词条", "/susp", "/su审批"],
        )
        assert_matcher_registered(
            requests.super_sp_add,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".requests",
            rule_contains=["指定词条+", "/susp+", "/su审批+", "指定词条加"],
        )
        assert_matcher_registered(
            requests.super_sp_de,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".requests",
            rule_contains=["指定词条-", "/susp-", "/su审批-", "指定词条减"],
        )
        assert_matcher_registered(
            requests.check,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".requests",
            rule_contains=["查看词条", "/sp", "/审批"],
        )
        assert_matcher_registered(
            requests.add_appr_term,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".requests",
            rule_contains=["词条+", "/sp+", "/审批+", "审批词条加", "词条加"],
        )
        assert_matcher_registered(
            requests.del_appr_term,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".requests",
            rule_contains=["词条-", "/sp-", "/审批-", "审批词条减", "词条减"],
        )
        assert_matcher_registered(
            requests.edit_appr_bk,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".requests",
            rule_contains=["词条拒绝", "/spx", "/审批拒绝", "拒绝词条"],
        )
        assert_matcher_registered(
            requests.group_req,
            matcher_type="request",
            priority=2,
            block=True,
            module_suffix=".requests",
        )

        await assert_matcher_runtime(
            notice.gad,
            bot=permission_bot,
            event=build_group_message_event("分管", 20001, role="admin"),
            state=build_command_state("分管"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            notice.gad,
            bot=permission_bot,
            event=build_group_message_event("分管123", 20001, role="admin"),
            state=build_command_state("分管"),
            rule_expected=False,
        )
        await assert_matcher_runtime(
            notice.gad,
            bot=permission_bot,
            event=build_group_message_event("/gad", 20002, role="member"),
            state=build_command_state("/gad"),
            perm_expected=False,
        )
        await assert_matcher_runtime(
            notice.su_g_admin,
            bot=permission_bot,
            event=build_group_message_event("所有分管", 10000),
            state=build_command_state("所有分管"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            notice.su_g_admin,
            bot=permission_bot,
            event=build_group_message_event("/su分群管理", 20003),
            state=build_command_state("/su分群管理"),
            perm_expected=False,
        )
        await assert_matcher_runtime(
            notice.g_admin,
            bot=permission_bot,
            event=build_group_message_event("分管+ 30002", 20004, role="admin"),
            state=build_command_state("分管+", "30002"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            notice.su_gad,
            bot=permission_bot,
            event=build_group_message_event("接收", 10000),
            state=build_command_state("接收"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            notice.su_gad,
            bot=permission_bot,
            event=build_group_message_event("接收123xx", 10000),
            state=build_command_state("接收"),
            rule_expected=False,
        )
        await assert_matcher_runtime(
            notice.su_gad,
            bot=permission_bot,
            event=build_group_message_event("接收", 20005),
            state=build_command_state("接收"),
            perm_expected=False,
        )
        await assert_matcher_runtime(
            notice.g_admin_,
            bot=permission_bot,
            event=build_group_message_event("分管- 30002", 20006, role="admin"),
            state=build_command_state("分管-", "30002"),
            perm_expected=True,
        )

        await assert_matcher_runtime(
            ai_group_verify.ai_switch,
            bot=permission_bot,
            event=build_group_message_event("ai拒绝开", 20007, role="admin"),
            state=build_command_state("ai拒绝", "开"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            ai_group_verify.ai_switch,
            bot=permission_bot,
            event=build_group_message_event("ai拒绝开", 20008),
            state=build_command_state("ai拒绝", "开"),
            perm_expected=False,
        )
        await assert_matcher_runtime(
            ai_group_verify.ai_prompt_set,
            bot=permission_bot,
            event=build_group_message_event("ai拒绝prompt 请填写来源", 20009, role="admin"),
            state=build_command_state("ai拒绝prompt", "请填写来源"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            ai_group_verify.ai_req_check,
            bot=permission_bot,
            event=build_group_request_event("答案：测试"),
        )

        await assert_matcher_runtime(
            requests.super_sp,
            bot=permission_bot,
            event=build_group_message_event("所有词条", 10000),
            state=build_command_state("所有词条"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            requests.super_sp,
            bot=permission_bot,
            event=build_group_message_event("所有词条123", 10000),
            state=build_command_state("所有词条"),
            rule_expected=False,
        )
        await assert_matcher_runtime(
            requests.super_sp,
            bot=permission_bot,
            event=build_group_message_event("/susp", 20010),
            state=build_command_state("/susp"),
            perm_expected=False,
        )
        await assert_matcher_runtime(
            requests.super_sp_add,
            bot=permission_bot,
            event=build_group_message_event("指定词条+ 10001 示例", 10000),
            state=build_command_state("指定词条+", "10001 示例"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            requests.super_sp_de,
            bot=permission_bot,
            event=build_group_message_event("指定词条- 10001 示例", 10000),
            state=build_command_state("指定词条-", "10001 示例"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            requests.check,
            bot=permission_bot,
            event=build_group_message_event("/审批", 20011, role="admin"),
            state=build_command_state("/审批"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            requests.check,
            bot=permission_bot,
            event=build_group_message_event("查看词条123", 20011, role="admin"),
            state=build_command_state("查看词条"),
            rule_expected=False,
        )
        await assert_matcher_runtime(
            requests.check,
            bot=permission_bot,
            event=build_group_message_event("查看词条", 20012),
            state=build_command_state("查看词条"),
            perm_expected=False,
        )
        await assert_matcher_runtime(
            requests.add_appr_term,
            bot=permission_bot,
            event=build_group_message_event("词条+ 示例", 20013, role="admin"),
            state=build_command_state("词条+", "示例"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            requests.del_appr_term,
            bot=permission_bot,
            event=build_group_message_event("词条- 示例", 20014, role="admin"),
            state=build_command_state("词条-", "示例"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            requests.edit_appr_bk,
            bot=permission_bot,
            event=build_group_message_event("词条拒绝 + 广告", 20015, role="admin"),
            state=build_command_state("词条拒绝", "+ 广告"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            requests.group_req,
            bot=permission_bot,
            event=build_group_request_event("答案：测试"),
        )

        assert await approval_store.g_admin_async() == {"su": "True"}
        assert await approval_store.g_admin_add(gid, 30001) is True
        assert await approval_store.g_admin_add(gid, 30001) is False
        assert (await approval_store.g_admin_async())[gid] == [30001]
        assert await approval_store.g_admin_del(gid, 30001) is True
        assert await approval_store.g_admin_del(gid, 30001) is None
        assert await approval_store.su_on_off() is False
        assert (await approval_store.g_admin_async())["su"] == "False"
        assert await approval_store.su_on_off() is True
        assert (await approval_store.g_admin_async())["su"] == "True"

        matcher = FakeMatcher()
        await group_admin_command_flow.handle_add_group_admins(
            matcher,
            gid,
            {"_prefix": {"command_arg": "30002"}},
            [],
        )
        assert matcher.sent[0][1] == "30002 已成为本群分群管理员：将接收加群处理结果，同时具有群管权限，但分管不能任命超管"

        matcher = FakeMatcher()
        message = await capture_finish(group_admin_command_flow.handle_list_group_admins(matcher, gid))
        assert "30002" in message

        matcher = FakeMatcher()
        message = await capture_finish(group_admin_command_flow.handle_list_all_group_admins(matcher))
        assert "'su': 'True'" in message

        matcher = FakeMatcher()
        message = await capture_finish(group_admin_command_flow.handle_toggle_superuser_receive(matcher))
        assert "审批消息接收当前状态为：已关闭" in message
        assert await approval_store.su_on_off() is True

        async def _status_true(_func_name: str, _gid: str) -> bool:
            return True

        matcher = FakeMatcher()
        await group_admin_command_flow.handle_remove_group_admins(
            matcher,
            gid,
            {"_prefix": {"command_arg": "30002"}},
            [],
            _status_true,
        )
        assert matcher.sent[0][1] == "30002 删除成功"

        assert await approval_store.write(gid, "正确答案") is True
        assert await approval_store.write(gid, "正确答案") is False
        assert await approval_store.delete(gid, "正确答案") is True
        assert await approval_store.delete(gid, "正确答案") is None

        matcher = FakeMatcher()
        message = await capture_finish(
            approval_command_flow.handle_add_term(
                matcher,
                FakeGroupEvent(group_id=int(gid)),
                {"_prefix": {"command_arg": "验证1"}},
            )
        )
        assert message == "群 10001 添加词条：验证1"

        matcher = FakeMatcher()
        message = await capture_finish(
            approval_command_flow.handle_check_terms(
                matcher,
                FakeGroupEvent(group_id=int(gid)),
            )
        )
        assert "验证1" in message

        matcher = FakeMatcher()
        message = await capture_finish(
            approval_command_flow.handle_edit_blacklist(
                matcher,
                FakeGroupEvent(group_id=int(gid)),
                {"_prefix": {"command_arg": "+ 广告"}},
            )
        )
        assert message == "群 10001 添加自动拒绝词条：广告"
        assert await approval_blacklist_store.get_group_blacklist(gid) == ["广告"]

        matcher = FakeMatcher()
        message = await capture_finish(
            approval_command_flow.handle_edit_blacklist(
                matcher,
                FakeGroupEvent(group_id=int(gid)),
                {"_prefix": {"command_arg": "- 广告"}},
            )
        )
        assert message == "群 10001 删除自动拒绝词条：广告"

        matcher = FakeMatcher()
        message = await capture_finish(
            approval_command_flow.handle_super_add_term(
                matcher,
                FakeMessageEvent("指定词条+ 10002 白名单"),
            )
        )
        assert message == "群 10002 添加入群审批词条：白名单"

        matcher = FakeMatcher()
        message = await capture_finish(approval_command_flow.handle_super_list_terms(matcher))
        assert "10002 : ['白名单']" in message

        matcher = FakeMatcher()
        message = await capture_finish(
            approval_command_flow.handle_super_delete_term(
                matcher,
                FakeMessageEvent("指定词条- 10002 白名单"),
            )
        )
        assert message == "群 10002 删除入群审批词条：白名单"

        assert await approval_store.g_admin_add(gid, 30003) is True

        bot = FakeBot()
        handled = await approval_request_flow.handle_group_request(
            bot,
            FakeGroupRequestEvent(
                group_id=10001,
                flag="flag-approve",
                user_id=20001,
                comment="答案：验证1",
            ),
            superusers,
        )
        assert handled is True
        assert bot.requests[-1]["approve"] is True
        assert len(bot.private_messages) >= 2

        await approval_blacklist_store.add_blacklist_term(gid, "广告")
        bot = FakeBot()
        handled = await approval_request_flow.handle_group_request(
            bot,
            FakeGroupRequestEvent(
                group_id=10001,
                flag="flag-reject",
                user_id=20002,
                comment="答案：广告",
            ),
            superusers,
        )
        assert handled is True
        assert bot.requests[-1]["approve"] is False
        assert bot.requests[-1]["reason"] == "答案未通过群管验证，可修改答案后再次申请"

        bot = FakeBot()
        handled = await approval_request_flow.handle_group_request(
            bot,
            FakeGroupRequestEvent(
                group_id=10003,
                flag="flag-skip",
                user_id=20003,
                comment="答案：没人配置",
            ),
            superusers,
        )
        assert handled is False
        assert not bot.requests

        await ai_verify_store.save_config({gid: {"enabled": True, "prompt": "请填写来源"}})
        ai_config = await ai_verify_store.load_config()
        assert ai_config[gid]["enabled"] is True
        assert ai_config[gid]["prompt"] == "请填写来源"

        matcher = FakeMatcher()
        message = await capture_finish(
            ai_verify_command_flow.handle_ai_switch_command(matcher, gid, "ai拒绝开")
        )
        assert message == "本群 AI 自动拒绝广告账号功能已【开启】。"
        assert (await ai_verify_store.load_config())[gid]["enabled"] is True

        matcher = FakeMatcher()
        message = await capture_finish(
            ai_verify_command_flow.handle_ai_prompt_command(matcher, gid, "请填写来源")
        )
        assert "请填写来源" in message
        assert (await ai_verify_store.load_config())[gid]["prompt"] == "请填写来源"

        matcher = FakeMatcher()
        message = await capture_finish(
            ai_verify_command_flow.handle_ai_prompt_command(matcher, gid, "")
        )
        assert message == "已清除自定义规则，仅拦截通用广告。"
        assert (await ai_verify_store.load_config())[gid]["prompt"] == ""

        ai_group_verify.plugin_config.ai_verify_proxy = "http://127.0.0.1:7890"
        ai_group_verify.plugin_config.ai_verify_use_proxy = True
        kwargs = ai_group_verify._build_ai_http_client_kwargs()
        assert kwargs["proxy"] == "http://127.0.0.1:7890"
        assert kwargs["trust_env"] is False

        ai_group_verify.plugin_config.ai_verify_use_proxy = False
        kwargs = ai_group_verify._build_ai_http_client_kwargs()
        assert "proxy" not in kwargs
        assert kwargs["trust_env"] is False

    print("approval smoke check passed")


if __name__ == "__main__":
    asyncio.run(run_checks())
