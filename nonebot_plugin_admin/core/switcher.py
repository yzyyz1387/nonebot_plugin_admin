# python3
# -*- coding: utf-8 -*-
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment, ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .exact_command import exact_command
from .html_snapshot import render_html_card_to_image
from .path import *
from .state_feedback import build_toggle_state_message
from .utils import fi, log_fi
from ..statistics.config_orm_store import orm_load_switcher, orm_save_switcher_group


switcher = on_command('开关', priority=1, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@switcher.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent, args: Message = CommandArg()):
    gid = str(event.group_id)
    user_input_func_name = str(args).strip()
    try:
        await switcher_handle(gid, matcher, user_input_func_name)
    except KeyError:
        await switcher_integrity_check(bot)
        await switcher_handle(gid, matcher, user_input_func_name)


switcher_html = on_command(
    '开关状态',
    priority=1,
    rule=exact_command('开关状态'),
    block=True,
    permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
)


@switcher_html.handle()
async def _(matcher: Matcher, event: GroupMessageEvent):
    gid = str(event.group_id)
    current_status = await _load_group_switcher(gid)
    summary_text = '当前群组开关状态：\n' + '\n'.join(
        [f'{admin_funcs[func][0]}：{"开启" if current_status.get(func, False) else "关闭"}' for func in admin_funcs]
    )
    try:
        from os.path import dirname
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(str(dirname(__file__))))
        template = env.get_template('switcher.html')
        html = template.render(funcs_status=current_status, funcs_name=admin_funcs, gid=gid)
        img_path = (re_img_path / f'{gid}.png').resolve()
        img_bytes = await render_html_card_to_image(
            html,
            img_path,
            viewport_width=640,
            viewport_height=1080,
        )
        await fi(matcher, MessageSegment.image(img_bytes))
    except ActionFailed:
        await log_fi(matcher, summary_text, '可能被风控，已使用文字发送', err=True)
    except FinishedException:
        pass
    except Exception as e:
        await log_fi(
            matcher,
            summary_text,
            f'开关渲染网页并截图失败，已使用文字发送，错误信息：\n{"-" * 30}{type(e)}: {e}{"-" * 30}',
            err=True,
        )


async def _load_group_switcher(gid: str) -> dict:
    """
    加载群开关
    :param gid: 群号
    :return: dict
    """
    group_data = dict(build_default_switchers())
    orm_data = await orm_load_switcher()
    group_data.update(orm_data.get(gid, {}))
    return group_data


async def _save_group_switcher(gid: str, funcs: dict) -> None:
    """
    保存群开关
    :param gid: 群号
    :param funcs: 功能映射
    :return: None
    """
    normalized = {
        func_name: bool(funcs.get(func_name, is_default_enabled(func_name)))
        for func_name in admin_funcs
    }
    await orm_save_switcher_group(gid, normalized)


async def switcher_integrity_check(bot: Bot):
    """
    检查开关integrity
    :param bot: Bot 实例
    :return: None
    """
    g_list = await bot.get_group_list()
    orm_data = await orm_load_switcher()

    for group in g_list:
        gid = str(group['group_id'])
        current = orm_data.get(gid, {})
        normalized = {
            func_name: bool(current.get(func_name, is_default_enabled(func_name)))
            for func_name in admin_funcs
        }
        if normalized != current:
            await orm_save_switcher_group(gid, normalized)


async def switcher_handle(gid, matcher, user_input_func_name):
    """
    处理开关
    :param gid: 群号
    :param matcher: Matcher 实例
    :param user_input_func_name: user_input_func_name 参数
    :return: None
    """
    if not user_input_func_name:
        await fi(matcher, "请输入功能名，例如【开关消息记录】")
        return

    for func in admin_funcs:
        if user_input_func_name in admin_funcs[func]:
            funcs_status = await _load_group_switcher(gid)
            funcs_status[func] = not funcs_status[func]
            await _save_group_switcher(gid, funcs_status)
            display_name = get_func_display_name(func)
            await fi(
                matcher,
                build_toggle_state_message(
                    display_name,
                    enabled=funcs_status[func],
                    toggle_command=f"开关{display_name}",
                ),
            )
            return

    await fi(matcher, f"未找到功能【{user_input_func_name}】")
