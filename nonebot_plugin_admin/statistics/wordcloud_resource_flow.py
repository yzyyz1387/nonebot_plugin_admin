from __future__ import annotations


MASK_DEPRECATION_MESSAGE = "当前词云已切换为 HTML 截图模式，不再需要更新 mask。"


def build_mask_deprecation_message() -> str:
    """
    构建maskdeprecation消息
    :return: str
    """
    return MASK_DEPRECATION_MESSAGE


async def fetch_remote_background_count(_client=None) -> int:
    """
    拉取remotebackgroundcount
    :param _client: 客户端实例
    :return: int
    """
    return 0


async def fetch_background_content(_client=None, _index: int = 0) -> bytes:
    """
    拉取background内容
    :param _client: 客户端实例
    :param _index: _index 参数
    :return: bytes
    """
    return b""


async def build_background_update_notice(*_, **__) -> str | None:
    """
    构建backgroundupdate通知
    :param _: 可变位置参数
    :param __: 额外关键字参数
    :return: str | None
    """
    return None


async def sync_backgrounds(*_, **__) -> tuple[int, int]:
    """
    同步backgrounds
    :param _: 可变位置参数
    :param __: 额外关键字参数
    :return: tuple[int, int]
    """
    return 0, 0


async def ensure_local_backgrounds(*_, **__) -> bool:
    """
    确保localbackgrounds
    :param _: 可变位置参数
    :param __: 额外关键字参数
    :return: bool
    """
    return True
