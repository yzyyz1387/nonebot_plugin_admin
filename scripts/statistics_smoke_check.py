#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import importlib.util
import inspect
import json
import sys
import tempfile
import types
import warnings
from pathlib import Path
from typing import List, Optional

import nonebot
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent
from nonebot.consts import CMD_ARG_KEY, CMD_KEY, PREFIX_KEY, RAW_CMD_KEY, SHELL_ARGS, SHELL_ARGV


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "nonebot_plugin_admin"
PKG_NAME = "_statistics_smoke_pkg"

warnings.filterwarnings(
    "ignore",
    message="You seem to already have a custom sys.excepthook handler installed.*",
    category=RuntimeWarning,
)

def install_fake_orm_modules():
    plugin_module = sys.modules.get("nonebot_plugin_tortoise_orm")
    if plugin_module is None:
        plugin_module = types.ModuleType("nonebot_plugin_tortoise_orm")
        plugin_module.registered_models = []
        plugin_module.__spec__ = importlib.util.spec_from_loader("nonebot_plugin_tortoise_orm", loader=None)

        def _fake_add_model(model_path: str):
            plugin_module.registered_models.append(model_path)

        plugin_module.add_model = _fake_add_model
        sys.modules["nonebot_plugin_tortoise_orm"] = plugin_module

    if "tortoise" in sys.modules:
        return

    tortoise_module = types.ModuleType("tortoise")
    fields_module = types.ModuleType("tortoise.fields")
    models_module = types.ModuleType("tortoise.models")

    def _fake_field(*args, **kwargs):
        return None

    for field_name in [
        "IntField",
        "BigIntField",
        "CharField",
        "TextField",
        "BooleanField",
        "DatetimeField",
        "DateField",
        "SmallIntField",
    ]:
        setattr(fields_module, field_name, _fake_field)

    class FakeQuerySet:
        def __init__(self, model_cls, lookup):
            self.model_cls = model_cls
            self.lookup = lookup

        def _matches(self, record) -> bool:
            return all(getattr(record, key, None) == value for key, value in self.lookup.items())

        def _results(self):
            return [record for record in self.model_cls._records if self._matches(record)]

        async def delete(self):
            matched = self._results()
            self.model_cls._records = [record for record in self.model_cls._records if not self._matches(record)]
            return len(matched)

        async def all(self):
            return list(self._results())

        async def first(self):
            results = self._results()
            return results[0] if results else None

    class FakeModel:
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            cls._records = []
            cls._next_id = 1

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
            if getattr(self, "id", None) is None:
                self.id = self.__class__._next_id
                self.__class__._next_id += 1

        async def save(self):
            records = self.__class__._records
            for index, record in enumerate(records):
                if getattr(record, "id", None) == getattr(self, "id", None):
                    records[index] = self
                    return
            records.append(self)

        @classmethod
        async def create(cls, **kwargs):
            record = cls(**kwargs)
            cls._records.append(record)
            return record

        @classmethod
        async def get_or_create(cls, defaults=None, **lookup):
            defaults = defaults or {}
            for record in cls._records:
                if all(getattr(record, key, None) == value for key, value in lookup.items()):
                    return record, False
            record = cls(**lookup, **defaults)
            cls._records.append(record)
            return record, True

        @classmethod
        async def update_or_create(cls, defaults=None, **lookup):
            defaults = defaults or {}
            for record in cls._records:
                if all(getattr(record, key, None) == value for key, value in lookup.items()):
                    for key, value in defaults.items():
                        setattr(record, key, value)
                    return record, False
            record = cls(**lookup, **defaults)
            cls._records.append(record)
            return record, True

        @classmethod
        def filter(cls, **lookup):
            return FakeQuerySet(cls, lookup)

        @classmethod
        async def all(cls):
            return list(cls._records)

        @classmethod
        async def bulk_create(cls, objs):
            for obj in objs:
                if getattr(obj, "id", None) is None:
                    obj.id = cls._next_id
                    cls._next_id += 1
                cls._records.append(obj)

    tortoise_module.fields = fields_module
    models_module.Model = FakeModel

    sys.modules["tortoise"] = tortoise_module
    sys.modules["tortoise.fields"] = fields_module
    sys.modules["tortoise.models"] = models_module

def bootstrap_package():
    nonebot.init(superusers={"10000"}, host="127.0.0.1", port=8080)
    nonebot.require = lambda name: None
    install_fake_orm_modules()
    if not hasattr(nonebot, "get_plugin_config"):
        def _compat_get_plugin_config(config_cls):
            return config_cls()

        nonebot.get_plugin_config = _compat_get_plugin_config

    if "imageio" not in sys.modules:
        imageio = types.ModuleType("imageio")

        def _fake_imread(*args, **kwargs):
            raise RuntimeError("imageio is not available in statistics smoke check")

        imageio.imread = _fake_imread
        sys.modules["imageio"] = imageio

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

    migration_package = types.ModuleType(f"{PKG_NAME}.migration")
    migration_package.__path__ = [str(PACKAGE_DIR / "migration")]
    sys.modules[f"{PKG_NAME}.migration"] = migration_package


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_statistics_modules():
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
    modules["config"].plugin_config.statistics_orm_capture_message_content = True
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
    modules["statistics_store"] = load_module(
        f"{PKG_NAME}.statistics.statistics_store",
        PACKAGE_DIR / "statistics" / "statistics_store.py",
    )
    modules["legacy_store"] = load_module(
        f"{PKG_NAME}.statistics.legacy_store",
        PACKAGE_DIR / "statistics" / "legacy_store.py",
    )
    modules["orm_bootstrap"] = load_module(
        f"{PKG_NAME}.statistics.orm_bootstrap",
        PACKAGE_DIR / "statistics" / "orm_bootstrap.py",
    )
    modules["orm_store"] = load_module(
        f"{PKG_NAME}.statistics.orm_store",
        PACKAGE_DIR / "statistics" / "orm_store.py",
    )
    modules["migrate"] = load_module(
        f"{PKG_NAME}.migration.migrate",
        PACKAGE_DIR / "migration" / "migrate.py",
    )
    modules["stop_words_flow"] = load_module(
        f"{PKG_NAME}.statistics.stop_words_flow",
        PACKAGE_DIR / "statistics" / "stop_words_flow.py",
    )
    modules["statistics_read_service"] = load_module(
        f"{PKG_NAME}.statistics.statistics_read_service",
        PACKAGE_DIR / "statistics" / "statistics_read_service.py",
    )
    modules["statistics_record_flow"] = load_module(
        f"{PKG_NAME}.statistics.statistics_record_flow",
        PACKAGE_DIR / "statistics" / "statistics_record_flow.py",
    )
    modules["statistics_query_flow"] = load_module(
        f"{PKG_NAME}.statistics.statistics_query_flow",
        PACKAGE_DIR / "statistics" / "statistics_query_flow.py",
    )
    modules["wordcloud_resource_flow"] = load_module(
        f"{PKG_NAME}.statistics.wordcloud_resource_flow",
        PACKAGE_DIR / "statistics" / "wordcloud_resource_flow.py",
    )
    modules["wordcloud_generate_flow"] = load_module(
        f"{PKG_NAME}.statistics.wordcloud_generate_flow",
        PACKAGE_DIR / "statistics" / "wordcloud_generate_flow.py",
    )
    modules["group_message_config"] = load_module(
        f"{PKG_NAME}.statistics.group_message_config",
        PACKAGE_DIR / "statistics" / "group_message_config.py",
    )
    modules["group_message_send_flow"] = load_module(
        f"{PKG_NAME}.statistics.group_message_send_flow",
        PACKAGE_DIR / "statistics" / "group_message_send_flow.py",
    )
    modules["group_message_schedule_flow"] = load_module(
        f"{PKG_NAME}.statistics.group_message_schedule_flow",
        PACKAGE_DIR / "statistics" / "group_message_schedule_flow.py",
    )
    modules["word_analyze"] = load_module(
        f"{PKG_NAME}.statistics.word_analyze",
        PACKAGE_DIR / "statistics" / "word_analyze.py",
    )
    modules["wordcloud"] = load_module(
        f"{PKG_NAME}.statistics.wordcloud",
        PACKAGE_DIR / "statistics" / "wordcloud.py",
    )
    return modules


def patch_paths(modules: dict, temp_root: Path):
    config_dir = temp_root / "config"
    words_dir = config_dir / "words"
    stop_words_dir = config_dir / "stop_words"
    message_data_dir = config_dir / "group_message_data"
    wordcloud_bg_dir = config_dir / "wordcloud_bg"
    resource_dir = temp_root / "resource"
    imgs_dir = resource_dir / "imgs"
    ttf_path = resource_dir / "msyhblod.ttf"
    word_config_path = config_dir / "word_config.txt"
    record_state_path = config_dir / "statistics_record_state.json"
    limit_word_path = config_dir / "违禁词.txt"
    switcher_path = config_dir / "开关.json"
    config_admin_path = config_dir / "admin.json"
    config_group_admin_path = config_dir / "group_admin.json"
    approval_blacklist_path = config_dir / "加群验证信息黑名单.json"
    broadcast_avoid_path = config_dir / "广播排除群聊.json"
    user_violation_info_path = config_dir / "群内用户违规信息"

    for path in [config_dir, words_dir, stop_words_dir, message_data_dir, wordcloud_bg_dir, imgs_dir, user_violation_info_path]:
        path.mkdir(parents=True, exist_ok=True)
    word_config_path.write_text("", encoding="utf-8")
    record_state_path.write_text('{"version": 2, "mode": "disabled_groups", "disabled_groups": []}', encoding="utf-8")
    ttf_path.parent.mkdir(parents=True, exist_ok=True)
    ttf_path.write_bytes(b"fake-font")

    modules["path"].config_path = config_dir
    modules["path"].legacy_backup_path = config_dir / "legacy_backup"
    modules["path"].config_admin = config_admin_path
    modules["path"].config_group_admin = config_group_admin_path
    modules["path"].word_path = word_config_path
    modules["path"].statistics_record_state_path = record_state_path
    modules["path"].words_contents_path = words_dir
    modules["path"].stop_words_path = stop_words_dir
    modules["path"].group_message_data_path = message_data_dir
    modules["path"].wordcloud_bg_path = wordcloud_bg_dir
    modules["path"].limit_word_path = limit_word_path
    modules["path"].switcher_path = switcher_path
    modules["path"].appr_bk = approval_blacklist_path
    modules["path"].broadcast_avoid_path = broadcast_avoid_path
    modules["path"].user_violation_info_path = user_violation_info_path
    modules["path"].res_path = resource_dir
    modules["path"].re_img_path = imgs_dir
    modules["path"].ttf_name = ttf_path
    modules["path"].ttf_path = ttf_path

    modules["utils"].config_path = config_dir
    modules["utils"].legacy_backup_path = config_dir / "legacy_backup"
    modules["utils"].config_admin = config_admin_path
    modules["utils"].config_group_admin = config_group_admin_path
    modules["utils"].word_path = word_config_path
    modules["utils"].statistics_record_state_path = record_state_path
    modules["utils"].words_contents_path = words_dir
    modules["utils"].stop_words_path = stop_words_dir
    modules["utils"].group_message_data_path = message_data_dir
    modules["utils"].wordcloud_bg_path = wordcloud_bg_dir
    modules["utils"].limit_word_path = limit_word_path
    modules["utils"].switcher_path = switcher_path
    modules["utils"].appr_bk = approval_blacklist_path
    modules["utils"].broadcast_avoid_path = broadcast_avoid_path
    modules["utils"].user_violation_info_path = user_violation_info_path
    modules["utils"].res_path = resource_dir
    modules["utils"].re_img_path = imgs_dir
    modules["utils"].ttf_name = ttf_path
    modules["utils"].ttf_path = ttf_path
    modules["stop_words_flow"].stop_words_path = stop_words_dir


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


class FakeGroupBot:
    def __init__(self):
        self.member_infos = {
            "20001": {"card": "群名片A", "nickname": "昵称A"},
            "20002": {"card": "", "nickname": "昵称B"},
            "20003": {"card": "", "nickname": "昵称C"},
        }

    async def get_group_member_list(self, group_id: int):
        return [
            {"user_id": 20001},
            {"user_id": 20002},
            {"user_id": 20003},
        ]

    async def get_group_member_info(self, group_id: int, user_id: int):
        return self.member_infos.get(str(user_id), {"card": "", "nickname": str(user_id)})


class FakeSendBot:
    def __init__(self):
        self.messages = []

    async def send_group_msg(self, group_id, message):
        self.messages.append((group_id, message))

class FinishedException(Exception):
    pass


class FakeMatcher:
    def __init__(self):
        self.messages = []

    async def send(self, message):
        self.messages.append(str(message))

    async def finish(self, message=None):
        if message is not None:
            self.messages.append(str(message))
        raise FinishedException()


class FakeScheduler:
    def __init__(self):
        self.jobs = []

    def add_job(self, func, trigger, hour, minute, id):
        self.jobs.append((func, trigger, hour, minute, id))


class FakeResponse:
    def __init__(self, text: str):
        self.text = text


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


async def always_enabled(_func_name: str, _group_id: str) -> bool:
    return True


async def run_checks():
    modules = load_statistics_modules()
    with tempfile.TemporaryDirectory(prefix="statistics-smoke-") as temp_dir:
        temp_root = Path(temp_dir)
        patch_paths(modules, temp_root)

        statistics_store = modules["statistics_store"]
        statistics_record_flow = modules["statistics_record_flow"]
        statistics_query_flow = modules["statistics_query_flow"]
        wordcloud_resource_flow = modules["wordcloud_resource_flow"]
        wordcloud_generate_flow = modules["wordcloud_generate_flow"]
        orm_store = modules["orm_store"]
        migrate = modules["migrate"]
        config_orm_store = modules["config_orm_store"]
        legacy_store = modules["legacy_store"]
        stop_words_flow = modules["stop_words_flow"]
        statistics_read_service = modules["statistics_read_service"]
        orm_models = modules["models"]
        group_message_config_module = modules["group_message_config"]
        group_message_send_flow = modules["group_message_send_flow"]
        group_message_schedule_flow = modules["group_message_schedule_flow"]
        word_analyze = modules["word_analyze"]
        wordcloud = modules["wordcloud"]

        gid = "10001"
        permission_bot = FakePermissionBot(["10000"])
        fake_group_bot = FakeGroupBot()

        assert legacy_store.load_record_enabled_groups() == []
        enabled, message = await statistics_record_flow.handle_enable_group_recording(gid)
        await asyncio.sleep(0)
        assert enabled is True
        assert message == "本群消息记录当前状态为：已开启\n若要关闭，请发送【停止记录本群】"
        assert await statistics_store.is_group_record_enabled(gid) is True
        assert len(orm_models.StatisticsGroupRecordSetting._records) == 1
        assert orm_models.StatisticsGroupRecordSetting._records[0].enabled is True

        enabled, message = await statistics_record_flow.handle_enable_group_recording(gid)
        assert enabled is False
        assert message == "本群消息记录当前状态为：已开启\n若要关闭，请发送【停止记录本群】"

        await statistics_record_flow.record_group_message(gid, "20001", "第一条消息", "2026-04-18", message_id="m1", created_at="2026-04-18T08:30:00")
        await statistics_record_flow.record_group_message(gid, "20002", "第二条消息", "2026-04-18", message_id="m2", created_at="2026-04-18T09:45:00")
        assert await statistics_store.load_daily_message_stats(gid, "2026-04-18") == {"20001": 1, "20002": 1}
        assert await statistics_store.load_history_message_stats(gid) == {"20001": 1, "20002": 1}
        assert await orm_store.load_group_word_corpus_lines(gid) == ["第一条消息", "第二条消息"]
        assert {(record.group_id, record.user_id, record.message_count) for record in orm_models.StatisticsHistoryMessageStat._records} == {(gid, "20001", 1), (gid, "20002", 1)}
        assert {(record.group_id, record.user_id, str(record.stat_date), record.message_count) for record in orm_models.StatisticsDailyMessageStat._records} == {(gid, "20001", "2026-04-18", 1), (gid, "20002", "2026-04-18", 1)}
        assert {(record.message_key, record.plain_text, record.message_hour) for record in orm_models.StatisticsMessageRecord._records} == {("10001:m1", "第一条消息", 8), ("10001:m2", "第二条消息", 9)}

        disabled, message = await statistics_record_flow.handle_disable_group_recording(gid)
        await asyncio.sleep(0)
        assert disabled is True
        assert message == "本群消息记录当前状态为：已关闭\n若要开启，请发送【记录本群】\n历史记录不会删除。"
        assert await statistics_store.is_group_record_enabled(gid) is False
        assert orm_models.StatisticsGroupRecordSetting._records[0].enabled is False

        await statistics_record_flow.record_group_message(gid, "20001", "第三条消息", "2026-04-18", message_id="m3", created_at="2026-04-18T10:15:00")
        assert await statistics_store.load_daily_message_stats(gid, "2026-04-18") == {"20001": 2, "20002": 1}
        assert await statistics_store.load_history_message_stats(gid) == {"20001": 2, "20002": 1}
        assert await orm_store.load_group_word_corpus_lines(gid) == ["第一条消息", "第二条消息"]
        assert len(orm_models.StatisticsMessageRecord._records) == 2
        assert {(record.group_id, record.user_id, record.message_count) for record in orm_models.StatisticsHistoryMessageStat._records} == {(gid, "20001", 2), (gid, "20002", 1)}

        disabled, message = await statistics_record_flow.handle_disable_group_recording(gid)
        assert disabled is False
        assert message == "本群消息记录当前状态为：已关闭\n若要开启，请发送【记录本群】"

        add_stop_words_matcher = FakeMatcher()
        await stop_words_flow.handle_add_group_stop_words(gid, add_stop_words_matcher, "屏蔽词A 屏蔽词B")
        assert await stop_words_flow.load_group_stop_words(gid) == ["屏蔽词A", "屏蔽词B"]
        assert {(record.group_id, record.word) for record in orm_models.StatisticsGroupStopWord._records} == {
            (gid, "屏蔽词A"),
            (gid, "屏蔽词B"),
        }
        assert not (modules["path"].stop_words_path / f"{gid}.txt").exists()

        del_stop_words_matcher = FakeMatcher()
        try:
            await stop_words_flow.handle_delete_group_stop_words(gid, del_stop_words_matcher, "屏蔽词A")
        except FinishedException:
            pass
        assert await stop_words_flow.load_group_stop_words(gid) == ["屏蔽词B"]
        assert {(record.group_id, record.word) for record in orm_models.StatisticsGroupStopWord._records} == {
            (gid, "屏蔽词B"),
        }

        await orm_store.set_daily_message_stat(gid, "20003", "2026-04-17", 4)
        await orm_store.set_history_message_stat(gid, "20003", 7)
        assert {(record.group_id, record.user_id, str(record.stat_date), record.message_count) for record in orm_models.StatisticsDailyMessageStat._records} >= {
            (gid, "20003", "2026-04-17", 4),
        }
        assert {(record.group_id, record.user_id, record.message_count) for record in orm_models.StatisticsHistoryMessageStat._records} >= {
            (gid, "20003", 7),
        }

        assert await config_orm_store.orm_replace_content_guard_rules([["广告", "$撤回"], ["刷单", "$禁言"]]) is True
        assert await config_orm_store.orm_load_content_guard_rules() == [["广告", "$撤回"], ["刷单", "$禁言"]]
        assert await config_orm_store.orm_add_content_guard_rule("广告", "$撤回") is False
        assert await config_orm_store.orm_add_content_guard_rule("引流", "$撤回$禁言") is True
        assert await config_orm_store.orm_delete_content_guard_rule("刷单", "$禁言") is True
        assert await config_orm_store.orm_load_content_guard_rules() == [["广告", "$撤回"], ["引流", "$撤回$禁言"]]

        assert await orm_store.replace_group_word_corpus(gid, ["词料A", "词料B"], source_type="legacy") is True
        assert await orm_store.load_group_word_corpus_lines(gid) == ["词料A", "词料B"]
        assert await orm_store.append_group_word_corpus(gid, "词料C", source_type="message", created_at="2026-04-18T12:00:00") is True
        assert await orm_store.load_group_word_corpus_lines(gid) == ["词料A", "词料B", "词料C"]
        assert await orm_store.load_group_word_corpus_text(gid) == "词料A\n词料B\n词料C\n"

        await orm_store.replace_group_word_corpus(gid, ["绗竴鏉℃秷鎭?", "绗簩鏉℃秷鎭?"], source_type="message")
        await orm_store.replace_group_word_corpus(gid, ["第一条消息", "第二条消息"], source_type="message")
        wordcloud_source = await statistics_read_service.load_group_wordcloud_source(gid)
        assert wordcloud_source.available is True
        assert wordcloud_source.text == "\u7b2c\u4e00\u6761\u6d88\u606f\n\u7b2c\u4e8c\u6761\u6d88\u606f\n"
        assert "\u5c4f\u853d\u8bcdB" in wordcloud_source.stop_words
        assert await statistics_read_service.daily_message_stats_exists_snapshot(gid, "2026-04-18") is True
        assert await statistics_read_service.load_daily_message_stats_snapshot(gid, "2026-04-18") == {"20001": 2, "20002": 1}
        assert await statistics_read_service.load_history_message_stats_snapshot(gid) == {"20001": 2, "20002": 1, "20003": 7}

        top_message = await statistics_query_flow.build_top_speaker_message(
            fake_group_bot,
            gid,
            {"99999": 9, "20001": 5, "20002": 3},
        )
        assert top_message == "太强了！今日榜首：\n群名片A，发了5条消息"

        ranking_message = await statistics_query_flow.build_ranking_message(
            fake_group_bot,
            gid,
            {"99999": 9, "20001": 5, "20002": 3, "20003": 1},
        )
        assert ranking_message == "1. 群名片A，发了5条消息\n2. 昵称B，发了3条消息\n3. 昵称C，发了1条消息"

        history_count_messages = await statistics_query_flow.build_member_count_messages(
            fake_group_bot,
            gid,
            {"20001": 5},
            ["20001", "20003"],
            today=False,
        )
        assert history_count_messages == [
            "有记录以来群名片A在本群发了5条消息",
            "昵称C没有发消息",
        ]

        today_count_messages = await statistics_query_flow.build_member_count_messages(
            fake_group_bot,
            gid,
            {"20002": 2},
            ["20002", "20003"],
            today=True,
        )
        assert today_count_messages == [
            "今天昵称B发了2条消息",
            "今天昵称C没有发消息",
        ]

        assert await wordcloud_resource_flow.build_background_update_notice() is None
        assert await wordcloud_resource_flow.sync_backgrounds() == (0, 0)
        assert await wordcloud_resource_flow.ensure_local_backgrounds() is True
        assert wordcloud_resource_flow.build_mask_deprecation_message() == "当前词云已切换为 HTML 截图模式，不再需要更新 mask。"

        payload_ok, payload_text, payload_stop_words = await wordcloud_generate_flow.prepare_group_wordcloud_payload(
            gid,
            types.SimpleNamespace(lcut=lambda text: text.split()),
        )
        assert payload_ok is True
        assert payload_text == "第一条消息 第二条消息"
        assert payload_stop_words is not None

        payload_ok, payload_text, payload_stop_words = await wordcloud_generate_flow.prepare_group_wordcloud_payload(
            "99999",
            types.SimpleNamespace(lcut=lambda text: text.split()),
        )
        assert payload_ok is False
        assert payload_text == "当前群还没有可用于词云的消息记录，请等待群消息积累后再试。"
        assert payload_stop_words is None

        cloud_items = wordcloud_generate_flow.build_wordcloud_items(
            "统计 测试 统计 词云 测试 群聊",
            stop_words={"测试"},
        )
        assert [item.word for item in cloud_items[:3]] == ["统计", "词云", "群聊"]
        assert cloud_items[0].count == 2

        context = wordcloud_generate_flow.build_wordcloud_template_context(
            gid,
            "统计 测试 统计 词云 群聊 群聊",
            stop_words={"测试"},
        )
        assert context["group_id"] == gid
        assert context["top_word_count"] == 2
        assert len(context["cloud_items"]) >= 2

        captured = {}

        async def fake_screenshot_renderer(
            html: str,
            img_path: Path,
            *,
            selector: Optional[str] = None,
            viewport_width: int = 0,
            viewport_height: int = 0,
            wait_ms: int = 0,
        ) -> bytes:
            captured["html"] = html
            captured["selector"] = selector
            captured["viewport"] = (viewport_width, viewport_height)
            captured["wait_ms"] = wait_ms
            Path(img_path).write_bytes(b"fake-wordcloud")
            return b"fake-wordcloud"

        success, result = await wordcloud_generate_flow.render_wordcloud_image(
            "统计 测试 统计 词云 群聊",
            stop_words={"测试"},
            img_path=modules["path"].re_img_path / "wordcloud_test.png",
            group_id=gid,
            template_renderer=lambda render_context: f"<section class='wordcloud-card'>{render_context['group_id']}</section>",
            screenshot_renderer=fake_screenshot_renderer,
        )
        assert success is True
        assert result == b"fake-wordcloud"
        assert captured["selector"] == ".wordcloud-card"
        assert gid in captured["html"]

        GroupMessageConfig = group_message_config_module.GroupMessageConfig
        config = group_message_config_module.load_group_message_config(
            types.SimpleNamespace(
                send_group_id='["10001", "10002"]',
                send_switch_morning="false",
                send_switch_night="true",
                send_mode="1",
                send_sentence_morning='["早上好", "今天也加油"]',
                send_sentence_night=["晚安"],
                send_time_morning="8 30",
                send_time_night="23 15",
            )
        )
        assert config.group_ids == ["10001", "10002"]
        assert config.morning_enabled is False
        assert config.night_enabled is True
        assert config.mode == 1
        assert config.morning_sentences == ["早上好", "今天也加油"]
        assert config.night_sentences == ["晚安"]
        assert (config.morning_hour, config.morning_minute) == ("8", "30")
        assert (config.night_hour, config.night_minute) == ("23", "15")

        hitokoto_message = group_message_send_flow.fetch_hitokoto_message(
            request_get=lambda _url: FakeResponse('{"hitokoto":"测试一言","from":"测试作品","from_who":"测试作者"}')
        )
        assert hitokoto_message == "测试一言\n——《测试作品》测试作者"

        custom_message = group_message_send_flow.build_group_message_content(
            config,
            "morning",
            choice_func=lambda items: items[0],
        )
        assert custom_message == "早上好"

        api_message = group_message_send_flow.build_group_message_content(
            GroupMessageConfig(group_ids=["10001"], mode=2),
            "night",
            hitokoto_fetcher=lambda: "来自接口",
        )
        assert api_message == "来自接口"

        fake_send_bot = FakeSendBot()
        sent_count = await group_message_send_flow.send_group_messages_once(
            GroupMessageConfig(group_ids=["10001", "10002"], mode=1, morning_sentences=["早上好"]),
            "morning",
            bots_provider=lambda: {"bot": fake_send_bot},
            status_checker=always_enabled,
            choice_func=lambda items: items[0],
        )
        assert sent_count == 2
        assert fake_send_bot.messages == [("10001", "早上好"), ("10002", "早上好")]

        fake_send_bot = FakeSendBot()
        executed = await group_message_send_flow.run_group_message_job(
            GroupMessageConfig(group_ids=["10001"], mode=2),
            "morning",
            bots_provider=lambda: {"bot": fake_send_bot},
            status_checker=always_enabled,
            hitokoto_fetcher=lambda: "接口消息",
            sleep_func=lambda _seconds: asyncio.sleep(0),
            delay_func=lambda: 0,
        )
        assert executed is True
        assert fake_send_bot.messages == [("10001", "接口消息")]

        executed = await group_message_send_flow.run_group_message_job(
            GroupMessageConfig(group_ids=["10001"], morning_enabled=False),
            "morning",
            bots_provider=lambda: {"bot": fake_send_bot},
            status_checker=always_enabled,
            sleep_func=lambda _seconds: asyncio.sleep(0),
            delay_func=lambda: 0,
        )
        assert executed is False

        fake_scheduler = FakeScheduler()
        group_message_schedule_flow.register_group_message_jobs(
            fake_scheduler,
            config,
            send_morning_job=lambda: None,
            send_night_job=lambda: None,
        )
        assert fake_scheduler.jobs[0][1:] == ("cron", "8", "30", "send_morning")
        assert fake_scheduler.jobs[1][1:] == ("cron", "23", "15", "send_night")

        assert_matcher_registered(
            word_analyze.word_start,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".word_analyze",
            rule_contains=["记录本群"],
        )
        assert_matcher_registered(
            word_analyze.word_stop,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".word_analyze",
            rule_contains=["停止记录本群"],
        )
        assert_matcher_registered(
            word_analyze.who_speak_most_today,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".word_analyze",
            rule_contains=["今日榜首", "今天谁话多"],
        )
        assert_matcher_registered(
            word_analyze.speak_top,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".word_analyze",
            rule_contains=["今日发言排行", "今日排行榜"],
        )
        assert_matcher_registered(
            word_analyze.speak_top_yesterday,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".word_analyze",
            rule_contains=["昨日发言排行", "昨日排行榜"],
        )
        assert_matcher_registered(
            word_analyze.who_speak_most,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".word_analyze",
            rule_contains=["排行", "排行榜"],
        )
        assert_matcher_registered(
            word_analyze.get_speak_num,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".word_analyze",
            rule_contains=["发言数", "发言量"],
        )
        assert_matcher_registered(
            word_analyze.get_speak_num_today,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".word_analyze",
            rule_contains=["今日发言数", "今日发言量"],
        )
        assert_matcher_registered(
            wordcloud.cloud,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".wordcloud",
            rule_contains=["群词云"],
        )
        assert_matcher_registered(
            wordcloud.update_mask,
            matcher_type="message",
            priority=2,
            block=True,
            module_suffix=".wordcloud",
            rule_contains=["更新mask", "下载mask"],
        )

        await assert_matcher_runtime(
            word_analyze.word_start,
            bot=permission_bot,
            event=build_group_message_event("记录本群", 20001, role="admin"),
            state=build_command_state("记录本群"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            word_analyze.word_start,
            bot=permission_bot,
            event=build_group_message_event("记录本群123", 20001, role="admin"),
            state=build_command_state("记录本群"),
            rule_expected=False,
        )
        await assert_matcher_runtime(
            word_analyze.word_start,
            bot=permission_bot,
            event=build_group_message_event("记录本群", 20002, role="member"),
            state=build_command_state("记录本群"),
            perm_expected=False,
        )
        await assert_matcher_runtime(
            word_analyze.word_stop,
            bot=permission_bot,
            event=build_group_message_event("停止记录本群", 10000),
            state=build_command_state("停止记录本群"),
            perm_expected=True,
        )
        await assert_matcher_runtime(
            word_analyze.who_speak_most_today,
            bot=permission_bot,
            event=build_group_message_event("今日榜首", 20003),
            state=build_command_state("今日榜首"),
        )
        await assert_matcher_runtime(
            word_analyze.who_speak_most_today,
            bot=permission_bot,
            event=build_group_message_event("今日榜首123", 20003),
            state=build_command_state("今日榜首"),
            rule_expected=False,
        )
        await assert_matcher_runtime(
            word_analyze.get_speak_num,
            bot=permission_bot,
            event=build_group_message_event("发言数", 20003),
            state=build_command_state("发言数"),
        )
        await assert_matcher_runtime(
            word_analyze.stop_words_list,
            bot=permission_bot,
            event=build_group_message_event("停用词列表123", 20001, role="admin"),
            state=build_command_state("停用词列表"),
            rule_expected=False,
        )
        await assert_matcher_runtime(
            wordcloud.cloud,
            bot=permission_bot,
            event=build_group_message_event("群词云123", 20003),
            state=build_command_state("群词云"),
            rule_expected=False,
        )
        await assert_matcher_runtime(
            wordcloud.update_mask,
            bot=permission_bot,
            event=build_group_message_event("更新mask", 20001, role="admin"),
            state=build_command_state("更新mask"),
            perm_expected=True,
        )

        modules["path"].limit_word_path.write_text("广告\t$撤回\n刷单\t$禁言\n", encoding="utf-8")
        (modules["path"].words_contents_path / "30001.txt").write_text("旧词料A\n旧词料B\n", encoding="utf-8")
        (modules["path"].words_contents_path / "30002.txt").write_text("旧词料C\n", encoding="utf-8")
        (modules["path"].group_message_data_path / "30002").mkdir(parents=True, exist_ok=True)
        modules["path"].word_path.write_text("30001\n", encoding="utf-8")
        violation_group_dir = modules["path"].user_violation_info_path / "30003"
        violation_group_dir.mkdir(parents=True, exist_ok=True)
        (violation_group_dir / "40001.json").write_text(
            json.dumps(
                {
                    "40001": {
                        "level": 2,
                        "info": {
                            "2026-04-19T10:00:00": ["Spam", "legacy violation"],
                        },
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        await migrate.run_migration_check()

        assert [[record.pattern, record.options] for record in orm_models.ContentGuardRule._records] == [
            ["广告", "$撤回"],
            ["刷单", "$禁言"],
        ]
        assert [record.content for record in orm_models.StatisticsWordCorpus._records if record.group_id == "30001"] == [
            "旧词料A",
            "旧词料B",
        ]
        assert [record.content for record in orm_models.StatisticsWordCorpus._records if record.group_id == "30002"] == [
            "旧词料C",
        ]
        record_state_map = {record.group_id: record.enabled for record in orm_models.StatisticsGroupRecordSetting._records}
        assert record_state_map["30001"] is True
        assert record_state_map["30002"] is False
        assert ("30003", "40001", 2) in {
            (record.group_id, record.user_id, record.level)
            for record in orm_models.UserViolation._records
        }
        assert ("30003", "40001", "Spam", "legacy violation") in {
            (record.group_id, record.user_id, record.label, record.content)
            for record in orm_models.ViolationRecord._records
        }
        migrated_paths = {record.file_path for record in orm_models.MigrationManifest._records}
        assert "违禁词.txt" in migrated_paths
        assert "words/30001.txt" in migrated_paths
        assert "words/30002.txt" in migrated_paths
        assert "word_config.txt" in migrated_paths
        assert "开关.json" not in migrated_paths

        user_violation_targets = {
            rel_path
            for rel_path, _, data_type in migrate._collect_migration_targets()
            if data_type == "user_violations"
        }
        assert user_violation_targets <= migrated_paths
        assert not modules["path"].limit_word_path.exists()
        assert not (modules["path"].words_contents_path / "30001.txt").exists()
        assert not (modules["path"].words_contents_path / "30002.txt").exists()
        assert not modules["path"].word_path.exists()
        assert not modules["path"].user_violation_info_path.exists()
        backup_root = modules["path"].legacy_backup_path
        assert backup_root.exists()
        assert list(backup_root.rglob("30001.txt"))
        assert list(backup_root.rglob("30002.txt"))
        assert list(backup_root.rglob(modules["path"].word_path.name))
        assert list(backup_root.rglob(modules["path"].limit_word_path.name))
        assert list(backup_root.rglob("40001.json"))

    print("statistics smoke check passed")


if __name__ == "__main__":
    asyncio.run(run_checks())
