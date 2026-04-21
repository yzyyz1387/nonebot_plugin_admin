from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from nonebot import logger


async def _render_with_htmlrender(
    html: str,
    *,
    viewport_width: int,
    viewport_height: int,
    wait_ms: int,
) -> bytes:
    """
    渲染withhtmlrender
    :param html: HTML 内容
    :param viewport_width: 截图视口宽度
    :param viewport_height: 截图视口高度
    :param wait_ms: 等待毫秒数
    :return: bytes
    """
    from nonebot import require

    require("nonebot_plugin_htmlrender")
    from nonebot_plugin_htmlrender import html_to_pic  # noqa: WPS433

    return await html_to_pic(
        html=html,
        wait=max(wait_ms, 0),
        type="png",
        device_scale_factor=2,
        screenshot_timeout=30_000,
        viewport={"width": viewport_width, "height": viewport_height},
    )


async def _render_with_pyppeteer(
    html: str,
    img_path: Path,
    *,
    selector: str | None,
    viewport_width: int,
    viewport_height: int,
    wait_ms: int,
) -> bytes:
    """
    渲染withpyppeteer
    :param html: HTML 内容
    :param img_path: 图片路径
    :param selector: 选择器
    :param viewport_width: 截图视口宽度
    :param viewport_height: 截图视口高度
    :param wait_ms: 等待毫秒数
    :return: bytes
    """
    try:
        from pyppeteer import launch
    except ModuleNotFoundError as err:
        raise RuntimeError("未安装 pyppeteer，无法渲染 HTML 截图") from err

    browser = None
    temp_path: Path | None = None

    try:
        with NamedTemporaryFile("w", encoding="utf-8", suffix=".html", delete=False) as tmp:
            tmp.write(html)
            temp_path = Path(tmp.name)

        browser = await launch(
            options={
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ]
            },
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False,
        )
        page = await browser.newPage()
        await page.setViewport({"width": viewport_width, "height": viewport_height, "deviceScaleFactor": 2})
        await page.goto(temp_path.resolve().as_uri(), {"waitUntil": "networkidle2"})
        if wait_ms > 0:
            await page.waitFor(wait_ms)

        if selector:
            await page.waitForSelector(selector)
            target = await page.querySelector(selector)
            if target is None:
                raise RuntimeError(f"未找到截图选择器: {selector}")
            await target.screenshot({"path": str(img_path)})
        else:
            await page.screenshot({"path": str(img_path), "fullPage": True})

        return img_path.read_bytes()
    finally:
        if browser is not None:
            await browser.close()
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


async def render_html_card_to_image(
    html: str,
    img_path: Path,
    *,
    selector: str | None = None,
    viewport_width: int = 1560,
    viewport_height: int = 1100,
    wait_ms: int = 200,
) -> bytes:
    """
    渲染HTMLcardto图片
    :param html: HTML 内容
    :param img_path: 图片路径
    :param selector: 选择器
    :param viewport_width: 截图视口宽度
    :param viewport_height: 截图视口高度
    :param wait_ms: 等待毫秒数
    :return: bytes
    """
    img_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        image_bytes = await _render_with_htmlrender(
            html,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            wait_ms=wait_ms,
        )
        img_path.write_bytes(image_bytes)
        return image_bytes
    except Exception as err:
        logger.warning(f"HTMLRender 截图失败，回退 pyppeteer: {type(err).__name__}: {err}")

    return await _render_with_pyppeteer(
        html,
        img_path,
        selector=selector,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        wait_ms=wait_ms,
    )
