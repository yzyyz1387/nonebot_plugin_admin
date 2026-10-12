from __future__ import annotations

import asyncio
import json
import os
import re
import signal
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from nonebot import get_driver, logger, on_message
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.matcher import Matcher
from nonebot.rule import Rule
from nonebot.typing import T_State

from ..dashboard.dashboard_oplog_service import record_oplog
from . import path as admin_path


RESTART_NOTICE_TTL_SECONDS = 60 * 60
RESTART_PREPARE_DELAY_SECONDS = 0.4
RESTART_CANCEL_WORDS = {"0", "取消", "退出"}
RESTART_MANAGED_WORDS = {"1", "有", "是"}
RESTART_SELF_WORDS = {"2", "没有", "无", "否"}

logger.info("BOT 重启命令已加载，可由超级用户发送 @机器人 重启")


@dataclass(frozen=True)
class PendingRestartNotice:
    request_id: str
    bot_id: str
    target_type: str
    target_id: str
    mode: str
    requested_at: int


def _restart_notice_path(bot_id: str | int) -> Path:
    safe_bot_id = re.sub(r"[^0-9A-Za-z_.-]", "_", str(bot_id)) or "unknown"
    return admin_path.config_path / f"bot_restart_pending_{safe_bot_id}.json"


def _read_pending_restart_notice(bot_id: str | int) -> PendingRestartNotice | None:
    path = _restart_notice_path(bot_id)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        pending = PendingRestartNotice(
            request_id=str(raw["request_id"]),
            bot_id=str(raw["bot_id"]),
            target_type=str(raw["target_type"]),
            target_id=str(raw["target_id"]),
            mode=str(raw["mode"]),
            requested_at=int(raw["requested_at"]),
        )
    except FileNotFoundError:
        return None
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as err:
        logger.warning(f"BOT 重启通知状态读取失败，将忽略该状态：{type(err).__name__}: {err}")
        return None

    if pending.bot_id != str(bot_id) or pending.target_type not in {"group", "private"} or not pending.target_id:
        logger.warning("BOT 重启通知状态无效，将忽略该状态")
        return None
    if pending.requested_at < int(time.time()) - RESTART_NOTICE_TTL_SECONDS:
        _clear_pending_restart_notice(pending)
        logger.warning("BOT 重启通知状态已过期，已清理")
        return None
    return pending


def _write_pending_restart_notice(pending: PendingRestartNotice) -> bool:
    path = _restart_notice_path(pending.bot_id)
    temporary_path = path.with_name(f".{path.name}.{pending.request_id}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path.write_text(json.dumps(asdict(pending), ensure_ascii=False), encoding="utf-8")
        os.replace(temporary_path, path)
        return True
    except OSError as err:
        logger.error(f"BOT 重启通知状态写入失败：{type(err).__name__}: {err}")
        temporary_path.unlink(missing_ok=True)
        return False


def _clear_pending_restart_notice(pending: PendingRestartNotice) -> None:
    path = _restart_notice_path(pending.bot_id)
    current = _read_pending_restart_notice_unchecked(pending.bot_id)
    if current is not None and current.request_id != pending.request_id:
        return
    path.unlink(missing_ok=True)


def _read_pending_restart_notice_unchecked(bot_id: str | int) -> PendingRestartNotice | None:
    path = _restart_notice_path(bot_id)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return PendingRestartNotice(
            request_id=str(raw["request_id"]),
            bot_id=str(raw["bot_id"]),
            target_type=str(raw["target_type"]),
            target_id=str(raw["target_id"]),
            mode=str(raw["mode"]),
            requested_at=int(raw["requested_at"]),
        )
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def prepare_restart_notice(bot_id: str | int, event: Event, mode: str) -> PendingRestartNotice | None:
    if mode not in {"managed", "self"}:
        return None

    group_id = getattr(event, "group_id", None)
    user_id = getattr(event, "user_id", None)
    if group_id is not None:
        target_type, target_id = "group", str(group_id)
    elif user_id is not None:
        target_type, target_id = "private", str(user_id)
    else:
        return None

    pending = PendingRestartNotice(
        request_id=uuid.uuid4().hex,
        bot_id=str(bot_id),
        target_type=target_type,
        target_id=target_id,
        mode=mode,
        requested_at=int(time.time()),
    )
    return pending if _write_pending_restart_notice(pending) else None


def is_restart_superuser(bot: Bot, event: Event) -> bool:
    try:
        user_id = str(event.get_user_id())
    except Exception:
        return False
    superusers = {str(item) for item in (getattr(get_driver().config, "superusers", set()) or set())}
    adapter_name = str(getattr(getattr(bot, "adapter", None), "get_name", lambda: "")()).split(maxsplit=1)[0].lower()
    return user_id in superusers or f"{adapter_name}:{user_id}" in superusers


def _normalize_restart_command(value: object) -> str:
    text = str(value or "").casefold()
    return "".join(char for char in text if not char.isspace() and char not in {"\u200b", "\ufeff"})


def _configured_bot_nicknames() -> tuple[str, ...]:
    nicknames = getattr(get_driver().config, "nickname", ()) or ()
    if isinstance(nicknames, str):
        nicknames = (nicknames,)
    try:
        return tuple(str(nickname) for nickname in nicknames if str(nickname).strip())
    except TypeError:
        return ()


async def _restart_command_rule(event: Event) -> bool:
    try:
        plain_text = event.get_plaintext()
    except Exception:
        plain_text = getattr(event, "raw_message", "")
    command = _normalize_restart_command(plain_text)

    if command == "重启" and bool(getattr(event, "to_me", False)):
        return True

    raw_command = _normalize_restart_command(getattr(event, "raw_message", ""))
    return any(raw_command == f"{_normalize_restart_command(nickname)}重启" for nickname in _configured_bot_nicknames())


async def notify_pending_restart(bot: Bot) -> bool:
    pending = _read_pending_restart_notice(bot.self_id)
    if pending is None:
        return False

    try:
        if pending.target_type == "group":
            await bot.send_group_msg(group_id=int(pending.target_id), message="BOT 重启完成。")
        else:
            await bot.send_private_msg(user_id=int(pending.target_id), message="BOT 重启完成。")
    except Exception as err:
        logger.warning(f"BOT 重启完成通知发送失败，将在下次连接时重试：{type(err).__name__}: {err}")
        return False

    _clear_pending_restart_notice(pending)
    await record_oplog(
        action="bot_restart",
        detail=f"Bot [{bot.self_id}] 重启完成",
        extra={"bot_id": str(bot.self_id), "mode": pending.mode},
    )
    logger.success(f"Bot [{bot.self_id}] 重启完成通知已发送")
    return True


async def _send_restart_failure(bot: Bot, pending: PendingRestartNotice) -> None:
    try:
        if pending.target_type == "group":
            await bot.send_group_msg(group_id=int(pending.target_id), message="BOT 重启失败，请查看控制台日志。")
        else:
            await bot.send_private_msg(user_id=int(pending.target_id), message="BOT 重启失败，请查看控制台日志。")
    except Exception as err:
        logger.warning(f"BOT 重启失败通知发送失败：{type(err).__name__}: {err}")


async def _restart_after_response(bot: Bot, pending: PendingRestartNotice) -> None:
    await asyncio.sleep(RESTART_PREPARE_DELAY_SECONDS)
    try:
        if pending.mode == "managed":
            logger.warning(f"Bot [{bot.self_id}] 正在退出，等待进程守护工具重新拉起")
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            os.kill(os.getpid(), signal.SIGTERM)
            return

        logger.warning(f"Bot [{bot.self_id}] 正在自行重启")
        os.execv(sys.executable, [sys.executable, *sys.argv])
    except Exception as err:
        _clear_pending_restart_notice(pending)
        logger.exception(f"BOT 重启失败：{type(err).__name__}: {err}")
        await _send_restart_failure(bot, pending)


bot_restart = on_message(
    rule=Rule(_restart_command_rule),
    priority=1,
    block=True,
)


@bot_restart.handle()
async def _(bot: Bot, event: Event, matcher: Matcher, state: T_State):
    if not is_restart_superuser(bot, event):
        logger.warning(f"已忽略非超级用户发起的 BOT 重启请求：{getattr(event, 'user_id', 'unknown')}")
        await matcher.finish()
    if _read_pending_restart_notice(bot.self_id) is not None:
        await matcher.finish("已有重启任务正在等待 BOT 重新连接，请稍后。")

    state["restart_requested"] = True
    await matcher.send(
        "BOT 是否有进程守护类工具？\n"
        "回复【有】仅停止当前 BOT，由守护工具重新拉起。\n"
        "回复【没有】由 BOT 自行重启。\n"
        "回复【取消】终止本次操作。"
    )
    await matcher.pause()


@bot_restart.handle()
async def _(bot: Bot, event: Event, matcher: Matcher, state: T_State):
    if not state.get("restart_requested"):
        return

    reply = event.get_plaintext().strip().casefold()
    if reply in RESTART_CANCEL_WORDS:
        await matcher.finish("已取消 BOT 重启。")
    if reply in RESTART_MANAGED_WORDS:
        mode = "managed"
    elif reply in RESTART_SELF_WORDS:
        mode = "self"
    else:
        await matcher.reject("请回复【有】、【没有】或【取消】。")
        return

    pending = prepare_restart_notice(bot.self_id, event, mode)
    if pending is None:
        await matcher.finish("无法记录重启完成通知，已取消本次重启。")

    await record_oplog(
        action="bot_restart",
        group_id=getattr(event, "group_id", None),
        user_id=getattr(event, "user_id", None),
        detail="超级用户请求重启，等待进程守护工具拉起" if mode == "managed" else "超级用户请求 BOT 自行重启",
        extra={"bot_id": str(bot.self_id), "mode": mode},
    )
    await matcher.send("准备重启...")
    asyncio.create_task(_restart_after_response(bot, pending))
    await matcher.finish()
