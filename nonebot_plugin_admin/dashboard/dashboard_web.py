from __future__ import annotations

import html
import json
import logging
from pathlib import Path

import nonebot
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from nonebot import logger
from starlette.requests import Request
from starlette.responses import Response

from ..core.config import parse_string_list, plugin_config
from .dashboard_api import create_dashboard_api_router


DASHBOARD_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = DASHBOARD_DIR / "templates" / "index.html"
STATIC_DIR = DASHBOARD_DIR / "static"
PLUGIN_ROOT_DIR = Path(__file__).resolve().parents[1]
ADMIN_WEB_DIST_DIR = PLUGIN_ROOT_DIR / "admin-web" / "dist"

_UVICORN_ACCESS_LOGGER = logging.getLogger("uvicorn.access")


class _DashboardSilentAccessMiddleware:
    def __init__(self, app, prefix: str):
        """
        处理 __init__ 的业务逻辑
        :param app: app 参数
        :param prefix: prefix 参数
        :return: None
        """
        self.app = app
        self.prefix = prefix

    async def __call__(self, scope, receive, send):
        """
        处理 __call__ 的业务逻辑
        :param scope: scope 参数
        :param receive: receive 参数
        :param send: send 参数
        :return: None
        """
        if scope["type"] == "http" and scope.get("path", "").startswith(self.prefix):
            _prev_level = _UVICORN_ACCESS_LOGGER.level
            _UVICORN_ACCESS_LOGGER.setLevel(logging.CRITICAL + 1)
            try:
                await self.app(scope, receive, send)
            finally:
                _UVICORN_ACCESS_LOGGER.setLevel(_prev_level)
        else:
            await self.app(scope, receive, send)


def normalize_dashboard_base_path(raw_path: str) -> str:
    """
    规范化面板base路径
    :param raw_path: 路径对象
    :return: str
    """
    normalized = raw_path.strip() or "/admin-dashboard"
    normalized = "/" + normalized.strip("/")
    return normalized.rstrip("/") or "/admin-dashboard"


def _normalize_dashboard_host(raw_host: object) -> str:
    """
    规范化面板host
    :param raw_host: raw_host 参数
    :return: str
    """
    host = str(raw_host or "127.0.0.1").strip() or "127.0.0.1"
    if host in {"0.0.0.0", "::", "[::]"}:
        return "127.0.0.1"
    if ":" in host and not host.startswith("["):
        return f"[{host}]"
    return host


def build_dashboard_runtime_url(base_path: str) -> str:
    """
    构建面板运行时地址
    :param base_path: 路径对象
    :return: str
    """
    driver = nonebot.get_driver()
    host = _normalize_dashboard_host(getattr(driver.config, "host", "127.0.0.1"))
    port = str(getattr(driver.config, "port", 8080) or 8080)
    return f"http://{host}:{port}{base_path}"


def resolve_dashboard_cors_allow_origins() -> list[str]:
    """
    解析面板corsalloworigins
    :return: list[str]
    """
    return parse_string_list(plugin_config.dashboard_cors_allow_origins)


def ensure_dashboard_cors(server_app) -> None:
    """
    确保面板cors
    :param server_app: server_app 参数
    :return: None
    """
    allow_origins = resolve_dashboard_cors_allow_origins()
    if not allow_origins:
        return

    cors_state = getattr(server_app.state, "admin_dashboard_cors_state", None)
    desired_state = (
        tuple(allow_origins),
        bool(plugin_config.dashboard_cors_allow_credentials),
    )
    if cors_state == desired_state:
        return

    if cors_state is not None:
        logger.warning(
            "Admin dashboard CORS is already registered with a different configuration. "
            "Restart the bot if you changed dashboard_cors_allow_origins."
        )
        return

    server_app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=plugin_config.dashboard_cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    server_app.state.admin_dashboard_cors_state = desired_state
    logger.info(f"Admin dashboard CORS enabled for origins: {', '.join(allow_origins)}")


def _render_dashboard_html(base_path: str) -> str:
    """
    渲染面板HTML
    :param base_path: 路径对象
    :return: str
    """
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    bootstrap = {
        "title": plugin_config.dashboard_title,
        "basePath": base_path,
        "apiBasePath": f"{base_path}/api",
        "authRequired": bool(plugin_config.dashboard_api_token.strip()),
        "frontendEnabled": plugin_config.dashboard_frontend_enabled,
    }
    return (
        template.replace("__ADMIN_DASHBOARD_TITLE__", html.escape(plugin_config.dashboard_title))
        .replace("__ADMIN_DASHBOARD_STATIC_PREFIX__", f"{base_path}/static")
        .replace(
            "__ADMIN_DASHBOARD_BOOTSTRAP__",
            json.dumps(bootstrap, ensure_ascii=False),
        )
    )


def resolve_dashboard_frontend_dist_dir() -> Path | None:
    """
    解析面板frontenddistdir
    :return: Path | None
    """
    index_path = ADMIN_WEB_DIST_DIR / "index.html"
    if index_path.exists():
        return ADMIN_WEB_DIST_DIR
    return None


def _resolve_admin_web_asset(frontend_dist_dir: Path, full_path: str) -> Path:
    """
    解析管理员webasset
    :param frontend_dist_dir: frontend_dist_dir 参数
    :param full_path: 路径对象
    :return: Path
    """
    normalized_path = full_path.strip("/")
    if not normalized_path:
        return frontend_dist_dir / "index.html"

    if normalized_path == "api" or normalized_path.startswith("api/"):
        raise FileNotFoundError(normalized_path)

    candidate = (frontend_dist_dir / normalized_path).resolve()
    frontend_root = frontend_dist_dir.resolve()
    try:
        candidate.relative_to(frontend_root)
    except ValueError as err:
        raise FileNotFoundError(normalized_path) from err

    if candidate.is_file():
        return candidate

    return frontend_dist_dir / "index.html"


def register_dashboard_routes() -> bool:
    """
    注册面板routes
    :return: bool
    """
    if not plugin_config.dashboard_enabled:
        return False

    driver = nonebot.get_driver()
    server_app = getattr(driver, "server_app", None)
    if server_app is None:
        logger.warning("Admin dashboard requires a FastAPI driver. Current driver does not expose server_app.")
        return False

    ensure_dashboard_cors(server_app)

    base_path = normalize_dashboard_base_path(plugin_config.dashboard_base_path)
    registered_paths = getattr(server_app.state, "admin_dashboard_registered_paths", set())
    if base_path in registered_paths:
        return True

    server_app.add_middleware(_DashboardSilentAccessMiddleware, prefix=base_path)

    server_app.include_router(create_dashboard_api_router(base_path))

    if plugin_config.dashboard_frontend_enabled:
        frontend_dist_dir = resolve_dashboard_frontend_dist_dir()
        if frontend_dist_dir is not None:

            async def dashboard_frontend_dist(full_path: str = ""):
                """
                处理 dashboard_frontend_dist 的业务逻辑
                :param full_path: 路径对象
                :return: None
                """
                try:
                    file_path = _resolve_admin_web_asset(frontend_dist_dir, full_path)
                except FileNotFoundError:
                    return HTMLResponse("Not Found", status_code=404)
                return FileResponse(file_path)

            server_app.add_api_route(base_path, dashboard_frontend_dist, methods=["GET"], include_in_schema=False)
            server_app.add_api_route(f"{base_path}/", dashboard_frontend_dist, methods=["GET"], include_in_schema=False)
            server_app.add_api_route(
                f"{base_path}/{{full_path:path}}",
                dashboard_frontend_dist,
                methods=["GET"],
                include_in_schema=False,
            )
            logger.info(f"Admin dashboard frontend bundle: admin-web/dist -> {frontend_dist_dir}")
        else:
            static_route = f"{base_path}/static"
            static_paths = getattr(server_app.state, "admin_dashboard_registered_static_paths", set())
            if static_route not in static_paths:
                server_app.mount(
                    static_route,
                    StaticFiles(directory=str(STATIC_DIR)),
                    name=f"admin-dashboard-static-{base_path.strip('/').replace('/', '-') or 'root'}",
                )
                static_paths = set(static_paths)
                static_paths.add(static_route)
                server_app.state.admin_dashboard_registered_static_paths = static_paths

            async def dashboard_frontend():
                """
                处理 dashboard_frontend 的业务逻辑
                :return: None
                """
                return HTMLResponse(_render_dashboard_html(base_path))

            server_app.add_api_route(base_path, dashboard_frontend, methods=["GET"], include_in_schema=False)
            server_app.add_api_route(f"{base_path}/", dashboard_frontend, methods=["GET"], include_in_schema=False)
            logger.warning(
                "Admin dashboard frontend bundle admin-web/dist was not found. "
                "Falling back to the built-in minimal dashboard page."
            )

    registered_paths = set(registered_paths)
    registered_paths.add(base_path)
    server_app.state.admin_dashboard_registered_paths = registered_paths

    if not plugin_config.dashboard_api_token.strip():
        logger.warning(
            "Admin dashboard API is enabled without dashboard_api_token. "
            "The API will be accessible without authentication."
        )

    api_url = f"{build_dashboard_runtime_url(base_path)}/api"
    logger.info(f"Admin dashboard API is available at {api_url}")

    if plugin_config.dashboard_frontend_enabled:
        frontend_url = build_dashboard_runtime_url(base_path)
        logger.info(f"Admin dashboard frontend is available at {frontend_url}")

    return True
