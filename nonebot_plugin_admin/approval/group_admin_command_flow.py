from typing import Awaitable, Callable, Iterable

from nonebot.matcher import Matcher
from nonebot.typing import T_State

from . import approval_store
from ..core.state_feedback import build_toggle_state_message
from ..core.utils import fi


async def handle_list_group_admins(matcher: Matcher, gid: str):
    """
    处理list群管理员
    :param matcher: Matcher 实例
    :param gid: 群号
    :return: None
    """
    admins = await approval_store.g_admin_async()
    if gid in admins:
        await matcher.finish(f"本群分管：{admins[gid]}")
    await matcher.finish("查询不到，使用 分管+@xx 来添加分管")


async def handle_list_all_group_admins(matcher: Matcher):
    """
    处理listall群管理员
    :param matcher: Matcher 实例
    :return: None
    """
    await matcher.finish(str(await approval_store.g_admin_async()))



def _parse_targets(state: T_State, sb: Iterable[str]) -> list[str]:
    """
    解析targets
    :param state: 状态字典
    :param sb: 目标成员列表
    :return: list[str]
    """
    if sb and "all" not in sb:
        return [str(qq) for qq in sb]
    return [qq for qq in str(state["_prefix"]["command_arg"]).split(" ") if qq]


async def handle_add_group_admins(matcher: Matcher, gid: str, state: T_State, sb: Iterable[str]):
    """
    处理add群管理员
    :param matcher: Matcher 实例
    :param gid: 群号
    :param state: 状态字典
    :param sb: 目标成员列表
    :return: None
    """
    for qq in _parse_targets(state, sb):
        g_admin_handle = await approval_store.g_admin_add(gid, int(qq))
        if g_admin_handle:
            await matcher.send(f"{qq} 已成为本群分群管理员：将接收加群处理结果，同时具有群管权限，但分管不能任命超管")
        else:
            await matcher.send(f"用户 {qq} 已存在")


async def handle_toggle_superuser_receive(matcher: Matcher):
    """
    处理togglesuperuserreceive
    :param matcher: Matcher 实例
    :return: None
    """
    status = await approval_store.su_on_off()
    await matcher.finish(
        build_toggle_state_message(
            "审批消息接收",
            enabled=status,
            toggle_command="接收",
        )
    )


async def handle_remove_group_admins(
    matcher: Matcher,
    gid: str,
    state: T_State,
    sb: Iterable[str],
    status_checker: Callable[[str, str], Awaitable[bool]],
):
    """
    处理remove群管理员
    :param matcher: Matcher 实例
    :param gid: 群号
    :param state: 状态字典
    :param sb: 目标成员列表
    :param status_checker: status_checker 参数
    :return: None
    """
    status = await status_checker("requests", gid)
    if not status:
        await fi(matcher, "请先发送【开关加群审批】开启加群处理")
        return

    for qq in _parse_targets(state, sb):
        g_admin_del_handle = await approval_store.g_admin_del(gid, int(qq))
        if g_admin_del_handle is True:
            await matcher.send(f"{qq} 删除成功")
        elif g_admin_del_handle is False:
            await matcher.send(f"{qq} 还不是分群管理员")
        else:
            await matcher.send(f"群 {gid} 未添加过分群管理员\n使用 /gad+ [用户（可@ 或 qq）] 来添加分群管理员")
