from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MenuItem:
    name: str
    usage: str
    permission: str = "所有人"
    aliases: List[str] = field(default_factory=list)


@dataclass
class MenuCategory:
    name: str
    items: List[MenuItem] = field(default_factory=list)


class MenuRegistry:
    _categories: Dict[str, MenuCategory]

    def __init__(self) -> None:
        """
        处理 __init__ 的业务逻辑
        :return: None
        """
        self._categories: Dict[str, MenuCategory] = {}

    def register(
        self,
        category: str,
        name: str,
        usage: str,
        *,
        permission: str = "所有人",
        aliases: List[str] | None = None,
    ) -> None:
        """
        注册
        :param category: category 参数
        :param name: 名称
        :param usage: usage 参数
        :param permission: permission 参数
        :param aliases: aliases 参数
        :return: None
        """
        if category not in self._categories:
            self._categories[category] = MenuCategory(name=category)
        self._categories[category].items.append(
            MenuItem(name=name, usage=usage, permission=permission, aliases=aliases or [])
        )

    def get_categories(self) -> List[MenuCategory]:
        """
        获取categories
        :return: List[MenuCategory]
        """
        return list(self._categories.values())

    def get_all_items(self) -> List[MenuItem]:
        """
        获取allitems
        :return: List[MenuItem]
        """
        items: List[MenuItem] = []
        for cat in self._categories.values():
            items.extend(cat.items)
        return items


menu_registry = MenuRegistry()
