"""OneBot v12 适配器配置项。

FrontMatter:
    sidebar_position: 2
    description: onebot.v12.config 模块
"""

from typing import Set, Dict, Optional

from pydantic import Field, AnyUrl, BaseModel


class WSUrl(AnyUrl):
    """ws或wss url"""

    allow_schemes = {"ws", "wss"}


class Config(BaseModel):
    """OneBot 配置类。"""

    onebot_access_token: Optional[str] = Field(
        default=None, alias="onebot_v12_access_token"
    )
    """OneBot 协议授权令牌"""
    onebot_ws_urls: Set[WSUrl] = Field(default_factory=set, alias="onebot_v12_ws_urls")
    """OneBot 正向 Websocket 连接目标 URL 集合"""
    onebot_api_roots: Dict[str, AnyUrl] = Field(
        default_factory=dict, alias="onebot_v12_api_roots"
    )
    """OneBot HTTP API 请求地址字典"""

    class Config:
        extra = "ignore"
