# python3
# -*- coding: utf-8 -*-

import re
from typing import Dict

import httpx
import nonebot
from nonebot import logger, on_command, on_request
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GroupRequestEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from . import ai_verify_store
from ..core.config import plugin_config
from ..core.state_feedback import build_explicit_state_message
from ..dashboard.dashboard_oplog_service import record_oplog

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None
    logger.warning("未安装 openai 库，AI 鉴权功能将不可用。")


driver = nonebot.get_driver()
global_config = driver.config

AI_API_KEY = getattr(global_config, "ai_verify_api_key", "")
AI_BASE_URL = getattr(global_config, "ai_verify_base_url", "https://api.deepseek.com")
AI_MODEL_NAME = getattr(global_config, "ai_verify_model", "deepseek-chat")
AI_VERIFY_ENABLE_COMMAND = "ai拒绝开"
AI_VERIFY_DISABLE_COMMAND = "ai拒绝关"
AI_VERIFY_FEATURE_NAME = "AI 自动拒绝广告账号"


async def load_config() -> Dict:
    """
    加载配置
    :return: Dict
    """
    return await ai_verify_store.load_config()


async def save_config(data: Dict):
    """
    保存配置
    :param data: 数据对象
    :return: None
    """
    await ai_verify_store.save_config(data)


async def _ensure_group_config(gid: str) -> Dict:
    """
    确保群配置
    :param gid: 群号
    :return: Dict
    """
    config = await load_config()
    if gid not in config:
        config[gid] = {"enabled": False, "prompt": ""}
    return config


def _build_ai_http_client_kwargs() -> Dict:
    """
    构建aihttpclientkwargs
    :return: Dict
    """
    kwargs: Dict = {
        "timeout": httpx.Timeout(60.0, connect=20.0),
    }
    proxy = (plugin_config.ai_verify_proxy or "").strip()
    use_proxy = plugin_config.ai_verify_use_proxy

    if use_proxy:
        if proxy:
            kwargs["proxy"] = proxy
            kwargs["trust_env"] = False
            logger.info(f"AI 鉴权请求将使用代理: {proxy}")
        else:
            logger.info("AI 鉴权请求已启用代理模式，但未配置代理地址，将沿用系统网络环境")
    else:
        kwargs["trust_env"] = False
        logger.info("AI 鉴权请求已禁用代理")

    return kwargs


async def _check_is_ad_bot(comment: str, custom_prompt: str = "") -> str:
    """
    使用 AI 判断是否为广告/人机
    返回 "True"  -> 是确定的广告/人机（直接拒绝）
    返回 "False" -> 可能是真人/无法确定（放行，交给人工处理）
    返回 "Agree" -> 确定是真人且符合条件（直接同意入群，仅自定义 prompt 下可能返回）
    """
    if not comment:
        return "True"

    if AsyncOpenAI is None or not AI_API_KEY:
        return "False"

    try:
        async with httpx.AsyncClient(**_build_ai_http_client_kwargs()) as http_client:
            client = AsyncOpenAI(
                api_key=AI_API_KEY,
                base_url=AI_BASE_URL,
                http_client=http_client,
            )

            system_prompt = (
                '你是一个QQ群的防火墙。你的唯一任务是【拦截广告机器人】。'
                '\n\n请按以下逻辑判断用户发送的验证消息：'
                '\n1. 【必须拦截】(返回 True)：'
                '\n   - 明显的广告推销（兼职、卖课、刷单等）。'
                '\n   - 毫无意义的通用请求（如\u201c通过一下\u201d、\u201c进群交流\u201d、\u201c朋友推荐\u201d、\u201c你好\u201d，\u201c趣味相投谢谢了\u201d，\u201c同意一下，谢谢啦！！！\u201d等等），且不包含任何具体个人信息。'
                '\n   - 看起来像机器生成的乱码或重复字符。'
                '\n'
                '\n2. 【必须放行】(返回 False)：'
                '\n   - 看起来像真人说的话。'
                '\n   - 有些同学群包含具体的年级、专业、姓名、学号等信息（即使格式不规范）。'
                '\n   - 有些兴趣群包含具体加群来源，如抖音、b站、某网站、xxx看到的之类的（即使格式不规范）。'
                '\n   - 哪怕用户没有完全遵守群规格式，只要他不像广告机器人，就都放行。'
            )

            if custom_prompt:
                system_prompt += (
                    f'\n\n【参考信息】：\n'
                    f'{custom_prompt}\n\n'
                    f'判断规则：\n'
                    f'- 如果用户回答符合上述参考信息中的条件（即使不完全准确），请返回 Agree（直接同意入群）。\n'
                    f'- 如果用户看起来像真人但回答不符合条件，请返回 False（放行给管理员处理）。\n'
                    f'- 只有当用户明显是广告/人机时，才返回 True（拒绝）。\n'
                )
                system_prompt += "\n\n请只回答 'True'（拦截）、'False'（放行）或 'Agree'（直接同意），不要包含任何标点符号或其他文字。"
            else:
                system_prompt += "\n\n请只回答 'True' (代表是广告/拦截) 或 'False' (代表不是广告/放行)，不要包含任何标点符号或其他文字。"

            response = await client.chat.completions.create(
                model=AI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"验证消息内容：{comment}"},
                ],
                temperature=0.1,
            )

        result = response.choices[0].message.content.strip()
        logger.info(f"AI 鉴权结果: {result} | 原始内容: {comment}")

        if "Agree" in result:
            return "Agree"
        if "True" in result:
            return "True"
        return "False"

    except Exception as e:
        logger.error(f"AI 鉴权调用失败: {e}")
        return "False"


ai_switch = on_command("ai拒绝", priority=5, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@ai_switch.handle()
async def _(event: GroupMessageEvent):
    gid = str(event.group_id)
    msg = event.get_plaintext().strip().lower()
    config = await _ensure_group_config(gid)

    if "开" in msg:
        if not config[gid].get("enabled", False):
            config[gid]["enabled"] = True
            await save_config(config)
        await ai_switch.finish(
            build_explicit_state_message(
                AI_VERIFY_FEATURE_NAME,
                enabled=True,
                enable_command=AI_VERIFY_ENABLE_COMMAND,
                disable_command=AI_VERIFY_DISABLE_COMMAND,
            )
        )
    elif "关" in msg:
        if config[gid].get("enabled", False):
            config[gid]["enabled"] = False
            await save_config(config)
        await ai_switch.finish(
            build_explicit_state_message(
                AI_VERIFY_FEATURE_NAME,
                enabled=False,
                enable_command=AI_VERIFY_ENABLE_COMMAND,
                disable_command=AI_VERIFY_DISABLE_COMMAND,
            )
        )
    else:
        await ai_switch.finish("指令错误，请发送：ai拒绝开 / ai拒绝关")


ai_prompt_set = on_command("ai拒绝prompt", priority=5, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@ai_prompt_set.handle()
async def _(event: GroupMessageEvent, state: T_State):
    args = str(state["_prefix"]["command_arg"]).strip()
    gid = str(event.group_id)
    config = await _ensure_group_config(gid)

    if args:
        config[gid]["prompt"] = args
        await save_config(config)
        await ai_prompt_set.finish(
            f"设置成功！\n"
            f"AI 将参考以下规则进行判断：\n"
            f"- 符合条件的回答 → 直接同意入群（Agree）\n"
            f"- 看起来像真人但不符合条件 → 放行给管理员处理（False）\n"
            f"- 广告/人机 → 拒绝（True）\n\n"
            f"自定义规则：{args}"
        )
    else:
        config[gid]["prompt"] = ""
        await save_config(config)
        await ai_prompt_set.finish("已清除自定义规则，仅拦截通用广告（True/False 二级判断）。")


ai_req_check = on_request(priority=1, block=False)


@ai_req_check.handle()
async def _(bot: Bot, event: GroupRequestEvent, matcher: Matcher):
    if event.sub_type != "add":
        return

    gid = str(event.group_id)
    config = await load_config()
    if gid not in config or not config[gid].get("enabled", False):
        return

    comment = event.comment
    word_match = re.findall(re.compile("答案：(.*)"), comment)
    actual_msg = word_match[0] if word_match else comment
    custom_rule = config[gid].get("prompt", "")

    ai_result = await _check_is_ad_bot(actual_msg, custom_rule)

    if ai_result == "True":
        logger.info(f"群 {gid} [AI拦截] 广告/人机请求，用户: {event.user_id}, 验证消息: {actual_msg}")
        await record_oplog(
            action="ai_approval",
            group_id=gid,
            user_id=str(event.user_id),
            detail=f"AI拦截广告/人机，验证消息: {actual_msg[:60]}{'...' if len(actual_msg) > 60 else ''}",
            extra={"result": "rejected", "comment": actual_msg[:200]},
        )
        await bot.set_group_add_request(
            flag=event.flag,
            sub_type=event.sub_type,
            approve=False,
            reason="[AI安全拦截] 您的验证消息被判定为广告或无效请求。",
        )
        matcher.stop_propagation()
    elif ai_result == "Agree":
        logger.info(f"群 {gid} [AI直接同意] 判定为符合条件，用户: {event.user_id}, 验证消息: {actual_msg}")
        await record_oplog(
            action="ai_approval",
            group_id=gid,
            user_id=str(event.user_id),
            detail=f"AI直接同意入群，验证消息: {actual_msg[:60]}{'...' if len(actual_msg) > 60 else ''}",
            extra={"result": "agreed", "comment": actual_msg[:200]},
        )
        await bot.set_group_add_request(
            flag=event.flag,
            sub_type=event.sub_type,
            approve=True,
            reason=" ",
        )
        try:
            await bot.send_group_msg(
                group_id=int(gid),
                message=f"入群审核：用户 {event.user_id} 验证消息：{actual_msg}\n机器人已自动放行。",
            )
        except Exception as e:
            logger.warning(f"AI同意入群后群内通知发送失败: {e}")
        matcher.stop_propagation()
    else:
        logger.info(f"群 {gid} [AI放行] 判定为非广告，转交人工/后续逻辑。验证消息: {actual_msg}")
        await record_oplog(
            action="ai_approval",
            group_id=gid,
            user_id=str(event.user_id),
            detail=f"AI放行，验证消息: {actual_msg[:60]}{'...' if len(actual_msg) > 60 else ''}",
            extra={"result": "passed", "comment": actual_msg[:200]},
        )
