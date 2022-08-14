"""OneBot v12 协议适配。

协议详情请看: [OneBot V12](https://12.1bot.dev/)

FrontMatter:
    sidebar_position: 0
    description: onebot.v12 模块
"""

from .event import *
from .exception import *
from .permission import *
from .bot import Bot as Bot
from .utils import log as log
from .adapter import Adapter as Adapter
from .message import Message as Message
from .message import MessageSegment as MessageSegment
