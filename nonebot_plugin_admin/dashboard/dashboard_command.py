from __future__ import annotations

from nonebot import on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Event

from ..core.config import plugin_config
from ..core.exact_command import exact_command
from .dashboard_web import build_dashboard_runtime_url, normalize_dashboard_base_path

DASHBOARD_URL_ALIASES = {"获取面板", "dashboard地址"}

dashboard_url_cmd = on_command(
    "面板地址",
    aliases=DASHBOARD_URL_ALIASES,
    rule=exact_command("面板地址", DASHBOARD_URL_ALIASES),
    priority=1,
    block=True,
    permission=SUPERUSER,
)


@dashboard_url_cmd.handle()
async def _(event: Event):
    if not plugin_config.dashboard_enabled:
        await dashboard_url_cmd.finish("Dashboard 未启用。请在 .env 中设置 dashboard_enabled=true")

    base_path = normalize_dashboard_base_path(plugin_config.dashboard_base_path)
    url = build_dashboard_runtime_url(base_path)

    lines = [f"Dashboard 地址：{url}"]

    if plugin_config.dashboard_api_token:
        lines.append("API 已启用鉴权，Token 请在 .env 配置文件中查看（dashboard_api_token）")
        lines.append("请求受保护接口时需在 Header 中携带 X-Admin-Token")
    else:
        lines.append("⚠️ 未配置 dashboard_api_token，API 接口无鉴权保护，建议尽快设置")

    lines.append("提示：地址基于当前运行环境所在服务器，如需远程访问请确保网络可达")

    await dashboard_url_cmd.finish("\n".join(lines))
