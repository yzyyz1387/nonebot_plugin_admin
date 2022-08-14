from typing import Any, Dict, List, Union, Literal, Optional

from nonebot.adapters import Bot as BaseBot

from .event import Event, MessageEvent
from .message import Message, MessageSegment

def _check_reply(bot: "Bot", event: MessageEvent): ...
def _check_to_me(bot: "Bot", event: MessageEvent): ...
def _check_nickname(bot: "Bot", event: MessageEvent): ...
async def send(
    bot: "Bot",
    event: Event,
    message: Union[str, Message, MessageSegment],
    at_sender: bool = ...,
    reply_message: bool = ...,
    **kwargs: Any,
) -> Any: ...

class Bot(BaseBot):
    async def call_api(self, api: str, **data) -> Any:
        """调用 OneBot 协议 API。

        参数:
            api: API 名称
            data: API 参数

        返回:
            API 调用返回数据

        异常:
            nonebot.adapters.onebot.exception.NetworkError: 网络错误
            nonebot.adapters.onebot.exception.ActionFailed: API 调用失败
        """
        ...
    async def handle_event(self, event: Event) -> None: ...
    async def send(
        self, event: Event, message: str | Message | MessageSegment, **kwargs: Any
    ) -> Any: ...
    async def get_latest_events(
        self, *, limit: int = ..., timeout: int = ..., **kwargs: Any
    ) -> List[Event]:
        """获取最新事件列表

        参数:
            limit: 获取的事件数量上限，0 表示不限制
            timeout: 没有事件时要等待的秒数，0 表示使用短轮询，不等待
            kwargs: 扩展字段
        """
        ...
    async def get_supported_actions(self, **kwargs: Any) -> List[str]:
        """获取支持的动作列表

        参数:
            kwargs: 扩展字段
        """
        ...
    async def get_status(
        self, **kwargs: Any
    ) -> Dict[Literal["good", "online"] | str, bool]:
        """获取运行状态

        参数:
            kwargs: 扩展字段
        """
        ...
    async def get_version(
        self,
        **kwargs: Any,
    ) -> Dict[Literal["impl", "platform", "version", "onebot_version"] | str, str]:
        """获取版本信息

        参数:
            kwargs: 扩展字段
        """
        ...
    async def send_message(
        self,
        *,
        detail_type: Literal["private", "group", "channel"] | str,
        user_id: str = ...,
        group_id: str = ...,
        guild_id: str = ...,
        channel_id: str = ...,
        message: Message,
        **kwargs: Any,
    ) -> Dict[Literal["message_id", "time"] | str, Any]:
        """发送消息

        参数:
            detail_type: 发送的类型，可以为 private、group 或扩展的类型，和消息事件的 detail_type 字段对应
            user_id: 用户 ID，当 detail_type 为 private 时必须传入
            group_id: 群 ID，当 detail_type 为 group 时必须传入
            guild_id: Guild 群组 ID，当 detail_type 为 channel 时必须传入
            channel_id: 频道 ID，当 detail_type 为 channel 时必须传入
            message: 消息内容
            kwargs: 扩展字段
        """
        ...
    async def delete_message(self, *, message_id: str, **kwargs: Any) -> None:
        """撤回消息

        参数:
            message_id: 唯一的消息 ID
        """
        ...
    async def get_self_info(
        self, **kwargs: Any
    ) -> Dict[Literal["user_id", "nickname"] | str, str]:
        """获取机器人自身信息"""
        ...
    async def get_user_info(
        self, *, user_id: str, **kwargs: Any
    ) -> Dict[Literal["user_id", "nickname"] | str, str]:
        """获取用户信息

        参数:
            user_id: 用户 ID，可以是好友，也可以是陌生人
            kwargs: 扩展字段
        """
        ...
    async def get_friend_list(
        self,
        **kwargs: Any,
    ) -> List[Dict[Literal["user_id", "nickname"] | str, str]]:
        """获取好友列表

        参数:
            kwargs: 扩展字段
        """
        ...
    async def get_group_info(
        self, *, group_id: str, **kwargs: Any
    ) -> Dict[Literal["group_id", "group_name"] | str, str]:
        """获取群信息

        参数:
            group_id: 群 ID
            kwargs: 扩展字段
        """
        ...
    async def get_group_list(
        self,
        **kwargs: Any,
    ) -> List[Dict[Literal["group_id", "group_name"] | str, str]]:
        """获取群列表

        参数:
            kwargs: 扩展字段
        """
        ...
    async def get_group_member_info(
        self, *, group_id: str, user_id: str, **kwargs: Any
    ) -> Dict[Literal["user_id", "nickname"] | str, str]:
        """获取群成员信息

        参数:
            group_id: 群 ID
            user_id: 用户 ID
            kwargs: 扩展字段
        """
        ...
    async def get_group_member_list(
        self, *, group_id: str, **kwargs: Any
    ) -> List[Dict[Literal["user_id", "nickname"] | str, str]]:
        """获取群成员列表

        参数:
            group_id: 群 ID
            kwargs: 扩展字段
        """
        ...
    async def set_group_name(
        self, *, group_id: str, group_name: str, **kwargs: Any
    ) -> None:
        """设置群名称

        参数:
            group_id: 群 ID
            group_name: 群名称
            kwargs: 扩展字段
        """
        ...
    async def leave_group(self, *, group_id: str, **kwargs: Any) -> None:
        """退出群

        参数:
            group_id: 群 ID
            kwargs: 扩展字段
        """
        ...
    async def kick_group_member(
        self, *, group_id: str, user_id: str, **kwargs: Any
    ) -> None:
        """踢出群成员

        参数:
            group_id: 群 ID
            user_id: 用户 ID
            kwargs: 扩展字段
        """
        ...
    async def ban_group_member(
        self, *, group_id: str, user_id: str, **kwargs: Any
    ) -> None:
        """禁言群成员

        参数:
            group_id: 群 ID
            user_id: 用户 ID
            kwargs: 扩展字段
        """
        ...
    async def unban_group_member(
        self, *, group_id: str, user_id: str, **kwargs: Any
    ) -> None:
        """解除禁言群成员

        参数:
            group_id: 群 ID
            user_id: 用户 ID
            kwargs: 扩展字段
        """
        ...
    async def set_group_admin(
        self, *, group_id: str, user_id: str, **kwargs: Any
    ) -> None:
        """设置管理员

        参数:
            group_id: 群 ID
            user_id: 用户 ID
            kwargs: 扩展字段
        """
        ...
    async def unset_group_admin(
        self, *, group_id: str, user_id: str, **kwargs: Any
    ) -> None:
        """解除管理员

        参数:
            group_id: 群 ID
            user_id: 用户 ID
            kwargs: 扩展字段
        """
        ...
    async def get_guild_info(
        self, *, guild_id: str, **kwargs: Any
    ) -> Dict[Literal["guild_id", "guild_name"] | str, str]:
        """获取 Guild 信息

        参数:
            guild_id: 群组 ID
            kwargs: 扩展字段
        """
        ...
    async def get_guild_list(
        self,
        **kwargs: Any,
    ) -> List[Dict[Literal["guild_id", "guild_name"] | str, str]]:
        """获取群组列表

        参数:
            kwargs: 扩展字段
        """
        ...
    async def get_channel_info(
        self, *, guild_id: str, channel_id: str, **kwargs: Any
    ) -> Dict[Literal["channel_id", "channel_name"] | str, str]:
        """获取频道信息

        参数:
            guild_id: 群组 ID
            channel_id: 频道 ID
            kwargs: 扩展字段
        """
        ...
    async def get_channel_list(
        self, *, guild_id: str, **kwargs: Any
    ) -> List[Dict[Literal["channel_id", "channel_name"] | str, str]]:
        """获取频道列表

        参数:
            guild_id: 群组 ID
            kwargs: 扩展字段
        """
        ...
    async def get_guild_member_info(
        self, *, guild_id: str, user_id: str, **kwargs: Any
    ) -> Dict[Literal["user_id", "nickname"] | str, str]:
        """获取群组成员信息

        参数:
            guild_id: 群组 ID
            user_id: 用户 ID
            kwargs: 扩展字段
        """
        ...
    async def get_guild_member_list(
        self, *, guild_id: str, **kwargs: Any
    ) -> List[Dict[Literal["user_id", "nickname"] | str, str]]:
        """获取群组成员列表

        参数:
            guild_id: 群组 ID
            kwargs: 扩展字段
        """
        ...
    async def set_guild_name(
        self, *, guild_id: str, guild_name: str, **kwargs: Any
    ) -> None:
        """设置群组名称

        参数:
            guild_id: 群组 ID
            guild_name: 群组名称
            kwargs: 扩展字段
        """
        ...
    async def set_channel_name(
        self, *, guild_id: str, channel_id: str, channel_name: str, **kwargs: Any
    ) -> None:
        """设置频道名称

        参数:
            guild_id: 群组 ID
            channel_id: 频道 ID
            channel_name: 频道名称
            kwargs: 扩展字段
        """
        ...
    async def leave_guild(self, *, guild_id: str, **kwargs: Any) -> None:
        """退出群组

        参数:
            guild_id: 群组 ID
            kwargs: 扩展字段
        """
        ...
    async def upload_file(
        self,
        *,
        type: Literal["url", "path", "data"] | str,
        name: str,
        url: str = ...,
        headers: Dict[str, str] = ...,
        path: str = ...,
        data: bytes = ...,
        sha256: str = ...,
        **kwargs: Any,
    ) -> Dict[Literal["file_id"] | str, str]:
        """上传文件

        参数:
            type: 上传文件的方式，可以为 url、path、data 或扩展的方式
            name: 文件名
            url: 文件 URL，当 type 为 url 时必须传入
            headers: 下载 URL 时需要添加的 HTTP 请求头，可选传入
            path: 文件路径，当 type 为 path 时必须传入
            data: 文件数据，当 type 为 data 时必须传入
            sha256: 文件数据（原始二进制）的 SHA256 校验和，全小写，可选传入
            kwargs: 扩展字段
        """
        ...
    async def upload_file_fragmented(
        self,
        stage: Literal["prepare", "transfer", "finish"],
        name: str = ...,
        total_size: int = ...,
        sha256: str = ...,
        file_id: str = ...,
        offset: int = ...,
        size: int = ...,
        data: bytes = ...,
        **kwargs: Any,
    ) -> Optional[Dict[Literal["file_id"] | str, str]]:
        """分片上传文件

        参数:
            stage: 上传阶段
            name: 文件名
            total_size: 文件完整大小
            sha256: 整个文件的 SHA256 校验和，全小写
            file_id: 准备阶段返回的文件 ID
            offset: 本次传输的文件偏移，单位：字节
            size: 本次传输的文件大小，单位：字节
            data: 本次传输的文件数据
            kwargs: 扩展字段
        """
        ...
    async def get_file(
        self,
        *,
        type: Literal["url", "path", "data"] | str,
        file_id: str,
        **kwargs: Any,
    ) -> Dict[Literal["name", "url", "headers", "path", "data", "sha256"] | str, str]:
        """获取文件

        参数:
            type: 获取文件的方式，可以为 url、path、data 或扩展的方式
            file_id: 文件 ID
            kwargs: 扩展字段
        """
        ...
    async def get_file_fragmented(
        self,
        *,
        stage: Literal["prepare", "transfer"],
        file_id: str,
        offset: int = ...,
        size: int = ...,
        **kwargs: Any,
    ) -> Dict[Literal["name", "total_size", "sha256", "data"] | str, str]:
        """分片获取文件

        参数:
            stage: 获取阶段
            file_id: 文件 ID
            offset: 本次获取的文件偏移，单位：字节
            size: 本次获取的文件大小，单位：字节
            kwargs: 扩展字段
        """
        ...
