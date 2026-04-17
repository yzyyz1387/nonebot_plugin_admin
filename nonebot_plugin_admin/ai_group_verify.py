# python3
# -*- coding: utf-8 -*-
# @Time    : 2026/02/05
# @Author  : AI_Assistant
# @File    : ai_group_verify.py
# @Software: PyCharm

import json
import re
from pathlib import Path
from typing import Optional, Dict

import httpx
import nonebot
from nonebot import on_command, on_request, logger
from nonebot.adapters.onebot.v11 import Bot, GroupRequestEvent, GroupMessageEvent
# 【修正点1】从 adapter 导入群组权限，从 nonebot 导入超管权限
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from nonebot.matcher import Matcher

from .config import plugin_config

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None
    logger.warning("未安装 openai 库，AI 鉴权功能将不可用。")

# 【修正点2】使用你指定的数据路径方式
from .path import *
# 确保 config 目录存在 (基于运行目录的 config 文件夹)
DATA_DIR = config_path = Path() / 'config'
CONFIG_FILE = DATA_DIR / "ai_verify_config.json"

# --- 独立的配置读取逻辑 ---
driver = nonebot.get_driver()
global_config = driver.config

# 读取 .env 配置
AI_API_KEY = getattr(global_config, "ai_verify_api_key", "")
AI_BASE_URL = getattr(global_config, "ai_verify_base_url", "https://api.deepseek.com") 
AI_MODEL_NAME = getattr(global_config, "ai_verify_model", "deepseek-chat") 


def load_config() -> Dict:
    # 确保父目录存在
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(data: Dict):
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def _build_ai_http_client_kwargs() -> Dict:
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

# --- AI 请求核心逻辑 ---
async def _check_is_ad_bot(comment: str, custom_prompt: str = "") -> bool:
    """
    使用 AI 判断是否为广告/人机
    返回 True  -> 是确定的广告/人机（直接拒绝）
    返回 False -> 可能是真人/无法确定（放行，交给人工处理）
    """
    if not comment:
        return True # 空消息直接视为可疑

    if AsyncOpenAI is None or not AI_API_KEY:
        return False

    try:
        async with httpx.AsyncClient(**_build_ai_http_client_kwargs()) as http_client:
            client = AsyncOpenAI(
                api_key=AI_API_KEY,
                base_url=AI_BASE_URL,
                http_client=http_client,
            )

            # 宽松模式 Prompt：只拦截确定的广告，真人放行
            system_prompt = (
                "你是一个QQ群的防火墙。你的唯一任务是【拦截广告机器人】。"
                "\n\n请按以下逻辑判断用户发送的验证消息："
                "\n1. 【必须拦截】(返回 True)："
                "\n   - 明显的广告推销（兼职、卖课、刷单等）。"
                "\n   - 毫无意义的通用请求（如“通过一下”、“进群交流”、“朋友推荐”、“你好”，“趣味相投谢谢了”，“同意一下，谢谢啦！！！”等等），且不包含任何具体个人信息。"
                "\n   - 看起来像机器生成的乱码或重复字符。"
                "\n"
                "\n2. 【必须放行】(返回 False)："
                "\n   - 看起来像真人说的话。"
                "\n   - 有些同学群包含具体的年级、专业、姓名、学号等信息（即使格式不规范）。"
                "\n   - 有些兴趣群包含具体加群来源，如抖音、b站、某网站、xxx看到的之类的（即使格式不规范）。"
                "\n   - 哪怕用户没有完全遵守群规格式，只要他不像广告机器人，就都放行。"
            )

            if custom_prompt:
                system_prompt += (
                    f"\n\n【参考信息】：\n"
                    f"本群建议的验证格式是：{custom_prompt}\n"
                    f"注意：如果用户尝试回答了这些信息，即使回答得不完美，也请判定为【放行】(False)。"
                    f"只有当用户完全无视这些问题，直接发送广告或通用话术时，才判定为【拦截】(True)。"
                )
            
            system_prompt += "\n\n请只回答 'True' (代表是广告/拦截) 或 'False' (代表不是广告/放行)，不要包含任何标点符号或其他文字。"

            response = await client.chat.completions.create(
                model=AI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"验证消息内容：{comment}"}
                ],
                temperature=0.1, 
            )

        result = response.choices[0].message.content.strip()
        logger.info(f"AI 鉴权结果: {result} | 原始内容: {comment}")
        
        return "True" in result

    except Exception as e:
        logger.error(f"AI 鉴权调用失败: {e}")
        return False # 报错时默认放行

# --- 指令处理 ---

ai_switch = on_command("ai拒绝", priority=5, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)

@ai_switch.handle()
async def _(event: GroupMessageEvent):
    msg = event.get_plaintext().strip().lower()
    gid = str(event.group_id)
    config = load_config()
    
    if gid not in config:
        config[gid] = {"enabled": False, "prompt": ""}

    if "开" in msg:
        config[gid]["enabled"] = True
        save_config(config)
        await ai_switch.finish(f"本群 AI 自动拒绝广告账号功能已【开启】。")
    elif "关" in msg:
        config[gid]["enabled"] = False
        save_config(config)
        await ai_switch.finish(f"本群 AI 自动拒绝广告账号功能已【关闭】。")
    else:
        await ai_switch.finish("指令错误，请发送：ai拒绝开 / ai拒绝关")

ai_prompt_set = on_command("ai拒绝prompt", priority=5, block=True, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)

@ai_prompt_set.handle()
async def _(event: GroupMessageEvent, state: T_State):
    args = str(state["_prefix"]["command_arg"]).strip()
    gid = str(event.group_id)
    config = load_config()

    if gid not in config:
        config[gid] = {"enabled": False, "prompt": ""}

    if args:
        config[gid]["prompt"] = args
        save_config(config)
        await ai_prompt_set.finish(f"设置成功！\nAI 将参考以下规则拦截广告（真人未按格式填写不会被拦截）：\n{args}")
    else:
        config[gid]["prompt"] = ""
        save_config(config)
        await ai_prompt_set.finish("已清除自定义规则，仅拦截通用广告。")

# --- 事件监听：加群请求 ---
# 优先级 1，先于 requests.py 运行
ai_req_check = on_request(priority=1, block=False) 

@ai_req_check.handle()
async def _(bot: Bot, event: GroupRequestEvent, matcher: Matcher):
    # 只处理加群请求
    if event.sub_type != "add":
        return

    gid = str(event.group_id)
    config = load_config()

    # 没开功能直接跳过
    if gid not in config or not config[gid].get("enabled", False):
        return 

    comment = event.comment
    word_match = re.findall(re.compile('答案：(.*)'), comment)
    actual_msg = word_match[0] if word_match else comment
    
    custom_rule = config[gid].get("prompt", "")

    # 调用 AI 判断
    is_spam = await _check_is_ad_bot(actual_msg, custom_rule)

    if is_spam:
        # 情况1：AI 认定是广告 -> 直接拒绝，并拦截事件
        logger.info(f"群 {gid} [AI拦截] 广告/人机请求，用户: {event.user_id}, 验证消息: {actual_msg}")
        await bot.set_group_add_request(
            flag=event.flag,
            sub_type=event.sub_type,
            approve=False,
            reason="[AI安全拦截] 您的验证消息被判定为广告或无效请求。"
        )
        matcher.stop_propagation() # 停止传播，不让 requests.py 处理
    else:
        # 情况2：AI 认为是真人（或者不确定） -> 放行
        logger.info(f"群 {gid} [AI放行] 判定为非广告，转交人工/后续逻辑。验证消息: {actual_msg}")
        # 不做任何操作，让 requests.py 继续
