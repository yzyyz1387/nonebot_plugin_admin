from __future__ import annotations

from nonebot.matcher import Matcher

from . import ai_verify_store

AI_VERIFY_ENABLED_TEXT = "本群 AI审批已【开启】。"
AI_VERIFY_DISABLED_TEXT = "本群 AI审批已【关闭】。"
AI_VERIFY_INVALID_TEXT = "指令错误，请发送：开关AI审批 或 ai拒绝开 / ai拒绝关"
AI_VERIFY_PROMPT_CLEARED_TEXT = "已清除自定义规则，仅拦截通用广告。"


async def _ensure_group_config(gid: str) -> dict:
    """
    确保群配置
    :param gid: 群号
    :return: dict
    """
    config = await ai_verify_store.load_config()
    if gid not in config:
        config[gid] = {"enabled": False, "prompt": ""}
    return config


async def handle_ai_switch_command(matcher: Matcher, gid: str, command_text: str) -> None:
    """
    处理aiswitchcommand
    :param matcher: Matcher 实例
    :param gid: 群号
    :param command_text: 命令文本
    :return: None
    """
    config = await _ensure_group_config(gid)
    normalized = str(command_text or "").strip().lower()

    if "开" in normalized:
        config[gid]["enabled"] = True
        await ai_verify_store.save_config(config)
        await matcher.finish(AI_VERIFY_ENABLED_TEXT)

    if "关" in normalized:
        config[gid]["enabled"] = False
        await ai_verify_store.save_config(config)
        await matcher.finish(AI_VERIFY_DISABLED_TEXT)

    await matcher.finish(AI_VERIFY_INVALID_TEXT)


async def handle_ai_prompt_command(matcher: Matcher, gid: str, prompt_text: str) -> None:
    """
    处理aipromptcommand
    :param matcher: Matcher 实例
    :param gid: 群号
    :param prompt_text: 提示词文本
    :return: None
    """
    config = await _ensure_group_config(gid)
    normalized_prompt = str(prompt_text or "").strip()
    config[gid]["prompt"] = normalized_prompt
    await ai_verify_store.save_config(config)

    if not normalized_prompt:
        await matcher.finish(AI_VERIFY_PROMPT_CLEARED_TEXT)

    await matcher.finish(
        "设置成功！\n"
        "AI 将参考以下规则进行判断：\n"
        "- 符合条件的回答 → 直接同意入群（Agree）\n"
        "- 看起来像真人但不符合条件 → 放行给管理员处理（False）\n"
        "- 广告/人机 → 拒绝（True）\n\n"
        f"自定义规则：{normalized_prompt}"
    )
