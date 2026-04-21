from __future__ import annotations

from os.path import dirname

from jinja2 import Environment, FileSystemLoader
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher

from .exact_command import exact_command
from .html_snapshot import render_html_card_to_image
from .menu_registry import menu_registry
from .path import re_img_path
from .utils import fi, log_fi


def _perm_class(permission: str) -> str:
    """
    处理 _perm_class 的业务逻辑
    :param permission: permission 参数
    :return: str
    """
    mapping = {
        "超管": "su",
        "超级用户": "su",
        "群主": "owner",
        "群主/超管": "owner",
        "管理员": "admin",
        "群管理": "admin",
        "群管": "admin",
        "管理员/群主": "admin",
    }
    return mapping.get(permission, "all")


def _build_template_context() -> list:
    """
    构建templatecontext
    :return: list
    """
    categories = []
    for cat in menu_registry.get_categories():
        commands = []
        for item in cat.items:
            commands.append({
                "name": item.name,
                "usage": item.usage,
                "permission": item.permission,
                "aliases": item.aliases,
                "perm_class": _perm_class(item.permission),
            })
        categories.append({"name": cat.name, "commands": commands})
    return categories


menu_cmd = on_command("群管菜单", priority=2, rule=exact_command("群管菜单"), block=True)


@menu_cmd.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent):
    categories = _build_template_context()
    if not categories:
        await fi(matcher, "暂无可用菜单项")
        return

    fallback_text = "群管菜单：\n"
    for cat in categories:
        fallback_text += f"\n【{cat['name']}】\n"
        for cmd in cat["commands"]:
            fallback_text += f"  {cmd['name']}：{cmd['usage']}\n"

    try:
        env = Environment(loader=FileSystemLoader(str(dirname(__file__))))
        template = env.get_template("menu.html")
        html = template.render(categories=categories)

        gid = str(event.group_id)
        img_path = (re_img_path / f"menu_{gid}.png").resolve()
        img_bytes = await render_html_card_to_image(
            html,
            img_path,
            viewport_width=1320,
            viewport_height=1600,
        )
        await fi(matcher, MessageSegment.image(img_bytes))
    except FinishedException:
        pass
    except Exception as e:
        await log_fi(
            matcher,
            fallback_text,
            f"菜单渲染截图失败，已使用文字发送：{type(e).__name__}: {e}",
            err=True,
        )
