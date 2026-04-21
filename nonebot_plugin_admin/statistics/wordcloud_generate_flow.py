from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable

from nonebot import logger

from ..core.html_snapshot import render_html_card_to_image
from .statistics_read_service import load_group_wordcloud_source
from .statistics_store import is_group_record_enabled

WORDCLOUD_TEMPLATE_NAME = "wordcloud.html"
WORDCLOUD_SELECTOR = ".wordcloud-card"
WORDCLOUD_LIMIT = 60

WORDCLOUD_THEME = (
    {"text_color": "#1b4d70", "background": "linear-gradient(135deg, rgba(198, 232, 245, 0.95), rgba(233, 246, 250, 0.95))"},
    {"text_color": "#8a4e2b", "background": "linear-gradient(135deg, rgba(255, 224, 198, 0.96), rgba(255, 241, 225, 0.96))"},
    {"text_color": "#31563d", "background": "linear-gradient(135deg, rgba(214, 239, 213, 0.96), rgba(239, 248, 232, 0.96))"},
    {"text_color": "#6b3f74", "background": "linear-gradient(135deg, rgba(232, 214, 245, 0.96), rgba(246, 237, 252, 0.96))"},
    {"text_color": "#8f5b18", "background": "linear-gradient(135deg, rgba(255, 233, 182, 0.96), rgba(255, 246, 222, 0.96))"},
    {"text_color": "#7a3042", "background": "linear-gradient(135deg, rgba(248, 212, 223, 0.96), rgba(254, 240, 245, 0.96))"},
)

WORDCLOUD_ROTATIONS = (0, 0, 0, -4, 4, -2, 2)


@dataclass(frozen=True)
class WordcloudItem:
    word: str
    count: int
    font_size: int
    rotate: int
    text_color: str
    background: str


async def load_group_word_text(group_id: int | str) -> str | None:
    """
    加载群词文本
    :param group_id: 群号
    :return: str | None
    """
    return (await load_group_wordcloud_source(group_id)).text


async def build_stop_words(group_id: int | str) -> set[str]:
    """
    构建stop词料
    :param group_id: 群号
    :return: set[str]
    """
    return (await load_group_wordcloud_source(group_id)).stop_words


async def prepare_group_wordcloud_payload(group_id: int | str, jieba_module) -> tuple[bool, str, set[str] | None]:
    """
    处理 prepare_group_wordcloud_payload 的业务逻辑
    :param group_id: 群号
    :param jieba_module: jieba_module 参数
    :return: tuple[bool, str, set[str] | None]
    """
    source = await load_group_wordcloud_source(group_id)
    if not source.available:
        if await is_group_record_enabled(group_id):
            return False, "当前群还没有可用于词云的消息记录，请等待群消息积累后再试。", None
        return False, "当前群已停止记录消息内容，请先发送【记录本群】恢复记录后再试。", None
    return True, " ".join(jieba_module.lcut(source.text or "")), source.stop_words


def _is_meaningful_token(token: str, stop_words: set[str]) -> bool:
    """
    处理 _is_meaningful_token 的业务逻辑
    :param token: token 参数
    :param stop_words: stop_words 参数
    :return: bool
    """
    normalized = token.strip()
    if not normalized or normalized in stop_words:
        return False
    if normalized.isdigit():
        return False
    if len(normalized) == 1 and not normalized.isascii():
        return False
    return any(char.isalnum() or ("\u4e00" <= char <= "\u9fff") for char in normalized)


def build_wordcloud_items(
    segmented_text: str,
    *,
    stop_words: set[str] | None = None,
    limit: int = WORDCLOUD_LIMIT,
) -> list[WordcloudItem]:
    """
    构建词云items
    :param segmented_text: 文本内容
    :param stop_words: stop_words 参数
    :param limit: 数量限制
    :return: list[WordcloudItem]
    """
    stop_words = stop_words or set()
    counter = Counter(
        token.strip()
        for token in segmented_text.split()
        if _is_meaningful_token(token, stop_words)
    )
    top_items = counter.most_common(limit)
    if not top_items:
        return []

    counts = [count for _, count in top_items]
    min_count = min(counts)
    max_count = max(counts)
    count_span = max(max_count - min_count, 1)

    items: list[WordcloudItem] = []
    for index, (word, count) in enumerate(top_items):
        theme = WORDCLOUD_THEME[index % len(WORDCLOUD_THEME)]
        font_size = 24 + int((count - min_count) / count_span * 42)
        items.append(
            WordcloudItem(
                word=word,
                count=count,
                font_size=font_size,
                rotate=WORDCLOUD_ROTATIONS[index % len(WORDCLOUD_ROTATIONS)],
                text_color=theme["text_color"],
                background=theme["background"],
            )
        )
    return items


def build_wordcloud_template_context(
    group_id: int | str,
    segmented_text: str,
    *,
    stop_words: set[str] | None = None,
    limit: int = WORDCLOUD_LIMIT,
) -> dict:
    """
    构建词云templatecontext
    :param group_id: 群号
    :param segmented_text: 文本内容
    :param stop_words: stop_words 参数
    :param limit: 数量限制
    :return: dict
    """
    stop_words = stop_words or set()
    items = build_wordcloud_items(segmented_text, stop_words=stop_words, limit=limit)
    if not items:
        raise ValueError("当前词云数据量不足，暂时无法生成图片。")

    total_tokens = sum(item.count for item in items)
    top_words = items[:10]
    return {
        "group_id": str(group_id),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "description": f"共提取 {total_tokens} 个高频分词，已按当前停用词配置过滤。",
        "cloud_words_count": len(items),
        "total_tokens": total_tokens,
        "unique_words": len(items),
        "top_word_count": items[0].count,
        "stop_words_count": len(stop_words),
        "cloud_items": items,
        "top_words": top_words,
    }


def render_wordcloud_html(
    context: dict,
    *,
    template_name: str = WORDCLOUD_TEMPLATE_NAME,
) -> str:
    """
    渲染词云HTML
    :param context: 文本内容
    :param template_name: template_name 参数
    :return: str
    """
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ModuleNotFoundError as err:
        raise RuntimeError("未安装 jinja2，无法渲染词云 HTML 模板") from err

    template_dir = Path(__file__).resolve().parent
    environment = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(("html", "xml")),
    )
    template = environment.get_template(template_name)
    return template.render(**context)


async def render_wordcloud_image(
    text: str,
    *,
    stop_words: set[str] | None = None,
    img_path: Path,
    group_id: int | str = "",
    template_renderer: Callable[[dict], str] | None = None,
    screenshot_renderer: Callable[..., Awaitable[bytes]] | None = None,
    **_ignored,
) -> tuple[bool, bytes | str]:
    """
    渲染词云图片
    :param text: 文本内容
    :param stop_words: stop_words 参数
    :param img_path: 图片路径
    :param group_id: 群号
    :param template_renderer: template_renderer 参数
    :param screenshot_renderer: screenshot_renderer 参数
    :param _ignored: 额外关键字参数
    :return: tuple[bool, bytes | str]
    """
    try:
        context = build_wordcloud_template_context(group_id or "-", text, stop_words=stop_words)
        html = template_renderer(context) if template_renderer else render_wordcloud_html(context)
        renderer = screenshot_renderer or render_html_card_to_image
        image_bytes = await renderer(
            html,
            img_path,
            selector=WORDCLOUD_SELECTOR,
            viewport_width=1560,
            viewport_height=1100,
            wait_ms=220,
        )
        return True, image_bytes
    except Exception as err:
        logger.info(f"词云 HTML 渲染失败: {type(err).__name__}: {err}")
        return False, f"词云图片生成失败：{type(err).__name__}: {err}"
