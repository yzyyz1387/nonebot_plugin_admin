#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import datetime
import importlib.util
import sys
import types
import warnings
from pathlib import Path

import nonebot
from nonebot.adapters.onebot.v11 import (
    GroupAdminNoticeEvent,
    GroupMessageEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupRecallNoticeEvent,
    GroupUploadNoticeEvent,
    HonorNotifyEvent,
    LuckyKingNotifyEvent,
    PokeNotifyEvent,
)

from _fake_orm import install_fake_orm_modules


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "nonebot_plugin_admin"
PKG_NAME = "_event_notice_smoke_pkg"

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

    statistics_package = types.ModuleType(f"{PKG_NAME}.statistics")
    statistics_package.__path__ = [str(PACKAGE_DIR / "statistics")]
    sys.modules[f"{PKG_NAME}.statistics"] = statistics_package

    event_notice_package = types.ModuleType(f"{PKG_NAME}.event_notice")
    event_notice_package.__path__ = [str(PACKAGE_DIR / "event_notice")]
    sys.modules[f"{PKG_NAME}.event_notice"] = event_notice_package



def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module



def load_event_notice_modules():
    bootstrap_package()
    modules = {}
    modules["util.time_util"] = load_module(f"{PKG_NAME}.util.time_util", PACKAGE_DIR / "util" / "time_util.py")
    modules["util.file_util"] = load_module(f"{PKG_NAME}.util.file_util", PACKAGE_DIR / "util" / "file_util.py")
    modules["config"] = load_module(f"{PKG_NAME}.core.config", PACKAGE_DIR / "core" / "config.py")
    modules["config"].plugin_config.statistics_orm_enabled = True
    modules["path"] = load_module(f"{PKG_NAME}.core.path", PACKAGE_DIR / "core" / "path.py")
    modules["utils"] = load_module(f"{PKG_NAME}.core.utils", PACKAGE_DIR / "core" / "utils.py")
    modules["models"] = load_module(
        f"{PKG_NAME}.statistics.models",
        PACKAGE_DIR / "statistics" / "models.py",
    )
    modules["recall_archive_store"] = load_module(
        f"{PKG_NAME}.event_notice.recall_archive_store",
        PACKAGE_DIR / "event_notice" / "recall_archive_store.py",
    )
    modules["anti_recall_flow"] = load_module(
        f"{PKG_NAME}.event_notice.anti_recall_flow",
        PACKAGE_DIR / "event_notice" / "anti_recall_flow.py",
    )
    modules["event_notice_flow"] = load_module(
        f"{PKG_NAME}.event_notice.event_notice_flow",
        PACKAGE_DIR / "event_notice" / "event_notice_flow.py",
    )
    modules["group_recall"] = load_module(
        f"{PKG_NAME}.event_notice.group_recall",
        PACKAGE_DIR / "event_notice" / "group_recall.py",
    )
    modules["particular_e_notice"] = load_module(
        f"{PKG_NAME}.event_notice.particular_e_notice",
        PACKAGE_DIR / "event_notice" / "particular_e_notice.py",
    )
    return modules



def assert_matcher_registered(matcher, *, matcher_type: str, priority: int, block: bool, module_suffix: str):
    assert matcher.type == matcher_type
    assert matcher.priority == priority
    assert matcher.block is block
    assert len(matcher.handlers) >= 1
    assert matcher.module_name.endswith(module_suffix)


class FakeNoticeBot:
    def __init__(self):
        self.self_id = 10000
        self.sent_messages = []
        self.get_msg_calls = []
        self.get_msg_response = {"message": "api fallback"}

    async def get_group_member_info(self, *, group_id: int, user_id: int, no_cache: bool = True):
        return {
            10000: {"user_id": 10000, "nickname": "bot", "card": ""},
            20001: {"user_id": 20001, "nickname": "小明", "card": ""},
            20002: {"user_id": 20002, "nickname": "管理员甲", "card": "管理甲"},
            20003: {"user_id": 20003, "nickname": "小红", "card": ""},
        }[user_id]

    async def get_stranger_info(self, *, user_id: int):
        return {
            20001: {"nickname": "小明"},
            20003: {"nickname": "小红"},
        }[user_id]

    async def get_msg(self, *, message_id: int):
        self.get_msg_calls.append(message_id)
        return self.get_msg_response

    async def send_group_msg(self, *, group_id: int, message):
        self.sent_messages.append({"group_id": group_id, "message": message})
        return {"group_id": group_id, "message": message}


async def immediate_sleep(_: float):
    return None



def build_poke_event():
    return PokeNotifyEvent.parse_obj(
        {
            "time": 0,
            "self_id": 10000,
            "post_type": "notice",
            "notice_type": "notify",
            "sub_type": "poke",
            "group_id": 12345,
            "user_id": 20001,
            "target_id": 10000,
        }
    )



def build_honor_event(honor_type: str, user_id: int):
    return HonorNotifyEvent.parse_obj(
        {
            "time": 0,
            "self_id": 10000,
            "post_type": "notice",
            "notice_type": "notify",
            "sub_type": "honor",
            "group_id": 12345,
            "user_id": user_id,
            "honor_type": honor_type,
        }
    )



def build_upload_event():
    return GroupUploadNoticeEvent.parse_obj(
        {
            "time": 0,
            "self_id": 10000,
            "post_type": "notice",
            "notice_type": "group_upload",
            "group_id": 12345,
            "user_id": 20001,
            "file": {"id": "1", "name": "demo.txt", "size": 1, "busid": 0},
        }
    )



def build_decrease_event(operator_id: int, user_id: int, sub_type: str = "kick"):
    return GroupDecreaseNoticeEvent.parse_obj(
        {
            "time": 1710000000,
            "self_id": 10000,
            "post_type": "notice",
            "notice_type": "group_decrease",
            "sub_type": sub_type,
            "group_id": 12345,
            "operator_id": operator_id,
            "user_id": user_id,
        }
    )



def build_increase_event(operator_id: int, user_id: int, sub_type: str = "approve"):
    return GroupIncreaseNoticeEvent.parse_obj(
        {
            "time": 0,
            "self_id": 10000,
            "post_type": "notice",
            "notice_type": "group_increase",
            "sub_type": sub_type,
            "group_id": 12345,
            "operator_id": operator_id,
            "user_id": user_id,
        }
    )



def build_admin_event(user_id: int, sub_type: str):
    return GroupAdminNoticeEvent.parse_obj(
        {
            "time": 0,
            "self_id": 10000,
            "post_type": "notice",
            "notice_type": "group_admin",
            "sub_type": sub_type,
            "group_id": 12345,
            "user_id": user_id,
        }
    )



def build_red_packet_event():
    return LuckyKingNotifyEvent.parse_obj(
        {
            "time": 0,
            "self_id": 10000,
            "post_type": "notice",
            "notice_type": "notify",
            "sub_type": "lucky_king",
            "group_id": 12345,
            "user_id": 20001,
            "target_id": 20003,
        }
    )


def build_group_message_event(message_id: int, raw_message: str, *, user_id: int = 20001, group_id: int = 12345):
    return GroupMessageEvent.parse_obj(
        {
            "time": 1710000100,
            "self_id": 10000,
            "post_type": "message",
            "sub_type": "normal",
            "user_id": user_id,
            "message_type": "group",
            "message_id": message_id,
            "message": [{"type": "text", "data": {"text": raw_message}}],
            "original_message": [{"type": "text", "data": {"text": raw_message}}],
            "raw_message": raw_message,
            "font": 14,
            "sender": {"user_id": user_id, "nickname": "小明", "card": "", "role": "member"},
            "to_me": False,
            "group_id": group_id,
            "anonymous": None,
        }
    )


def build_group_recall_event(message_id: int, *, user_id: int = 20001, group_id: int = 12345):
    return GroupRecallNoticeEvent.parse_obj(
        {
            "time": 1710000200,
            "self_id": 10000,
            "post_type": "notice",
            "notice_type": "group_recall",
            "group_id": group_id,
            "user_id": user_id,
            "operator_id": user_id,
            "message_id": message_id,
        }
    )


async def run_checks():
    modules = load_event_notice_modules()
    anti_recall_flow = modules["anti_recall_flow"]
    event_notice_flow = modules["event_notice_flow"]
    group_recall = modules["group_recall"]
    recall_archive_store = modules["recall_archive_store"]
    orm_models = modules["models"]
    particular_notice = modules["particular_e_notice"]

    event_notice_flow.asyncio.sleep = immediate_sleep

    assert_matcher_registered(group_recall.group_recall, matcher_type="notice", priority=5, block=False, module_suffix="group_recall")
    assert_matcher_registered(group_recall.group_recall_archive, matcher_type="message", priority=4, block=False, module_suffix="group_recall")
    assert_matcher_registered(particular_notice.poke, matcher_type="notice", priority=50, block=False, module_suffix="particular_e_notice")
    assert_matcher_registered(particular_notice.honor, matcher_type="notice", priority=50, block=False, module_suffix="particular_e_notice")
    assert_matcher_registered(particular_notice.upload_files, matcher_type="notice", priority=50, block=False, module_suffix="particular_e_notice")
    assert_matcher_registered(particular_notice.user_decrease, matcher_type="notice", priority=50, block=False, module_suffix="particular_e_notice")
    assert_matcher_registered(particular_notice.user_increase, matcher_type="notice", priority=50, block=False, module_suffix="particular_e_notice")
    assert_matcher_registered(particular_notice.admin_change, matcher_type="notice", priority=50, block=False, module_suffix="particular_e_notice")
    assert_matcher_registered(particular_notice.red_packet, matcher_type="notice", priority=50, block=False, module_suffix="particular_e_notice")

    assert anti_recall_flow.should_forward_recall(20001, 20001, "member", ["10000"]) is True
    assert anti_recall_flow.should_forward_recall(20001, 20002, "member", ["10000"]) is False
    assert anti_recall_flow.should_forward_recall(10000, 10000, "member", ["10000"]) is False
    assert anti_recall_flow.should_forward_recall(20001, 20001, "admin", ["10000"]) is False

    recall_text = anti_recall_flow.build_recall_message(
        {"user_id": 20001, "nickname": "小明", "card": ""},
        {"message": "你好"},
    )
    assert isinstance(recall_text, str)
    assert "小明" in recall_text and "你好" in recall_text

    recall_segments = anti_recall_flow.build_recall_message(
        {"user_id": 20001, "nickname": "小明", "card": "小明卡片"},
        {"message": [{"type": "text", "data": {"text": "hello"}}]},
    )
    assert "检测到" in str(recall_segments)
    assert "hello" in str(recall_segments)

    recall_cq_payload = anti_recall_flow.build_recall_message(
        {"user_id": 20001, "nickname": "小明", "card": ""},
        {"message": [{"type": "text", "data": {"text": "[CQ:image,file=demo.jpg,url=https://example.com/demo.jpg]"}}]},
    )
    assert str(recall_cq_payload[1]).startswith("[CQ:image")

    recall_cq_raw = anti_recall_flow.build_recall_message(
        {"user_id": 20001, "nickname": "小明", "card": ""},
        {"message": [], "raw_message": "[CQ:image,file=demo2.jpg,url=https://example.com/demo2.jpg]"},
    )
    assert str(recall_cq_raw[1]).startswith("[CQ:image")

    recall_fallback = anti_recall_flow.build_recall_message(
        {"user_id": 20001, "nickname": "小明", "card": ""},
        {"message": [{"bad": "segment"}]},
    )
    assert "bad" in str(recall_fallback)

    message_event = build_group_message_event(30001, "测试撤回")
    assert await recall_archive_store.archive_group_message_snapshot(message_event) is True
    assert len(orm_models.RecallMessageArchive._records) == 1

    archived_payload = await recall_archive_store.load_recalled_message_snapshot(12345, 30001)
    assert archived_payload is not None
    assert archived_payload["message_id"] == "30001"
    assert archived_payload["raw_message"] == "测试撤回"
    assert archived_payload["message"][0]["data"]["text"] == "测试撤回"

    await orm_models.StatisticsMessageRecord.create(
        group_id="12345",
        user_id="20003",
        message_id="30002",
        message_key="12345:30002",
        plain_text="旧消息回退",
        message_length=5,
        message_date=datetime.date(2026, 4, 21),
        message_hour=12,
        created_at=datetime.datetime(2026, 4, 21, 12, 0, 0),
    )
    statistics_fallback = await recall_archive_store.load_recalled_message_snapshot(12345, 30002)
    assert statistics_fallback is not None
    assert statistics_fallback["raw_message"] == "旧消息回退"
    assert statistics_fallback["message"][0]["data"]["text"] == "旧消息回退"

    resolve_bot = FakeNoticeBot()
    resolved_from_db = await group_recall.resolve_recalled_message(resolve_bot, 12345, 30001)
    assert resolved_from_db is not None
    assert resolved_from_db["raw_message"] == "测试撤回"
    assert resolve_bot.get_msg_calls == []

    resolved_from_stats = await group_recall.resolve_recalled_message(resolve_bot, 12345, 30002)
    assert resolved_from_stats is not None
    assert resolved_from_stats["raw_message"] == "旧消息回退"
    assert resolve_bot.get_msg_calls == []

    resolved_from_api = await group_recall.resolve_recalled_message(resolve_bot, 12345, 39999)
    assert resolved_from_api == resolve_bot.get_msg_response
    assert resolve_bot.get_msg_calls == [39999]

    bot = FakeNoticeBot()
    poke_event = build_poke_event()
    honor_event = build_honor_event("performer", 20001)
    upload_event = build_upload_event()
    decrease_event = build_decrease_event(20002, 20001)
    increase_event = build_increase_event(20002, 20003)
    admin_event = build_admin_event(20001, "set")
    red_packet_event = build_red_packet_event()

    assert await event_notice_flow.is_poke(bot, poke_event, {}) is True
    assert await event_notice_flow.is_honor(bot, honor_event, {}) is True
    assert await event_notice_flow.is_upload(bot, upload_event, {}) is True
    assert await event_notice_flow.is_user_decrease(bot, decrease_event, {}) is True
    assert await event_notice_flow.is_user_increase(bot, increase_event, {}) is True
    assert await event_notice_flow.is_admin_change(bot, admin_event, {}) is True
    assert await event_notice_flow.is_red_packet(bot, red_packet_event, {}) is True
    assert await event_notice_flow.is_poke(bot, honor_event, {}) is False

    assert event_notice_flow.get_avatar_url(20001).endswith("dst_uin=20001&spec=640")
    assert await event_notice_flow.build_honor_message(bot, build_honor_event("talkative", 10000)) == "新龙王诞生，原来是我自己~"
    assert "群聊之火" in await event_notice_flow.build_honor_message(bot, build_honor_event("performer", 20001))
    assert await event_notice_flow.build_honor_message(bot, build_honor_event("unknown", 20001)) == ""

    decrease_message = await event_notice_flow.build_member_decrease_message(bot, decrease_event)
    assert "送走了" in str(decrease_message)
    assert "小明" in str(decrease_message)
    assert "q4.qlogo.cn" in str(decrease_message)

    leave_message = await event_notice_flow.build_member_decrease_message(bot, build_decrease_event(20001, 20001, "leave"))
    assert "离开了本群" in str(leave_message)

    increase_message = await event_notice_flow.build_member_increase_message(bot, increase_event)
    assert "欢迎" in str(increase_message)
    assert "q4.qlogo.cn" in str(increase_message)

    assert await event_notice_flow.build_admin_change_message(bot, build_admin_event(20001, "set")) == "管理员变动\n恭喜 小明 成为管理员"
    assert await event_notice_flow.build_admin_change_message(bot, build_admin_event(10000, "unset")) == "管理员变动\n我 不再是本群管理员"

    print("event notice smoke check passed")


if __name__ == "__main__":
    asyncio.run(run_checks())
