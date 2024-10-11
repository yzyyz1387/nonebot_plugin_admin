import re
from typing import Union

from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent

async def msg_text(event: GroupMessageEvent) -> str:
    return event.get_plaintext()

async def msg_text_no_url(event: GroupMessageEvent) -> str:
    msg = event.get_plaintext()
    no_url = re.sub(r'https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]', '', msg)
    return re.sub(r'\s+', '', no_url)

async def msg_img(event: GroupMessageEvent) -> list:
    img = []
    for msg in event.message:
        if msg.type in ['image', 'mface']:
            img.append(msg.data['url'])
    return img

async def msg_raw(bot: Bot, event: GroupMessageEvent) -> str:
    raw = event.raw_message
    for msg in event.message:
        if msg.type in ['image', 'mface']:
            if msg.type == 'image':
                try:
                    res = await bot.call_api(api='ocr_image', image=msg.data['url'])
                    raw = raw.replace(str(msg), ' ' + ' '.join([i['text'] for i in res['texts']]) + ' ', 1)
                    continue
                except Exception:
                    pass
            raw = raw.replace(str(msg), ' ' + msg.data['url'] + ' ', 1)
        elif msg.type == 'forward':  # 合并转发不可能与其他消息结合
            try:
                forward = await bot.get_forward_msg(id=msg.data['id'])
                return ' '.join([i['raw_message'] for i in forward['messages']])
            except Exception:
                break
    return raw

async def msg_at(event: GroupMessageEvent) -> list:
    qq = []
    for msg in event.message:
        if msg.type == 'at':
            qq.append(msg.data['qq'])
    return qq

async def msg_reply(event: GroupMessageEvent) -> Union[int, None]:
    return event.reply.message_id if event.reply else None
