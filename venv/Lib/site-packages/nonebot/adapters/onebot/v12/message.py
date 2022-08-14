"""OneBot v12 消息类型。

FrontMatter:
    sidebar_position: 5
    description: onebot.v12.message 模块
"""

from typing import Any, Type, Iterable

from nonebot.typing import overrides

from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment


class MessageSegment(BaseMessageSegment["Message"]):
    """OneBot v12 协议 MessageSegment 适配。具体方法参考协议消息段类型或源码。"""

    @classmethod
    @overrides(BaseMessageSegment)
    def get_message_class(cls) -> Type["Message"]:
        return Message

    @overrides(BaseMessageSegment)
    def __str__(self) -> str:
        if self.type == "text":
            return self.data.get("text", "")
        params = ",".join(
            [f"{k}={str(v)}" for k, v in self.data.items() if v is not None]
        )
        return f"[{self.type}:{params}]"

    @overrides(BaseMessageSegment)
    def is_text(self) -> bool:
        return self.type == "text"

    @staticmethod
    def text(text: str, **kwargs) -> "MessageSegment":
        return MessageSegment("text", {**kwargs, "text": text})

    @staticmethod
    def mention(user_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("mention", {**kwargs, "user_id": user_id})

    @staticmethod
    def mention_all(**kwargs) -> "MessageSegment":
        return MessageSegment("mention_all", {**kwargs})

    @staticmethod
    def image(file_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("image", {**kwargs, "file_id": file_id})

    @staticmethod
    def voice(file_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("voice", {**kwargs, "file_id": file_id})

    @staticmethod
    def audio(file_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("audio", {**kwargs, "file_id": file_id})

    @staticmethod
    def video(file_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("video", {**kwargs, "file_id": file_id})

    @staticmethod
    def file(file_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("file", {**kwargs, "file_id": file_id})

    @staticmethod
    def location(
        latitude: float,
        longitude: float,
        title: str,
        content: str,
        **kwargs,
    ) -> "MessageSegment":
        return MessageSegment(
            "location",
            {
                **kwargs,
                "latitude": latitude,
                "longitude": longitude,
                "title": title,
                "content": content,
            },
        )

    @staticmethod
    def reply(message_id: str, **kwargs: Any) -> "MessageSegment":
        return MessageSegment("reply", {**kwargs, "message_id": message_id})


class Message(BaseMessage[MessageSegment]):
    @classmethod
    @overrides(BaseMessage)
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

    @staticmethod
    @overrides(BaseMessage)
    def _construct(msg: str) -> Iterable[MessageSegment]:
        yield MessageSegment.text(msg)

    @overrides(BaseMessage)
    def extract_plain_text(self) -> str:
        return "".join(seg.data["text"] for seg in self if seg.is_text())

    def ruduce(self) -> None:
        index = 1
        while index < len(self):
            if self[index - 1].type == "text" and self[index].type == "text":
                self[index - 1].data["text"] += self[index].data["text"]
                del self[index]
            else:
                index += 1
