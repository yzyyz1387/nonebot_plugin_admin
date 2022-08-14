"""OneBot v12 错误类型。

FrontMatter:
    sidebar_position: 7
    description: onebot.v12.exception 模块
"""

from typing import Any, Tuple, Optional

from nonebot.exception import AdapterException
from nonebot.exception import ActionFailed as BaseActionFailed
from nonebot.exception import NetworkError as BaseNetworkError
from nonebot.exception import NoLogException as BaseNoLogException
from nonebot.exception import ApiNotAvailable as BaseApiNotAvailable


class OneBotV12AdapterException(AdapterException):
    def __init__(self):
        super().__init__("OneBot V12")


class NoLogException(BaseNoLogException, OneBotV12AdapterException):
    pass


class NetworkError(BaseNetworkError, OneBotV12AdapterException):
    """网络错误。"""

    def __init__(self, msg: Optional[str] = None):
        super().__init__()
        self.msg: Optional[str] = msg
        """错误原因"""

    def __repr__(self):
        return f"<NetWorkError message={self.msg}>"

    def __str__(self):
        return self.__repr__()


class ApiNotAvailable(BaseApiNotAvailable, OneBotV12AdapterException):
    pass


class ActionFailed(BaseActionFailed, OneBotV12AdapterException):
    pass


class ActionMissingField(ActionFailed):
    """Action 返回数据缺少必要字段。"""

    def __init__(self, data: Any):
        super().__init__()
        self.data = data
        """Action 返回数据"""

    def __repr__(self):
        return f"<ActionMissingField data={self.data!r}>"

    def __str__(self):
        return self.__repr__()


class ActionFailedWithRetcode(ActionFailed):
    """API 请求返回错误信息。

    参数:
        status: 执行状态
        retcode: 错误码
        message: 错误信息
        data: 响应数据
        kwargs: 其他实现端提供信息
    """

    __retcode__: Tuple[str, ...] = ("",)

    def __init__(
        self, status: str, retcode: int, message: str, data: Any, **kwargs: Any
    ):
        super().__init__()
        self.status = status
        self.retcode = retcode
        self.message = message
        self.data = data
        self.extra = kwargs

    def __repr__(self):
        return (
            "<ActionFailed "
            + f"status={self.status!r}, "
            + f"retcode={self.retcode!r}, "
            + f"message={self.message!r}, "
            + f"data={self.data!r}"
            + "".join(f", {k}={v!r}" for k, v in self.extra.items())
            + ">"
        )

    def __str__(self):
        return self.__repr__()


# 1xxxx
class RequestError(ActionFailedWithRetcode):
    """动作请求错误。

    OneBot V12 协议错误码: 1xxxx。

    这种错误类型类似 HTTP 的 4xx 客户端错误。
    """

    __retcode__ = ("1",)


class BadRequest(RequestError):
    """无效的动作请求。

    OneBot V12 协议错误码: 10001。

    格式错误（包括实现不支持 MessagePack 的情况）、必要字段缺失或字段类型错误。
    """

    __retcode__ = ("10001",)


class UnsupportedAction(RequestError):
    """不支持的动作请求。

    OneBot V12 协议错误码: 10002。

    OneBot 实现没有实现该动作。
    """

    __retcode__ = ("10002",)


class BadParam(RequestError):
    """无效的动作请求参数。

    OneBot V12 协议错误码: 10003。

    参数缺失或参数类型错误。
    """

    __retcode__ = ("10003",)


class UnsupportedParam(RequestError):
    """不支持的动作请求参数。

    OneBot V12 协议错误码: 10004。

    OneBot 实现没有实现该参数的语义。
    """

    __retcode__ = ("10004",)


class UnsupportedSegment(RequestError):
    """不支持的消息段类型。

    OneBot V12 协议错误码: 10005。

    OneBot 实现没有实现该消息段类型。
    """

    __retcode__ = ("10005",)


class BadSegmentData(RequestError):
    """无效的消息段参数。

    OneBot V12 协议错误码: 10006。

    参数缺失或参数类型错误。
    """

    __retcode__ = ("10006",)


class UnsupportedSegmentData(RequestError):
    """不支持的消息段参数。

    OneBot V12 协议错误码: 10007。

    OneBot 实现没有实现该消息段参数的语义。
    """

    __retcode__ = ("10007",)


# 2xxxx
class HandlerError(ActionFailedWithRetcode):
    """动作处理器错误。

    OneBot V12 协议错误码: 2xxxx。

    这种错误类型类似 HTTP 的 5xx 服务端错误。
    """

    __retcode__ = ("2",)


class BadHandler(HandlerError):
    """动作处理器实现错误。

    OneBot V12 协议错误码: 20001。

    没有正确设置响应状态等。
    """

    __retcode__ = ("20001",)


class InternalHandlerError(HandlerError):
    """动作处理器运行时抛出异常。

    OneBot V12 协议错误码: 20002。

    OneBot 实现内部发生了未捕获的意料之外的异常。
    """

    __retcode__ = ("20002",)


# 3xxxx
class ExecutionError(ActionFailedWithRetcode):
    """动作请求有效，但动作执行失败。

    OneBot V12 协议错误码: 3xxxx。
    """

    __retcode__ = ("3",)


class DatabaseError(ExecutionError):
    """数据库错误。

    OneBot V12 协议错误码: 31xxx。

    如数据库查询失败等。
    """

    __retcode__ = ("31",)


class FileSystemError(ExecutionError):
    """文件系统错误。

    OneBot V12 协议错误码: 32xxx。

    如读取或写入文件失败等。
    """

    __retcode__ = ("32",)


class ExecNetworkError(ExecutionError):
    """网络错误。

    OneBot V12 协议错误码: 33xxx。

    如下载文件失败等。
    """

    __retcode__ = ("33",)


class PlatformError(ExecutionError):
    """机器人平台错误。

    OneBot V12 协议错误码: 34xxx。

    如由于机器人平台限制导致消息发送失败等。
    """

    __retcode__ = ("34",)


class LogicError(ExecutionError):
    """动作逻辑错误。

    OneBot V12 协议错误码: 35xxx。

    如尝试向不存在的用户发送消息等。
    """

    __retcode__ = ("35",)


class IAmTired(ExecutionError):
    """我不想干了。

    OneBot V12 协议错误码: 36xxx。

    一位 OneBot 实现决定罢工。
    """

    __retcode__ = ("36",)


# 6xxxx ~ 9xxxx
class ExtendedError(ActionFailedWithRetcode):
    """扩展错误。

    OneBot V12 协议错误码: 6xxxx ~ 9xxxx。
    """

    __retcode__ = ("6", "7", "8", "9")
