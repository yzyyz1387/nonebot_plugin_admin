from __future__ import annotations

from typing import Iterable

from nonebot.adapters import Event
from nonebot.rule import Rule


def exact_command(command: str, aliases: Iterable[str] | None = None) -> Rule:
    """
    处理 exact_command 的业务逻辑
    :param command: 命令文本
    :param aliases: aliases 参数
    :return: Rule
    """
    exact_names = {command.strip()}
    if aliases:
        exact_names.update(alias.strip() for alias in aliases if alias and alias.strip())

    async def _checker(event: Event) -> bool:
        """
        处理 _checker 的业务逻辑
        :param event: 事件对象
        :return: bool
        """
        try:
            raw_message = str(event.get_message())
        except Exception:
            raw_message = str(getattr(event, "raw_message", "") or "")
        return raw_message.strip() in exact_names

    return Rule(_checker)
