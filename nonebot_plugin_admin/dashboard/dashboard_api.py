from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional

import nonebot
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from ..core.config import plugin_config
from ..statistics.statistics_read_service import load_group_wordcloud_source
from ..statistics.wordcloud_generate_flow import render_wordcloud_image
from .dashboard_live_service import (
    broadcast_message_action,
    build_account_overview_payload,
    build_group_announcements_payload,
    build_group_profile_payload,
    build_group_essence_payload,
    build_group_files_payload,
    build_group_honors_payload,
    build_group_members_payload,
    build_group_messages_payload,
    build_recent_contacts_payload,
    fetch_group_bot_profile,
    kick_group_member_action,
    mark_group_msg_as_read_action,
    mute_group_member_action,
    send_group_message_action,
    set_group_feature_switch_action,
    set_group_special_title_action,
    set_group_whole_ban_action,
)
from .dashboard_log_service import build_logs_overview_payload, build_logs_payload
from .dashboard_oplog_service import build_oplog_overview_payload, build_oplog_payload
from .dashboard_service import (
    build_approval_overview_payload,
    build_basic_group_admin_overview_payload,
    build_broadcast_overview_payload,
    build_content_guard_overview_payload,
    build_dashboard_catalog_payload,
    build_dashboard_overview_payload,
    build_event_notice_overview_payload,
    build_group_approval_payload,
    build_group_basic_admin_payload,
    build_group_broadcast_payload,
    build_group_content_guard_payload,
    build_group_detail_payload,
    build_group_event_notice_payload,
    build_group_feature_switches_payload,
    build_group_member_cleanup_payload,
    build_group_statistics_payload,
    build_member_cleanup_overview_payload,
    build_operations_overview_payload,
    build_runtime_overview_payload,
    build_statistics_overview_payload,
    build_switcher_overview_payload,
    collect_dashboard_group_ids_live,
    list_group_summaries_payload,
    normalize_group_id,
    resolve_wordcloud_output_path,
)


class DashboardSendMessageRequest(BaseModel):
    message: str


class DashboardMuteRequest(BaseModel):
    user_id: str
    duration: int = 600


class DashboardKickRequest(BaseModel):
    user_id: str
    reject_add_request: bool = False


class DashboardSpecialTitleRequest(BaseModel):
    user_id: str
    special_title: str = ""


class DashboardFeatureSwitchRequest(BaseModel):
    enabled: bool


class DashboardWholeBanRequest(BaseModel):
    enabled: bool


class DashboardBroadcastRequest(BaseModel):
    message: str
    include_group_ids: Optional[List[str]] = None
    exclude_group_ids: List[str] = Field(default_factory=list)


class DashboardWorkspaceRequest(BaseModel):
    message_limit: int = 40
    member_page_size: int = 20


def verify_dashboard_token(x_admin_token: Optional[str] = Header(default=None)) -> None:
    """
    处理 verify_dashboard_token 的业务逻辑
    :param x_admin_token: x_admin_token 参数
    :return: None
    """
    token = plugin_config.dashboard_api_token.strip()
    if token and x_admin_token != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid dashboard token.",
        )


def create_dashboard_api_router(base_path: str) -> APIRouter:
    """
    创建面板apirouter
    :param base_path: 路径对象
    :return: APIRouter
    """
    router = APIRouter(prefix=f"{base_path}/api", tags=["admin-dashboard"])
    frontend_enabled = plugin_config.dashboard_frontend_enabled
    dashboard_mode = "integrated_web" if frontend_enabled else "api_only"

    async def ensure_group_exists(group_id: str) -> str:
        """
        确保群exists
        :param group_id: 群号
        :return: str
        """
        normalized_group_id = normalize_group_id(group_id)
        if normalized_group_id not in await collect_dashboard_group_ids_live():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
        return normalized_group_id

    @router.get("/meta")
    async def get_dashboard_meta():
        """
        获取面板meta
        :return: None
        """
        return {
            "title": plugin_config.dashboard_title,
            "base_path": base_path,
            "auth_required": bool(plugin_config.dashboard_api_token.strip()),
            "orm_enabled": plugin_config.statistics_orm_enabled,
            "mode": dashboard_mode,
            "frontend_enabled": frontend_enabled,
            "frontend_path": base_path if frontend_enabled else None,
            "overview_keys": [
                "dashboard",
                "operations",
                "logs",
                "statistics",
                "approval",
                "broadcast",
                "basic_group_admin",
                "content_guard",
                "member_cleanup",
                "event_notice",
                "switcher",
                "runtime",
                "account",
                "recent_contacts",
            ],
            "group_section_keys": [
                "statistics",
                "messages",
                "members",
                "feature_switches",
                "approval",
                "broadcast",
                "basic_group_admin",
                "content_guard",
                "member_cleanup",
                "event_notice",
                "announcements",
                "essence",
                "honors",
                "files",
            ],
        }

    @router.get("/catalog")
    async def get_dashboard_catalog():
        """
        获取面板catalog
        :return: None
        """
        return build_dashboard_catalog_payload(base_path)

    @router.get("/auth/session", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_session():
        """
        获取面板session
        :return: None
        """
        return {
            "title": plugin_config.dashboard_title,
            "base_path": base_path,
            "frontend_enabled": frontend_enabled,
            "auth_required": bool(plugin_config.dashboard_api_token.strip()),
            "bot_count": len(nonebot.get_bots()),
        }

    @router.get("/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_overview():
        """
        获取面板overview
        :return: None
        """
        return await build_dashboard_overview_payload()

    @router.get("/operations/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_operations_overview():
        """
        获取operationsoverview
        :return: None
        """
        return await build_operations_overview_payload()

    @router.get("/logs/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_logs_overview():
        """
        获取logsoverview
        :return: None
        """
        return await build_logs_overview_payload()

    @router.get("/logs", dependencies=[Depends(verify_dashboard_token)])
    async def get_logs(
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=50, ge=1, le=200),
        level: str = Query(default=""),
        keyword: str = Query(default=""),
        source: str = Query(default=""),
    ):
        """
        获取logs
        :param page: 页码
        :param page_size: 分页大小
        :param level: level 参数
        :param keyword: 关键字
        :param source: source 参数
        :return: None
        """
        return await build_logs_payload(
            page=page,
            page_size=page_size,
            level=level,
            keyword=keyword,
            source=source,
        )

    @router.get("/oplog/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_oplog_overview():
        """
        获取操作日志overview
        :return: None
        """
        return await build_oplog_overview_payload()

    @router.get("/oplog", dependencies=[Depends(verify_dashboard_token)])
    async def get_oplog(
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=50, ge=1, le=200),
        action: str = Query(default=""),
        group_id: str = Query(default=""),
        level: str = Query(default=""),
        keyword: str = Query(default=""),
    ):
        """
        获取操作日志
        :param page: 页码
        :param page_size: 分页大小
        :param action: action 参数
        :param group_id: 群号
        :param level: level 参数
        :param keyword: 关键字
        :return: None
        """
        return await build_oplog_payload(
            page=page,
            page_size=page_size,
            action=action,
            group_id=group_id,
            level=level,
            keyword=keyword,
        )

    @router.get("/statistics/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_statistics_overview():
        """
        获取statisticsoverview
        :return: None
        """
        return await build_statistics_overview_payload()

    @router.get("/approval/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_approval_overview():
        """
        获取审批overview
        :return: None
        """
        return await build_approval_overview_payload()

    @router.get("/broadcast/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_broadcast_overview():
        """
        获取broadcastoverview
        :return: None
        """
        return await build_broadcast_overview_payload()

    @router.get("/basic-group-admin/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_basic_group_admin_overview():
        """
        获取basic群管理员overview
        :return: None
        """
        return await build_basic_group_admin_overview_payload()

    @router.get("/content-guard/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_content_guard_overview():
        """
        获取内容审核overview
        :return: None
        """
        return await build_content_guard_overview_payload()

    @router.get("/member-cleanup/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_member_cleanup_overview():
        """
        获取成员清理overview
        :return: None
        """
        return await build_member_cleanup_overview_payload()

    @router.get("/event-notice/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_event_notice_overview():
        """
        获取event通知overview
        :return: None
        """
        return await build_event_notice_overview_payload()

    @router.get("/switcher/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_switcher_overview():
        """
        获取开关overview
        :return: None
        """
        return await build_switcher_overview_payload()

    @router.get("/runtime/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_runtime_overview():
        """
        获取运行时overview
        :return: None
        """
        return build_runtime_overview_payload(base_path)

    @router.get("/account/overview", dependencies=[Depends(verify_dashboard_token)])
    async def get_account_overview():
        """
        获取accountoverview
        :return: None
        """
        return await build_account_overview_payload()

    @router.get("/contacts/recent", dependencies=[Depends(verify_dashboard_token)])
    async def get_recent_contacts(count: int = Query(default=12, ge=1, le=100)):
        """
        获取recentcontacts
        :param count: count 参数
        :return: None
        """
        return await build_recent_contacts_payload(count=count)

    @router.get("/groups", dependencies=[Depends(verify_dashboard_token)])
    async def list_dashboard_groups():
        """
        列出面板群组
        :return: None
        """
        return {
            "items": await list_group_summaries_payload(),
        }

    @router.get("/groups/{group_id}", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_detail(group_id: str):
        """
        获取面板群detail
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        detail = await build_group_detail_payload(normalized_group_id)
        return detail

    @router.get("/groups/{group_id}/workspace", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_workspace(
        group_id: str,
        message_limit: int = Query(default=40, ge=10, le=100),
        member_page_size: int = Query(default=20, ge=5, le=100),
    ):
        """
        获取面板群workspace
        :param group_id: 群号
        :param message_limit: message_limit 参数
        :param member_page_size: member_page_size 参数
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        detail_task = asyncio.create_task(build_group_detail_payload(normalized_group_id))
        group_profile_task = asyncio.create_task(build_group_profile_payload(normalized_group_id))
        bot_profile_task = asyncio.create_task(fetch_group_bot_profile(normalized_group_id))
        messages_task = asyncio.create_task(build_group_messages_payload(normalized_group_id, limit=message_limit))
        members_task = asyncio.create_task(build_group_members_payload(normalized_group_id, page=1, page_size=member_page_size))
        announcements_task = asyncio.create_task(build_group_announcements_payload(normalized_group_id))
        essence_task = asyncio.create_task(build_group_essence_payload(normalized_group_id))
        honors_task = asyncio.create_task(build_group_honors_payload(normalized_group_id, honor_type="all"))
        files_task = asyncio.create_task(build_group_files_payload(normalized_group_id, file_count=30))
        detail, group_profile, bot_profile, messages, members, announcements, essence, honors, files = await asyncio.gather(
            detail_task, group_profile_task, bot_profile_task, messages_task, members_task,
            announcements_task, essence_task, honors_task, files_task,
        )
        return {
            "group_id": normalized_group_id,
            "detail": detail,
            "group_profile": group_profile,
            "bot_profile": bot_profile,
            "messages": messages,
            "members": members,
            "announcements": announcements,
            "essence": essence,
            "honors": honors,
            "files": files,
        }

    @router.get("/groups/{group_id}/profile", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_profile(group_id: str):
        """
        获取面板群资料
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_profile_payload(normalized_group_id)

    @router.get("/groups/{group_id}/statistics", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_statistics(group_id: str):
        """
        获取面板群statistics
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_statistics_payload(normalized_group_id)

    @router.get("/groups/{group_id}/messages", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_messages(
        group_id: str,
        limit: int = Query(default=50, ge=1, le=100),
        before_id: Optional[int] = Query(default=None, ge=1),
        after_id: Optional[int] = Query(default=None, ge=1),
    ):
        """
        获取面板群消息
        :param group_id: 群号
        :param limit: 数量限制
        :param before_id: 标识值
        :param after_id: 标识值
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_messages_payload(
            normalized_group_id,
            limit=limit,
            before_id=before_id,
            after_id=after_id,
        )

    @router.post("/groups/{group_id}/messages", dependencies=[Depends(verify_dashboard_token)])
    async def post_dashboard_group_message(group_id: str, payload: DashboardSendMessageRequest):
        """
        处理 post_dashboard_group_message 的业务逻辑
        :param group_id: 群号
        :param payload: 载荷数据
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        message = payload.message.strip()
        if not message:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Message cannot be empty.")
        try:
            result = await send_group_message_action(normalized_group_id, message)
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to send message: {type(err).__name__}: {err}",
            ) from err
        return {
            "ok": True,
            "action": "send_message",
            **result,
        }

    @router.get("/groups/{group_id}/members", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_members(
        group_id: str,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=50, ge=1, le=200),
        keyword: str = Query(default=""),
    ):
        """
        获取面板群成员
        :param group_id: 群号
        :param page: 页码
        :param page_size: 分页大小
        :param keyword: 关键字
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_members_payload(
            normalized_group_id,
            page=page,
            page_size=page_size,
            keyword=keyword,
        )

    @router.get("/groups/{group_id}/feature-switches", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_feature_switches(group_id: str):
        """
        获取面板群featureswitches
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_feature_switches_payload(normalized_group_id)

    @router.post("/groups/{group_id}/feature-switches/{switch_key}", dependencies=[Depends(verify_dashboard_token)])
    async def post_dashboard_group_feature_switch(group_id: str, switch_key: str, payload: DashboardFeatureSwitchRequest):
        """
        处理 post_dashboard_group_feature_switch 的业务逻辑
        :param group_id: 群号
        :param switch_key: switch_key 参数
        :param payload: 载荷数据
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        try:
            result = await set_group_feature_switch_action(normalized_group_id, switch_key, payload.enabled)
        except KeyError as err:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown feature switch: {switch_key}") from err
        return {
            "ok": True,
            "action": "set_feature_switch",
            **result,
        }

    @router.get("/groups/{group_id}/approval", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_approval(group_id: str):
        """
        获取面板群审批
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_approval_payload(normalized_group_id)

    @router.get("/groups/{group_id}/broadcast", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_broadcast(group_id: str):
        """
        获取面板群broadcast
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_broadcast_payload(normalized_group_id)

    @router.get("/groups/{group_id}/basic-group-admin", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_basic_group_admin(group_id: str):
        """
        获取面板群basic群管理员
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_basic_admin_payload(normalized_group_id)

    @router.get("/groups/{group_id}/bot-profile", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_bot_profile(group_id: str):
        """
        获取面板群机器人资料
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await fetch_group_bot_profile(normalized_group_id)

    @router.get("/groups/{group_id}/content-guard", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_content_guard(group_id: str):
        """
        获取面板群内容审核
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_content_guard_payload(normalized_group_id)

    @router.get("/groups/{group_id}/member-cleanup", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_member_cleanup(group_id: str):
        """
        获取面板群成员清理
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return build_group_member_cleanup_payload(normalized_group_id)

    @router.get("/groups/{group_id}/event-notice", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_event_notice(group_id: str):
        """
        获取面板群event通知
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_event_notice_payload(normalized_group_id)

    @router.get("/groups/{group_id}/announcements", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_announcements(group_id: str):
        """
        获取面板群announcements
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_announcements_payload(normalized_group_id)

    @router.get("/groups/{group_id}/essence", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_essence(group_id: str):
        """
        获取面板群essence
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_essence_payload(normalized_group_id)

    @router.get("/groups/{group_id}/honors", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_honors(group_id: str, honor_type: str = Query(default="all", alias="type")):
        """
        获取面板群honors
        :param group_id: 群号
        :param honor_type: honor_type 参数
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_honors_payload(normalized_group_id, honor_type=honor_type)

    @router.get("/groups/{group_id}/files", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_files(
        group_id: str,
        folder_id: Optional[str] = Query(default=None),
        folder: Optional[str] = Query(default=None),
        file_count: int = Query(default=50, ge=1, le=200),
    ):
        """
        获取面板群文件
        :param group_id: 群号
        :param folder_id: 标识值
        :param folder: folder 参数
        :param file_count: file_count 参数
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        return await build_group_files_payload(
            normalized_group_id,
            folder_id=folder_id,
            folder=folder,
            file_count=file_count,
        )

    @router.get("/groups/{group_id}/wordcloud-card", dependencies=[Depends(verify_dashboard_token)])
    async def get_dashboard_group_wordcloud_card(group_id: str):
        """
        获取面板群词云card
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        source = await load_group_wordcloud_source(normalized_group_id)
        if not source.available:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wordcloud source not found.")

        try:
            import jieba
        except ModuleNotFoundError as err:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="jieba is not installed.") from err

        segmented_text = " ".join(jieba.lcut(source.text or ""))
        output_path = resolve_wordcloud_output_path(normalized_group_id)
        success, result = await render_wordcloud_image(
            segmented_text,
            stop_words=source.stop_words,
            img_path=output_path,
            group_id=normalized_group_id,
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(result))

        headers = {
            "Cache-Control": "no-store",
            "Content-Disposition": f'inline; filename="{Path(output_path).name}"',
        }
        return Response(content=result, media_type="image/png", headers=headers)

    @router.post("/broadcast/send", dependencies=[Depends(verify_dashboard_token)])
    async def post_dashboard_broadcast(payload: DashboardBroadcastRequest):
        """
        处理 post_dashboard_broadcast 的业务逻辑
        :param payload: 载荷数据
        :return: None
        """
        message = payload.message.strip()
        if not message:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Broadcast message cannot be empty.")
        try:
            result = await broadcast_message_action(
                message,
                include_group_ids=payload.include_group_ids,
                exclude_group_ids=payload.exclude_group_ids,
            )
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to broadcast message: {type(err).__name__}: {err}",
            ) from err
        return {
            "ok": True,
            "action": "broadcast",
            **result,
        }

    @router.post("/groups/{group_id}/actions/mark-read", dependencies=[Depends(verify_dashboard_token)])
    async def post_dashboard_group_mark_read(group_id: str):
        """
        读取post面板群mark
        :param group_id: 群号
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        try:
            result = await mark_group_msg_as_read_action(normalized_group_id)
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to mark group messages as read: {type(err).__name__}: {err}",
            ) from err
        return {
            "ok": True,
            "action": "mark_read",
            **result,
        }

    @router.post("/groups/{group_id}/actions/whole-ban", dependencies=[Depends(verify_dashboard_token)])
    async def post_dashboard_group_whole_ban(group_id: str, payload: DashboardWholeBanRequest):
        """
        处理 post_dashboard_group_whole_ban 的业务逻辑
        :param group_id: 群号
        :param payload: 载荷数据
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        try:
            result = await set_group_whole_ban_action(normalized_group_id, payload.enabled)
        except PermissionError as err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to change whole-ban status: {type(err).__name__}: {err}",
            ) from err
        return {
            "ok": True,
            "action": "whole_ban",
            **result,
        }

    @router.post("/groups/{group_id}/actions/mute", dependencies=[Depends(verify_dashboard_token)])
    async def post_dashboard_group_mute(group_id: str, payload: DashboardMuteRequest):
        """
        处理 post_dashboard_group_mute 的业务逻辑
        :param group_id: 群号
        :param payload: 载荷数据
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        try:
            result = await mute_group_member_action(normalized_group_id, payload.user_id, payload.duration)
        except PermissionError as err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to mute member: {type(err).__name__}: {err}",
            ) from err
        return {
            "ok": True,
            "action": "mute",
            **result,
        }

    @router.post("/groups/{group_id}/actions/kick", dependencies=[Depends(verify_dashboard_token)])
    async def post_dashboard_group_kick(group_id: str, payload: DashboardKickRequest):
        """
        处理 post_dashboard_group_kick 的业务逻辑
        :param group_id: 群号
        :param payload: 载荷数据
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        try:
            result = await kick_group_member_action(
                normalized_group_id,
                payload.user_id,
                reject_add_request=payload.reject_add_request,
            )
        except PermissionError as err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to kick member: {type(err).__name__}: {err}",
            ) from err
        return {
            "ok": True,
            "action": "kick",
            **result,
        }

    @router.post("/groups/{group_id}/actions/special-title", dependencies=[Depends(verify_dashboard_token)])
    async def post_dashboard_group_special_title(group_id: str, payload: DashboardSpecialTitleRequest):
        """
        处理 post_dashboard_group_special_title 的业务逻辑
        :param group_id: 群号
        :param payload: 载荷数据
        :return: None
        """
        normalized_group_id = await ensure_group_exists(group_id)
        try:
            result = await set_group_special_title_action(
                normalized_group_id,
                payload.user_id,
                payload.special_title,
            )
        except PermissionError as err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to set special title: {type(err).__name__}: {err}",
            ) from err
        return {
            "ok": True,
            "action": "special_title",
            **result,
        }

    return router
