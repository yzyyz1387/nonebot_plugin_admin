from typing import Awaitable, Callable, Optional, Sequence, Union

from nonebot.adapters.onebot.v11 import Bot
from nonebot.matcher import Matcher

from ..core.utils import change_s_title, mute_sb

Target = Union[str, int]
SkipCallback = Callable[[str], Awaitable[None]]


def normalize_targets(targets: Optional[Sequence[Target]]) -> list[str]:
    """
    规范化targets
    :param targets: targets 参数
    :return: list[str]
    """
    if not targets:
        return []
    return [str(target) for target in targets]


def contains_all_target(targets: Optional[Sequence[Target]]) -> bool:
    """
    处理 contains_all_target 的业务逻辑
    :param targets: targets 参数
    :return: bool
    """
    return any(str(target) == "all" for target in normalize_targets(targets))


def is_superuser(user_id: Target, superusers: Sequence[Target]) -> bool:
    """
    处理 is_superuser 的业务逻辑
    :param user_id: 用户号
    :param superusers: 超管列表
    :return: bool
    """
    return str(user_id) in {str(superuser) for superuser in superusers}


def parse_mute_duration(raw_message: str) -> Optional[int]:
    """
    解析muteduration
    :param raw_message: 原始消息文本
    :return: Optional[int]
    """
    digits = "".join(ch for ch in raw_message if ch.isdigit())
    return int(digits) if digits else None


async def execute_mute(bot: Bot, group_id: int, targets: Sequence[Target], duration: Optional[int]) -> None:
    """
    处理 execute_mute 的业务逻辑
    :param bot: Bot 实例
    :param group_id: 群号
    :param targets: targets 参数
    :param duration: duration 参数
    :return: None
    """
    async for action in mute_sb(bot, gid=group_id, lst=normalize_targets(targets), time=duration):
        if action:
            await action


async def update_group_cards(bot: Bot, group_id: int, targets: Sequence[Target], card: str) -> None:
    """
    更新群cards
    :param bot: Bot 实例
    :param group_id: 群号
    :param targets: targets 参数
    :param card: card 参数
    :return: None
    """
    for target in normalize_targets(targets):
        await bot.set_group_card(group_id=group_id, user_id=int(target), card=card)


def resolve_special_title_targets(
    operator_id: int,
    targets: Optional[Sequence[Target]],
    superusers: Sequence[Target],
) -> tuple[list[int], Optional[str]]:
    """
    解析specialtitletargets
    :param operator_id: 标识值
    :param targets: targets 参数
    :param superusers: 超管列表
    :return: tuple[list[int], Optional[str]]
    """
    normalized = normalize_targets(targets)
    if not normalized or (len(normalized) == 1 and normalized[0] == str(operator_id)):
        return [operator_id], None
    if contains_all_target(normalized):
        return [], "all"
    if not is_superuser(operator_id, superusers):
        return [], "permission"
    return [int(target) for target in normalized], None


async def update_special_titles(
    bot: Bot,
    matcher: Matcher,
    group_id: int,
    targets: Sequence[int],
    special_title: str,
) -> None:
    """
    更新specialtitles
    :param bot: Bot 实例
    :param matcher: Matcher 实例
    :param group_id: 群号
    :param targets: targets 参数
    :param special_title: special_title 参数
    :return: None
    """
    for target in targets:
        await change_s_title(bot, matcher, group_id, target, special_title)


async def execute_group_kick(
    bot: Bot,
    group_id: int,
    operator_id: int,
    targets: Sequence[Target],
    superusers: Sequence[Target],
    *,
    reject_add_request: bool,
    on_skip_self: Optional[SkipCallback] = None,
    on_skip_superuser: Optional[SkipCallback] = None,
) -> list[int]:
    """
    处理 execute_group_kick 的业务逻辑
    :param bot: Bot 实例
    :param group_id: 群号
    :param operator_id: 标识值
    :param targets: targets 参数
    :param superusers: 超管列表
    :param reject_add_request: reject_add_request 参数
    :param on_skip_self: on_skip_self 参数
    :param on_skip_superuser: on_skip_superuser 参数
    :return: list[int]
    """
    kicked: list[int] = []
    for target in normalize_targets(targets):
        if target == "all":
            continue
        if target == str(operator_id):
            if on_skip_self:
                await on_skip_self(target)
            continue
        if is_superuser(target, superusers):
            if on_skip_superuser:
                await on_skip_superuser(target)
            continue
        await bot.set_group_kick(
            group_id=group_id,
            user_id=int(target),
            reject_add_request=reject_add_request,
        )
        kicked.append(int(target))
    return kicked


async def toggle_group_admin(bot: Bot, group_id: int, targets: Sequence[Target], enable: bool) -> None:
    """
    切换群管理员
    :param bot: Bot 实例
    :param group_id: 群号
    :param targets: targets 参数
    :param enable: 是否启用
    :return: None
    """
    for target in normalize_targets(targets):
        await bot.set_group_admin(group_id=group_id, user_id=int(target), enable=enable)


async def toggle_essence(bot: Bot, reply_message_id: Optional[int], enable: bool) -> None:
    """
    切换essence
    :param bot: Bot 实例
    :param reply_message_id: 标识值
    :param enable: 是否启用
    :return: None
    """
    if reply_message_id is None:
        return
    api_name = "set_essence_msg" if enable else "delete_essence_msg"
    await bot.call_api(api=api_name, message_id=reply_message_id)


