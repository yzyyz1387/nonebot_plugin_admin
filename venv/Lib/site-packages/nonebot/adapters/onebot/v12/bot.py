"""OneBot v12 机器人定义。

FrontMatter:
    sidebar_position: 3
    description: onebot.v12.bot 模块
"""

import re
from typing import Any, Union, Callable

from nonebot.typing import overrides
from nonebot.message import handle_event

from nonebot.adapters import Bot as BaseBot

from .utils import log
from .message import Message, MessageSegment
from .event import Event, Reply, MessageEvent


def _check_reply(bot: "Bot", event: MessageEvent) -> None:
    """检查消息中存在的回复，去除并赋值 `event.reply`, `event.to_me`。

    参数:
        bot: Bot 对象
        event: MessageEvent 对象
    """
    try:
        index = list(map(lambda x: x.type == "reply", event.message)).index(True)
    except ValueError:
        return

    msg_seg = event.message[index]

    try:
        event.reply = Reply.parse_obj(msg_seg.data)
        # event.reply = Reply.parse_obj(
        #     await bot.get_msg(message_id=msg_seg.data["id"])
        # )
    except Exception as e:
        log("WARNING", f"Error when getting message reply info: {repr(e)}", e)
        return

    # ensure string comparation
    if str(event.reply.user_id) == str(event.self_id):
        event.to_me = True

    del event.message[index]
    if len(event.message) > index and event.message[index].type == "mention":
        del event.message[index]
    if len(event.message) > index and event.message[index].type == "text":
        event.message[index].data["text"] = event.message[index].data["text"].lstrip()
        if not event.message[index].data["text"]:
            del event.message[index]
    if not event.message:
        event.message.append(MessageSegment.text(""))


def _check_to_me(bot: "Bot", event: MessageEvent) -> None:
    """检查消息开头或结尾是否存在 @机器人，去除并赋值 `event.to_me`。

    参数:
        bot: Bot 对象
        event: MessageEvent 对象
    """
    if not isinstance(event, MessageEvent):
        return

    # ensure message not empty
    if not event.message:
        event.message.append(MessageSegment.text(""))

    if event.detail_type == "private":
        event.to_me = True
    else:

        def _is_mention_me_seg(segment: MessageSegment) -> bool:
            return (
                segment.type == "mention"
                and str(segment.data.get("user_id", "")) == event.self_id
            )

        # check the first segment
        if _is_mention_me_seg(event.message[0]):
            event.to_me = True
            event.message.pop(0)
            if event.message and event.message[0].type == "text":
                event.message[0].data["text"] = event.message[0].data["text"].lstrip()
                if not event.message[0].data["text"]:
                    del event.message[0]
            if event.message and _is_mention_me_seg(event.message[0]):
                event.message.pop(0)
                if event.message and event.message[0].type == "text":
                    event.message[0].data["text"] = (
                        event.message[0].data["text"].lstrip()
                    )
                    if not event.message[0].data["text"]:
                        del event.message[0]

        if not event.to_me:
            # check the last segment
            i = -1
            last_msg_seg = event.message[i]
            if (
                last_msg_seg.type == "text"
                and not last_msg_seg.data["text"].strip()
                and len(event.message) >= 2
            ):
                i -= 1
                last_msg_seg = event.message[i]

            if _is_mention_me_seg(last_msg_seg):
                event.to_me = True
                del event.message[i:]

        if not event.message:
            event.message.append(MessageSegment.text(""))


def _check_nickname(bot: "Bot", event: MessageEvent) -> None:
    """检查消息开头是否存在昵称，去除并赋值 `event.to_me`。

    参数:
        bot: Bot 对象
        event: MessageEvent 对象
    """
    first_msg_seg = event.message[0]
    if first_msg_seg.type != "text":
        return

    first_text = first_msg_seg.data["text"]

    nicknames = set(filter(lambda n: n, bot.config.nickname))
    if nicknames:
        # check if the user is calling me with my nickname
        nickname_regex = "|".join(nicknames)
        m = re.search(rf"^({nickname_regex})([\s,，]*|$)", first_text, re.IGNORECASE)
        if m:
            nickname = m.group(1)
            log("DEBUG", f"User is calling me {nickname}")
            event.to_me = True
            first_msg_seg.data["text"] = first_text[m.end() :]


async def send(
    bot: "Bot",
    event: Event,
    message: Union[str, Message, MessageSegment],
    at_sender: bool = False,
    reply_message: bool = False,
    **params: Any,
) -> Any:
    """默认回复消息处理函数。"""
    event_dict = event.dict()

    params.setdefault("detail_type", event_dict["detail_type"])

    if "user_id" in event_dict:  # copy the user_id to the API params if exists
        params.setdefault("user_id", event_dict["user_id"])
    else:
        at_sender = False  # if no user_id, force disable at_sender

    if "group_id" in event_dict:  # copy the group_id to the API params if exists
        params.setdefault("group_id", event_dict["group_id"])

    if (
        "guild_id" in event_dict and "channel_id" in event_dict
    ):  # copy the guild_id to the API params if exists
        params.setdefault("guild_id", event_dict["guild_id"])
        params.setdefault("channel_id", event_dict["channel_id"])

    full_message = Message()  # create a new message with at sender segment
    if reply_message and "message_id" in event_dict:
        full_message += MessageSegment.reply(event_dict["message_id"])
    if at_sender and params["detail_type"] != "private":
        full_message += MessageSegment.mention(params["user_id"]) + " "
    full_message += message
    params.setdefault("message", full_message)

    return await bot.send_message(**params)


class Bot(BaseBot):

    send_handler: Callable[
        ["Bot", Event, Union[str, Message, MessageSegment]], Any
    ] = send

    async def handle_event(self, event: Event) -> None:
        """处理收到的事件。"""
        if isinstance(event, MessageEvent):
            _check_reply(self, event)
            _check_to_me(self, event)
            _check_nickname(self, event)
        await handle_event(self, event)

    @overrides(BaseBot)
    async def send(
        self, event: Event, message: Union[str, Message, MessageSegment], **kwargs: Any
    ) -> Any:
        """根据 `event` 向触发事件的主体回复消息。

        参数:
            event: Event 对象
            message: 要发送的消息
            at_sender (bool): 是否 @ 事件主体
            reply_message (bool): 是否回复事件消息
            kwargs: 其他参数，可以与 {ref}`nonebot.adapters.onebot.v12.adapter.Adapter.custom_send` 配合使用

        返回:
            API 调用返回数据

        异常:
            ValueError: 缺少 `user_id`, `group_id`
            NetworkError: 网络错误
            ActionFailed: API 调用失败
        """
        return await self.__class__.send_handler(self, event, message, **kwargs)
