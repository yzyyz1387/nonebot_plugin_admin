"""OneBot v12 杂项。

FrontMatter:
    sidebar_position: 8
    description: onebot.v12.utils 模块
"""

from typing import TypeVar
from base64 import b64encode

from nonebot.typing import overrides
from nonebot.utils import DataclassEncoder, logger_wrapper

T = TypeVar("T")


log = logger_wrapper("OneBot V12")


def flattened_to_nested(data: T) -> T:
    """将扁平键值转为嵌套字典。"""
    if isinstance(data, dict):
        pairs = [
            (
                key.split(".") if isinstance(key, str) else key,
                flattened_to_nested(value),
            )
            for key, value in data.items()
        ]
        result = {}
        for key_list, value in pairs:
            target = result
            for key in key_list[:-1]:
                target = target.setdefault(key, {})
            target[key_list[-1]] = value
        return result  # type: ignore
    elif isinstance(data, list):
        return [flattened_to_nested(item) for item in data]  # type: ignore
    return data


class CustomEncoder(DataclassEncoder):
    """OneBot V12 使用的 `JSONEncoder`"""

    @overrides(DataclassEncoder)
    def default(self, o):
        if isinstance(o, bytes):
            return b64encode(o).decode()
        return super(CustomEncoder, self).default(o)
