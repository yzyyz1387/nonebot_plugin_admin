from __future__ import annotations

from nonebot import get_driver, on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Event

from ..core.config import plugin_config
from ..core.exact_command import exact_command

db_url_cmd = on_command("数据库地址", priority=1, rule=exact_command("数据库地址"), block=True, permission=SUPERUSER)


@db_url_cmd.handle()
async def _(event: Event):
    db_url = str(getattr(get_driver().config, "tortoise_orm_db_url", "") or "").strip()

    if not db_url:
        await db_url_cmd.finish("未配置数据库地址。请在 .env 中设置 tortoise_orm_db_url")

    lines = [f"数据库地址：{db_url}"]

    if db_url.startswith("sqlite://"):
        raw = db_url[len("sqlite://"):]
        if raw and raw != ":memory:":
            from pathlib import Path
            p = Path(raw)
            if not p.is_absolute():
                p = Path.cwd() / p
            lines.append(f"文件路径：{p.resolve()}")

    if not plugin_config.statistics_orm_enabled:
        lines.append("提示：ORM 统计未启用，数据库当前仅用于迁移存储。设置 statistics_orm_enabled=true 可启用")

    await db_url_cmd.finish("\n".join(lines))
