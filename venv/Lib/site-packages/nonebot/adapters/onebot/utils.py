"""OneBot 辅助函数。

FrontMatter:
    sidebar_position: 3
    description: onebot.utils 模块
"""

from typing import Optional


def get_auth_bearer(access_token: Optional[str] = None) -> Optional[str]:
    if not access_token:
        return None
    scheme, _, param = access_token.partition(" ")
    if scheme.lower() not in ["bearer", "token"]:
        return None
    return param


def b2s(b: Optional[bool]) -> Optional[str]:
    """转换布尔值为字符串。"""
    return b if b is None else str(b).lower()
