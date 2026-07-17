# python3
# -*- coding: utf-8 -*-

import datetime
from html import escape
from pathlib import Path

from nonebot import get_driver, logger, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import ArgStr
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from ..core.exact_command import exact_command
from ..core.html_snapshot import render_html_card_to_image
from .member_cleanup_flow import (
    GROUP_LEVEL_KEYS,
    QQ_LEVEL_KEYS,
    build_category_prompt,
    build_zero_level_notice,
    execute_member_cleanup,
    extract_member_last_sent_times,
    extract_member_levels,
    filter_members_by_last_sent,
    filter_members_by_level,
    get_member_info_map,
    get_targetable_member_ids,
    parse_cleanup_date,
    parse_cleanup_exclusions,
    should_abort_for_remaining,
    should_cancel,
)
from .member_cleanup_lock import clear_cleanup_lock, ensure_cleanup_lock, get_cleanup_lock_path
from .member_cleanup_text import (
    CLEANUP_CANCELLED_TEXT,
    CLEANUP_CATEGORY_PROMPT,
    CLEANUP_CONFIRM_INVALID_TEXT,
    CLEANUP_CONFIRM_PROMPT,
    CLEANUP_DATE_FUTURE_TEXT,
    CLEANUP_DATE_INVALID_TEXT,
    CLEANUP_EXECUTING_TEXT,
    CLEANUP_EXECUTING_WITH_RANDOM_TEXT,
    CLEANUP_FAIL_TEXT,
    CLEANUP_INVALID_CATEGORY_TEXT,
    CLEANUP_LEVEL_INVALID_TEXT,
    CLEANUP_LIMIT_INVALID_TEXT,
    CLEANUP_LIMIT_PROMPT,
    CLEANUP_LIMIT_UNAVAILABLE_TEXT,
    CLEANUP_LOCK_EXISTS_TEXT,
    CLEANUP_NO_MEMBER_TEXT,
    CLEANUP_NO_TASK_TEXT,
    CLEANUP_NOTICE_MESSAGE_EMPTY_TEXT,
    CLEANUP_NOTICE_MESSAGE_PROMPT,
    CLEANUP_NOTICE_MODE_INVALID_TEXT,
    CLEANUP_NOTICE_MODE_PROMPT,
    CLEANUP_QUERYING_TEXT,
    CLEANUP_REMAINING_TOO_LOW_TEXT,
    CLEANUP_SUCCESS_TEXT,
    CLEANUP_UNLOCK_SUCCESS_TEXT,
)
from ..core.path import kick_lock_path, re_img_path


async def finish_matcher(matcher: Matcher, state: T_State, arg: str):
    """
    处理 finish_matcher 的业务逻辑
    :param matcher: Matcher 实例
    :param state: 状态字典
    :param arg: 参数值
    :return: None
    """
    if should_cancel(arg):
        clear_cleanup_lock(state["this_lock"])
        await matcher.finish(CLEANUP_CANCELLED_TEXT)


def _load_superusers() -> set[str]:
    return {str(user_id) for user_id in (getattr(get_driver().config, "superusers", set()) or set())}


def _limit_invalid_prompt(bound: int) -> str:
    if bound <= 1:
        return CLEANUP_LIMIT_UNAVAILABLE_TEXT
    return CLEANUP_LIMIT_INVALID_TEXT.format(bound=bound)


def _avatar_url(user_id: int) -> str:
    return f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"


def _display_name(info: dict, user_id: int) -> str:
    return str(info.get("card") or info.get("nickname") or user_id)


def _title_badge_class(role: str) -> str:
    return {
        "owner": "owner",
        "admin": "admin",
    }.get(role, "member")


def _display_title(info: dict) -> str:
    title = str(info.get("title") or "").strip()
    if title:
        return title
    role = str(info.get("role") or "member")
    if role == "owner":
        return "群主"
    if role == "admin":
        return "管理员"
    return ""


def _best_role(*roles: object) -> str:
    role_set = {str(role or "") for role in roles}
    if "owner" in role_set:
        return "owner"
    if "admin" in role_set:
        return "admin"
    return "member"


def _notice_text(mode: str) -> str:
    return {
        "1": "会发送@全体成员消息",
        "2": "会在群内@被清理成员",
        "3": "会向被清理成员发送私聊消息",
    }.get(mode, "不会发送清理前通知消息")


def _build_confirm_prompt(mode: str) -> str:
    return CLEANUP_CONFIRM_PROMPT.format(notice_text=_notice_text(mode))


def _build_cleanup_members_html(kick_list: list[int], member_infos: dict[int, dict]) -> str:
    cards = []
    for index, user_id in enumerate(kick_list, start=1):
        info = member_infos.get(user_id, {})
        name = escape(_display_name(info, user_id))
        uid = escape(str(user_id))
        avatar = escape(_avatar_url(user_id))
        level = escape(str(info.get("level") or "0"))
        title = _display_title(info)
        badge = ""
        if title:
            role_class = _title_badge_class(str(info.get("role") or "member"))
            badge = f'<div class="badge {role_class}">LV{level} {escape(title)}</div>'
        cards.append(
            f"""
            <div class="member-card">
              <div class="seq">{index}</div>
              <img class="avatar" src="{avatar}" />
              <div class="meta">
                {badge}
                <div class="name">{name}</div>
                <div class="uid">{uid}</div>
              </div>
            </div>
            """
        )

    return f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #f4f7fb;
      font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
      color: #172033;
    }}
    .page {{
      width: 2200px;
      padding: 36px;
    }}
    .title {{
      font-size: 34px;
      font-weight: 800;
      margin-bottom: 8px;
    }}
    .subtitle {{
      color: #657089;
      font-size: 20px;
      margin-bottom: 24px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
      gap: 16px;
    }}
    .member-card {{
      display: grid;
      grid-template-columns: 42px 64px minmax(0, 1fr);
      align-items: center;
      gap: 12px;
      min-height: 88px;
      padding: 12px;
      border-radius: 8px;
      background: #ffffff;
      border: 1px solid #dfe6f2;
    }}
    .seq {{
      width: 34px;
      height: 34px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #1e66f5;
      color: white;
      font-size: 18px;
      font-weight: 700;
    }}
    .avatar {{
      width: 64px;
      height: 64px;
      border-radius: 50%;
      object-fit: cover;
      background: #e8edf5;
    }}
    .meta {{ min-width: 0; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      max-width: 100%;
      min-height: 28px;
      padding: 2px 9px;
      margin-bottom: 6px;
      border-radius: 7px;
      font-size: 16px;
      font-weight: 700;
      line-height: 1.2;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .badge.owner {{
      color: #b15c00;
      background: #ffe8bd;
    }}
    .badge.admin {{
      color: #07806d;
      background: #c9f4ea;
    }}
    .badge.member {{
      color: #9a4bc9;
      background: #f0d5ff;
    }}
    .name {{
      font-size: 20px;
      font-weight: 700;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .uid {{
      margin-top: 6px;
      font-size: 15px;
      color: #69758d;
    }}
  </style>
</head>
<body>
  <div class="page">
    <div class="title">成员清理确认名单</div>
    <div class="subtitle">共 {len(kick_list)} 名成员</div>
    <div class="grid">
      {''.join(cards)}
    </div>
  </div>
</body>
</html>
"""


async def _send_cleanup_members_image(event: GroupMessageEvent, kick_list: list[int], member_infos: dict[int, dict]) -> None:
    rows = max(1, (len(kick_list) + 7) // 8)
    viewport_height = min(max(520, 150 + rows * 116), 12000)
    html = _build_cleanup_members_html(kick_list, member_infos)
    img_path = (re_img_path / f"member_cleanup_{event.group_id}.png").resolve()
    img_bytes = await render_html_card_to_image(
        html,
        img_path,
        viewport_width=2200,
        viewport_height=viewport_height,
        wait_ms=800,
    )
    await kick_by_rule.send(MessageSegment.image(img_bytes))


def _merge_member_list_infos(member_list: list[dict], member_infos: dict[int, dict]) -> dict[int, dict]:
    merged = {user_id: dict(info) for user_id, info in member_infos.items()}
    for member in member_list:
        user_id = member.get("user_id")
        if user_id is None:
            continue
        user_id = int(user_id)
        info = merged.setdefault(user_id, {})
        for key in ("nickname", "card", "level", "title"):
            if not info.get(key) and member.get(key):
                info[key] = member[key]
        info["role"] = _best_role(member.get("role"), info.get("role"))
    return merged


def _pick_member_preview_ids(member_list: list[dict], member_infos: dict[int, dict], limit: int = 50) -> list[int]:
    selected: list[int] = []
    selected_set: set[int] = set()

    def add(user_id: int) -> None:
        if len(selected) < limit and user_id not in selected_set:
            selected.append(user_id)
            selected_set.add(user_id)

    user_ids = [int(member["user_id"]) for member in member_list if "user_id" in member]
    for user_id in user_ids:
        if str(member_infos.get(user_id, {}).get("role") or "") == "owner":
            add(user_id)
    for user_id in user_ids:
        if str(member_infos.get(user_id, {}).get("role") or "") == "admin":
            add(user_id)
    for user_id in user_ids:
        if str(member_infos.get(user_id, {}).get("title") or "").strip():
            add(user_id)
    for user_id in user_ids:
        if not str(member_infos.get(user_id, {}).get("title") or "").strip():
            add(user_id)
    return selected


async def _prepare_cleanup_preview(bot: Bot, event: GroupMessageEvent, state: T_State) -> None:
    await kick_by_rule.send(CLEANUP_QUERYING_TEXT)
    category = str(state["k_category"])
    qq_list = state["qq_list"]

    async def report_progress(done: int, total: int) -> None:
        await kick_by_rule.send(f"持续查询消息中... 已查询 {done}/{total}")

    member_infos = await get_member_info_map(
        bot,
        event.group_id,
        qq_list,
        progress_callback=report_progress,
        progress_interval=20.0,
    )

    if category in ("1", "2"):
        threshold = int(state["cleanup_threshold"])
        level_keys = GROUP_LEVEL_KEYS if category == "1" else QQ_LEVEL_KEYS
        level_name = "群聊等级" if category == "1" else "QQ等级"
        level_map = extract_member_levels(member_infos, qq_list, level_keys=level_keys, level_name=level_name)
        kick_list, zero_level_list = filter_members_by_level(level_map, threshold, include_zero=category == "1")
        zero_level_notice = build_zero_level_notice(zero_level_list)
        if zero_level_notice:
            await kick_by_rule.send(zero_level_notice)
    elif category == "3":
        last_sent_map = extract_member_last_sent_times(member_infos)
        logger.debug(f"last_send_list: {last_sent_map}")
        input_time = state["cleanup_input_time"]
        kick_list = filter_members_by_last_sent(last_sent_map, input_time)
    else:
        await kick_by_rule.reject(CLEANUP_INVALID_CATEGORY_TEXT)

    cleanup_limit = int(state.get("cleanup_limit") or 0)
    if cleanup_limit:
        kick_list = kick_list[:cleanup_limit]

    if not kick_list:
        clear_cleanup_lock(state["this_lock"])
        await kick_by_rule.finish(CLEANUP_NO_MEMBER_TEXT)

    state["kick_list"] = kick_list
    state["kick_member_infos"] = {user_id: member_infos.get(user_id, {}) for user_id in kick_list}
    logger.debug(f"kick_list: {kick_list}")
    if should_abort_for_remaining(len(state["member_list"]), len(kick_list)):
        clear_cleanup_lock(state["this_lock"])
        await kick_by_rule.finish(CLEANUP_REMAINING_TOO_LOW_TEXT)

    try:
        await _send_cleanup_members_image(event, kick_list, state["kick_member_infos"])
    except Exception as err:
        logger.warning(f"成员清理预览图渲染失败，使用文字预览: {type(err).__name__}: {err}")
        fallback = "\n".join(f"{index}. {_display_name(state['kick_member_infos'].get(user_id, {}), user_id)}({user_id})" for index, user_id in enumerate(kick_list, start=1))
        await kick_by_rule.send(f"本次即将清理的成员：\n{fallback}")
    await kick_by_rule.send(_build_confirm_prompt(str(state.get("cleanup_notice_mode") or "4")))


async def _send_cleanup_notice(bot: Bot, group_id: int, kick_list: list[int], mode: str, message: str) -> None:
    if mode == "1":
        await bot.send_group_msg(
            group_id=group_id,
            message=Message([MessageSegment.at("all"), MessageSegment.text(f"\n{message}")]),
        )
        return

    if mode == "2":
        group_message = Message()
        for user_id in kick_list:
            group_message += MessageSegment.at(user_id)
        group_message += MessageSegment.text(f"\n{message}")
        await bot.send_group_msg(group_id=group_id, message=group_message)
        return

    if mode == "3":
        failed: list[int] = []
        for user_id in kick_list:
            try:
                await bot.send_private_msg(user_id=user_id, message=message)
            except ActionFailed:
                failed.append(user_id)
        if failed:
            await kick_by_rule.send(f"私聊通知发送失败：{failed}")
        if failed and len(failed) == len(kick_list):
            await kick_by_rule.send("私聊通知全部发送失败，改为群内@通知。")
            await _send_cleanup_notice(bot, group_id, kick_list, "2", message)


kick_by_rule = on_command("成员清理", priority=2, rule=exact_command("成员清理"), block=True, permission=SUPERUSER | GROUP_OWNER)


@kick_by_rule.got("k_category", prompt=CLEANUP_CATEGORY_PROMPT)
async def _(
    event: GroupMessageEvent,
    matcher: Matcher,
    state: T_State,
    k_category=ArgStr(),
):
    this_lock: Path = get_cleanup_lock_path(kick_lock_path, event.group_id)
    state["this_lock"] = this_lock
    if not ensure_cleanup_lock(this_lock):
        await kick_by_rule.finish(CLEANUP_LOCK_EXISTS_TEXT)

    category = str(k_category)
    await finish_matcher(matcher, state, category)

    prompt = build_category_prompt(category)
    if prompt:
        await kick_by_rule.send(prompt)
    else:
        await kick_by_rule.reject(CLEANUP_INVALID_CATEGORY_TEXT)


@kick_by_rule.got("kick_condition", prompt="请输入:")
async def _(
    bot: Bot,
    event: GroupMessageEvent,
    matcher: Matcher,
    state: T_State,
    kick_condition=ArgStr(),
):
    kick_condition = str(kick_condition)
    await finish_matcher(matcher, state, kick_condition)
    category = str(state["k_category"])

    if category in ("1", "2"):
        try:
            state["cleanup_threshold"] = int(kick_condition)
        except ValueError:
            await kick_by_rule.reject(CLEANUP_LEVEL_INVALID_TEXT)
    elif category == "3":
        try:
            input_time = parse_cleanup_date(kick_condition)
            if input_time > datetime.datetime.now():
                await kick_by_rule.reject(CLEANUP_DATE_FUTURE_TEXT)
        except ValueError:
            await kick_by_rule.reject(CLEANUP_DATE_INVALID_TEXT)
        state["cleanup_input_time"] = input_time
    else:
        await kick_by_rule.reject(CLEANUP_INVALID_CATEGORY_TEXT)

    try:
        member_list = await bot.get_group_member_list(group_id=event.group_id, no_cache=True)
    except ActionFailed as err:
        clear_cleanup_lock(state["this_lock"])
        await kick_by_rule.finish(f"获取群成员列表失败：{err}")
    except Exception as err:
        clear_cleanup_lock(state["this_lock"])
        await kick_by_rule.finish(f"获取群成员列表异常：{type(err).__name__}: {err}")

    qq_list = get_targetable_member_ids(member_list, bot.self_id, _load_superusers())
    if not qq_list:
        clear_cleanup_lock(state["this_lock"])
        await kick_by_rule.finish(CLEANUP_NO_MEMBER_TEXT)

    state["member_list"] = member_list
    state["qq_list"] = qq_list
    state["cleanup_limit_bound"] = len(qq_list)


@kick_by_rule.got("cleanup_limit", prompt=CLEANUP_LIMIT_PROMPT)
async def _(matcher: Matcher, state: T_State, cleanup_limit=ArgStr()):
    limit_text = str(cleanup_limit).strip()
    await finish_matcher(matcher, state, limit_text)

    if limit_text in {"0", "否", "不", "不指定", "否，不"}:
        state["cleanup_limit"] = 0
        return

    if not limit_text.isdigit():
        await kick_by_rule.reject(_limit_invalid_prompt(int(state["cleanup_limit_bound"])))

    limit = int(limit_text)
    bound = int(state["cleanup_limit_bound"])
    if limit <= 0 or limit >= bound:
        await kick_by_rule.reject(_limit_invalid_prompt(bound))
    state["cleanup_limit"] = limit


@kick_by_rule.got("cleanup_notice_mode", prompt=CLEANUP_NOTICE_MODE_PROMPT)
async def _(matcher: Matcher, state: T_State, cleanup_notice_mode=ArgStr()):
    mode = str(cleanup_notice_mode).strip()
    await finish_matcher(matcher, state, mode)

    if mode not in {"1", "2", "3", "4"}:
        await kick_by_rule.reject(CLEANUP_NOTICE_MODE_INVALID_TEXT)

    state["cleanup_notice_mode"] = mode
    if mode == "4":
        state["cleanup_notice_message"] = ""
        matcher.set_arg("cleanup_notice_message", Message(""))


@kick_by_rule.got("cleanup_notice_message", prompt=CLEANUP_NOTICE_MESSAGE_PROMPT)
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher, state: T_State, cleanup_notice_message=ArgStr()):
    if str(state.get("cleanup_notice_mode") or "4") != "4":
        message = str(cleanup_notice_message)
        await finish_matcher(matcher, state, message.strip())
        if not message.strip():
            await kick_by_rule.reject(CLEANUP_NOTICE_MESSAGE_EMPTY_TEXT)
        state["cleanup_notice_message"] = message

    await _prepare_cleanup_preview(bot, event, state)


@kick_by_rule.got("confirm")
async def _(matcher: Matcher, state: T_State):
    confirm = str(state["confirm"]).strip()
    await finish_matcher(matcher, state, confirm)
    kick_list = list(state["kick_list"])
    exclusions = parse_cleanup_exclusions(confirm, len(kick_list))
    if exclusions is None:
        await kick_by_rule.reject(CLEANUP_CONFIRM_INVALID_TEXT)

    if exclusions:
        excluded_ids = {kick_list[index - 1] for index in exclusions}
        state["kick_list"] = [user_id for user_id in kick_list if user_id not in excluded_ids]
        await kick_by_rule.send(f"已排除：{sorted(excluded_ids)}")
        if not state["kick_list"]:
            clear_cleanup_lock(state["this_lock"])
            await kick_by_rule.finish(CLEANUP_NO_MEMBER_TEXT)
    await kick_by_rule.send(CLEANUP_EXECUTING_TEXT)


@kick_by_rule.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    kick_list = state["kick_list"]
    if not kick_list:
        clear_cleanup_lock(state["this_lock"])
        await kick_by_rule.send(CLEANUP_NO_MEMBER_TEXT)
        return

    notice_mode = str(state.get("cleanup_notice_mode") or "4")
    notice_message = str(state.get("cleanup_notice_message") or "")
    if notice_mode in {"1", "2"} and notice_message.strip():
        try:
            await _send_cleanup_notice(bot, event.group_id, kick_list, notice_mode, notice_message)
        except ActionFailed as err:
            await kick_by_rule.send(f"清理前通知发送失败：{err}，继续执行清理...")
        except Exception as err:
            await kick_by_rule.send(f"清理前通知发送异常：{type(err).__name__}: {err}，继续执行清理...")

    await kick_by_rule.send(CLEANUP_EXECUTING_WITH_RANDOM_TEXT)
    success, fail = await execute_member_cleanup(
        bot,
        event.group_id,
        event.user_id,
        kick_list,
    )
    if success:
        await kick_by_rule.send(CLEANUP_SUCCESS_TEXT.format(success=success))
    if fail:
        await kick_by_rule.send(CLEANUP_FAIL_TEXT.format(fail=fail))

    clear_cleanup_lock(state["this_lock"])


delete_lock_manually = on_command("清理解锁", priority=2, rule=exact_command("清理解锁"), block=True, permission=SUPERUSER | GROUP_OWNER)


@delete_lock_manually.handle()
async def _(event: GroupMessageEvent):
    this_lock: Path = get_cleanup_lock_path(kick_lock_path, event.group_id)
    if this_lock.exists():
        clear_cleanup_lock(this_lock)
        await delete_lock_manually.finish(CLEANUP_UNLOCK_SUCCESS_TEXT)
    else:
        await delete_lock_manually.finish(CLEANUP_NO_TASK_TEXT)


member_info_test = on_command("/7.8测试", priority=2, block=True, permission=SUPERUSER | GROUP_OWNER)


@member_info_test.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    try:
        member_list = await bot.get_group_member_list(group_id=event.group_id, no_cache=True)
        user_ids = [int(member["user_id"]) for member in member_list if "user_id" in member]
        member_infos = await get_member_info_map(bot, event.group_id, user_ids)
        member_infos = _merge_member_list_infos(member_list, member_infos)
        preview_ids = _pick_member_preview_ids(member_list, member_infos, limit=50)
        if not preview_ids:
            await member_info_test.finish("没有可渲染的成员")
        await _send_cleanup_members_image(event, preview_ids, member_infos)
    except ActionFailed as err:
        logger.info(f"/7.8测试 渲染成员测试图片失败 group_id={event.group_id}: {err}")
        await member_info_test.finish(f"测试图片生成失败：{err}")
    except Exception as err:
        logger.info(f"/7.8测试 渲染成员测试图片异常 group_id={event.group_id}: {type(err).__name__}: {err}")
        await member_info_test.finish(f"测试图片生成异常：{type(err).__name__}: {err}")

    await member_info_test.finish("测试图片已经发送")
