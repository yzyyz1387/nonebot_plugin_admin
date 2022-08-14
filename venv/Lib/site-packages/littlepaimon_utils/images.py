from PIL import ImageFont


def get_font(size, font_path):
    """
    获取字体
    :param size: 字体大小
    :param font_path: 字体路径
    """
    return ImageFont.truetype(font_path, size)


def draw_right_text(draw, text: str, width: int, height: int, fill: str, font):
    """
    绘制右对齐文字
    :param draw: ImageDraw对象
    :param text: 文字
    :param width: 位置横坐标
    :param height: 位置纵坐标
    :param fill: 字体颜色
    :param font: 字体
    """
    text_length = draw.textlength(text, font=font)
    draw.text((width - text_length, height), text, fill=fill,
              font=font)


def draw_center_text(draw, text: str, left_width: int, right_width: int, height: int, fill: str, font):
    """
    绘制居中文字
    :param draw: ImageDraw对象
    :param text: 文字
    :param left_width: 左边位置横坐标
    :param right_width: 右边位置横坐标
    :param height: 位置纵坐标
    :param fill: 字体颜色
    :param font: 字体
    """
    text_length = draw.textlength(text, font=font)
    draw.text((left_width + (right_width - left_width - text_length) / 2, height), text, fill=fill,
              font=font)
