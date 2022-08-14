"""OneBot v12 适配器。

FrontMatter:
    sidebar_position: 1
    description: onebot.v12.adapter 模块
"""

import json
import asyncio
import inspect
import contextlib
from typing import Any, Dict, List, Type, Union, Callable, Optional, Generator, cast

import msgpack
from pygtrie import CharTrie
from nonebot.typing import overrides
from nonebot.utils import escape_tag
from nonebot.exception import WebSocketClosed
from nonebot.drivers import (
    URL,
    Driver,
    Request,
    Response,
    WebSocket,
    ForwardDriver,
    ReverseDriver,
    HTTPServerSetup,
    WebSocketServerSetup,
)

from nonebot.adapters import Adapter as BaseAdapter
from nonebot.adapters.onebot.collator import Collator
from nonebot.adapters.onebot.store import ResultStore
from nonebot.adapters.onebot.utils import get_auth_bearer

from .bot import Bot
from .event import Event
from .config import Config
from . import event, exception
from .message import Message, MessageSegment
from .utils import CustomEncoder, log, flattened_to_nested
from .exception import (
    NetworkError,
    ApiNotAvailable,
    ActionMissingField,
    ActionFailedWithRetcode,
)

RECONNECT_INTERVAL = 3.0
COLLATOR_KEY = ("type", "detail_type", "sub_type")
DEFAULT_MODELS: List[Type[Event]] = []
for model_name in dir(event):
    model = getattr(event, model_name)
    if not inspect.isclass(model) or not issubclass(model, Event):
        continue
    DEFAULT_MODELS.append(model)

DEFAULT_EXCEPTIONS: List[Type[ActionFailedWithRetcode]] = []
for exc_name in dir(exception):
    Exc = getattr(exception, exc_name)
    if not inspect.isclass(Exc) or not issubclass(Exc, ActionFailedWithRetcode):
        continue
    DEFAULT_EXCEPTIONS.append(Exc)


class Adapter(BaseAdapter):

    event_models: Dict[str, Collator[Event]] = {
        "": Collator(
            "OneBot V12",
            DEFAULT_MODELS,
            COLLATOR_KEY,
        )
    }

    exc_classes: CharTrie = CharTrie(
        (retcode, Exc) for Exc in DEFAULT_EXCEPTIONS for retcode in Exc.__retcode__
    )

    _result_store = ResultStore()

    @classmethod
    @overrides(BaseAdapter)
    def get_name(cls) -> str:
        return "OneBot V12"

    @overrides(BaseAdapter)
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)
        self.onebot_config: Config = Config(**self.config.dict())
        self.connections: Dict[str, WebSocket] = {}
        self.tasks: List["asyncio.Task"] = []
        self._setup()

    def _setup(self) -> None:
        if isinstance(self.driver, ReverseDriver):
            self.setup_http_server(
                HTTPServerSetup(
                    URL("/onebot/v12/"),
                    "POST",
                    self.get_name(),
                    self._handle_http,
                )
            )
            self.setup_http_server(
                HTTPServerSetup(
                    URL("/onebot/v12/http"),
                    "POST",
                    self.get_name(),
                    self._handle_http,
                )
            )
            self.setup_http_server(
                HTTPServerSetup(
                    URL("/onebot/v12/http/"),
                    "POST",
                    self.get_name(),
                    self._handle_http,
                )
            )
            self.setup_websocket_server(
                WebSocketServerSetup(
                    URL("/onebot/v12/"), self.get_name(), self._handle_ws
                )
            )
            self.setup_websocket_server(
                WebSocketServerSetup(
                    URL("/onebot/v12/ws"), self.get_name(), self._handle_ws
                )
            )
            self.setup_websocket_server(
                WebSocketServerSetup(
                    URL("/onebot/v12/ws/"), self.get_name(), self._handle_ws
                )
            )
        if self.onebot_config.onebot_ws_urls:
            if not isinstance(self.driver, ForwardDriver):
                log(
                    "WARNING",
                    f"Current driver {self.config.driver} don't support forward connections! Ignored",
                )
            else:
                self.driver.on_startup(self._start_forward)
                self.driver.on_shutdown(self._stop_forward)

    @overrides(BaseAdapter)
    async def _call_api(self, bot: Bot, api: str, **data: Any) -> Any:
        websocket = self.connections.get(bot.self_id, None)
        timeout: float = data.get("_timeout", self.config.api_timeout)
        log("DEBUG", f"Calling API <y>{api}</y>")

        if websocket:
            seq = self._result_store.get_seq()
            json_data = json.dumps(
                {"action": api, "params": data, "echo": str(seq)},
                cls=CustomEncoder,
            )
            await websocket.send(json_data)
            try:
                return self._handle_api_result(
                    await self._result_store.fetch(bot.self_id, seq, timeout)
                )
            except asyncio.TimeoutError:
                raise NetworkError(f"WebSocket call api {api} timeout") from None

        elif isinstance(self.driver, ForwardDriver):
            api_url = self.onebot_config.onebot_api_roots.get(bot.self_id)
            if not api_url:
                raise ApiNotAvailable

            headers = {"Content-Type": "application/json"}
            if self.onebot_config.onebot_access_token is not None:
                headers["Authorization"] = (
                    "Bearer " + self.onebot_config.onebot_access_token
                )

            request = Request(
                "POST",
                api_url,
                headers=headers,
                timeout=timeout,
                content=json.dumps({"action": api, "params": data}, cls=CustomEncoder),
            )

            try:
                response = await self.driver.request(request)

                if 200 <= response.status_code < 300:
                    if not response.content:
                        raise ValueError("Empty response")
                    result = json.loads(response.content)
                    return self._handle_api_result(result)
                raise NetworkError(
                    f"HTTP request received unexpected "
                    f"status code: {response.status_code}"
                )
            except NetworkError:
                raise
            except Exception as e:
                raise NetworkError("HTTP request failed") from e
        else:
            raise ApiNotAvailable

    def _handle_api_result(self, result: Any) -> Any:
        """处理 API 请求返回值。

        参数:
            result: API 返回数据

        返回:
            API 调用返回数据

        异常:
            ActionFailed: API 调用失败
        """
        if not isinstance(result, dict):
            raise ActionMissingField(result)
        elif not set(result.keys()).issuperset(
            {"status", "retcode", "data", "message"}
        ):
            raise ActionMissingField(result)

        if result["status"] == "failed":
            retcode = result["retcode"]
            if not isinstance(retcode, int):
                raise ActionMissingField(result)

            Exc = self.get_exception(retcode)

            raise Exc(**result)
        return result["data"]

    async def _handle_http(self, request: Request) -> Response:
        self_id = request.headers.get("x-self-id")

        # check self_id
        if not self_id:
            log("WARNING", "Missing X-Self-ID Header")
            return Response(400, content="Missing X-Self-ID Header")

        # check access_token
        response = self._check_access_token(request)
        if response is not None:
            return response

        data = request.content
        if data is not None:
            json_data = json.loads(data)
            event = self.json_to_event(json_data)
            if event:
                bot = self.bots.get(self_id, None)
                if not bot:
                    bot = Bot(self, self_id)
                    self.bot_connect(bot)
                    log("INFO", f"<y>Bot {escape_tag(self_id)}</y> connected")
                bot = cast(Bot, bot)
                asyncio.create_task(bot.handle_event(event))
        return Response(204)

    async def _handle_ws(self, websocket: WebSocket) -> None:
        self_id = websocket.request.headers.get("X-Self-Id")

        # check self_id
        if not self_id:
            log("WARNING", "Missing X-Self-ID Header")
            await websocket.close(1008, "Missing X-Self-ID Header")
            return
        elif self_id in self.bots:
            log("WARNING", f"There's already a bot {self_id}, ignored")
            await websocket.close(1008, "Duplicate X-Self-ID")
            return

        # check access_token
        response = self._check_access_token(websocket.request)
        if response is not None:
            content = cast(str, response.content)
            await websocket.close(1008, content)
            return

        await websocket.accept()
        bot = Bot(self, self_id)
        self.connections[self_id] = websocket
        self.bot_connect(bot)

        log("INFO", f"<y>Bot {escape_tag(self_id)}</y> connected")

        try:
            while True:
                data = await websocket.receive()
                raw_data = (
                    json.loads(data) if isinstance(data, str) else msgpack.unpackb(data)
                )
                event = self.json_to_event(raw_data, self_id)
                if event:
                    asyncio.create_task(bot.handle_event(event))
        except WebSocketClosed as e:
            log("WARNING", f"WebSocket for Bot {escape_tag(self_id)} closed by peer")
        except Exception as e:
            log(
                "ERROR",
                "<r><bg #f8bbd0>Error while process data from websocket "
                f"for bot {escape_tag(self_id)}.</bg #f8bbd0></r>",
                e,
            )

        finally:
            with contextlib.suppress(Exception):
                await websocket.close()
            self.connections.pop(self_id, None)
            self.bot_disconnect(bot)

    def _check_access_token(self, request: Request) -> Optional[Response]:
        token = get_auth_bearer(request.headers.get("Authorization"))

        access_token = self.onebot_config.onebot_access_token
        if access_token and access_token != token:
            msg = (
                "Authorization Header is invalid"
                if token
                else "Missing Authorization Header"
            )
            log("WARNING", msg)
            return Response(403, content=msg)

    async def _start_forward(self) -> None:
        for url in self.onebot_config.onebot_ws_urls:
            try:
                ws_url = URL(url)
                self.tasks.append(asyncio.create_task(self._forward_ws(ws_url)))
            except Exception as e:
                log(
                    "ERROR",
                    f"<r><bg #f8bbd0>Bad url {escape_tag(url)} "
                    "in onebot forward websocket config</bg #f8bbd0></r>",
                    e,
                )

    async def _stop_forward(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()

    async def _forward_ws(self, url: URL) -> None:
        headers = {}
        if self.onebot_config.onebot_access_token:
            headers[
                "Authorization"
            ] = f"Bearer {self.onebot_config.onebot_access_token}"
        req = Request("GET", url, headers=headers, timeout=30.0)
        bot: Optional[Bot] = None
        while True:
            try:
                async with self.websocket(req) as ws:
                    log(
                        "DEBUG",
                        f"WebSocket Connection to {escape_tag(str(url))} established",
                    )
                    try:
                        while True:
                            data = await ws.receive()
                            raw_data = (
                                json.loads(data)
                                if isinstance(data, str)
                                else msgpack.unpackb(data)
                            )
                            event = self.json_to_event(raw_data, bot and bot.self_id)
                            if not event:
                                continue
                            if not bot:
                                self_id = event.self_id
                                bot = Bot(self, self_id)
                                self.connections[self_id] = ws
                                self.bot_connect(bot)
                                log(
                                    "INFO",
                                    f"<y>Bot {escape_tag(str(self_id))}</y> connected",
                                )
                            asyncio.create_task(bot.handle_event(event))
                    except WebSocketClosed as e:
                        log(
                            "ERROR",
                            "<r><bg #f8bbd0>WebSocket Closed</bg #f8bbd0></r>",
                            e,
                        )
                    except Exception as e:
                        log(
                            "ERROR",
                            "<r><bg #f8bbd0>Error while process data from websocket"
                            f"{escape_tag(str(url))}. Trying to reconnect...</bg #f8bbd0></r>",
                            e,
                        )
                    finally:
                        if bot:
                            self.connections.pop(bot.self_id, None)
                            self.bot_disconnect(bot)
                            bot = None

            except Exception as e:
                log(
                    "ERROR",
                    "<r><bg #f8bbd0>Error while setup websocket to "
                    f"{escape_tag(str(url))}. Trying to reconnect...</bg #f8bbd0></r>",
                    e,
                )

            await asyncio.sleep(RECONNECT_INTERVAL)

    @classmethod
    def add_custom_model(
        cls,
        *model: Type[Event],
        impl: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> None:
        if platform is not None and impl is None:
            raise ValueError("Impl must be specified")
        if impl is not None and platform is None:
            raise ValueError("platform must be specified")
        key = f"/{impl}/{platform}" if impl and platform else ""
        if key not in cls.event_models:
            cls.event_models[key] = Collator(
                "OneBot V12",
                [],
                COLLATOR_KEY,
            )
        cls.event_models[key].add_model(*model)  # type: ignore

    @classmethod
    def get_event_model(
        cls, data: Dict[str, Any]
    ) -> Generator[Type[Event], None, None]:
        """根据事件获取对应 `Event Model` 及 `FallBack Event Model` 列表。"""
        key = f"/{data.get('impl')}/{data.get('platform')}"
        if key in cls.event_models:
            yield from cls.event_models[key].get_model(data)
        yield from cls.event_models[""].get_model(data)

    @classmethod
    def add_custom_exception(cls, exc: Type[ActionFailedWithRetcode]):
        for retcode in exc.__retcode__:
            if retcode in cls.exc_classes:
                log(
                    "WARNING",
                    f"Exception for retcode {retcode} is is overridden by {exc}",
                )
            cls.exc_classes[retcode] = exc

    @classmethod
    def get_exception(cls, retcode: int) -> Type[ActionFailedWithRetcode]:
        if retcode < 100000:
            Exc = cls.exc_classes.longest_prefix(str(retcode).rjust(5, "0"))
            Exc = Exc.value if Exc else ActionFailedWithRetcode
        else:
            Exc = ActionFailedWithRetcode
        return Exc

    @classmethod
    def json_to_event(
        cls, json_data: Any, self_id: Optional[str] = None
    ) -> Optional[Event]:
        if not isinstance(json_data, dict):
            return None

        # transform flattened dict to nested
        json_data = flattened_to_nested(json_data)

        if "type" not in json_data:
            if self_id is not None:
                cls._result_store.add_result(self_id, json_data)
            return None

        try:
            for model in cls.get_event_model(json_data):
                try:
                    event = model.parse_obj(json_data)
                    break
                except Exception as e:
                    log("DEBUG", "Event Parse Error", e)
            else:
                event = Event.parse_obj(json_data)
            return event

        except Exception as e:
            log(
                "ERROR",
                "<r><bg #f8bbd0>Failed to parse event. "
                f"Raw: {str(json_data)}</bg #f8bbd0></r>",
                e,
            )
            return None

    @classmethod
    def custom_send(
        cls,
        send_func: Callable[[Bot, Event, Union[str, Message, MessageSegment]], Any],
    ):
        """自定义 Bot 的回复函数。"""
        setattr(Bot, "send_handler", send_func)
