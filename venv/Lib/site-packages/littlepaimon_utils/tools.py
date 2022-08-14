import hashlib
import random
from collections import defaultdict
import time
from typing import Union, List


class FreqLimiter:
    """
    频率限制器（冷却时间限制器）
    """

    def __init__(self, default_cd_seconds: int = 60):
        """
        初始化一个频率限制器
        :param default_cd_seconds: 默认冷却时间（秒）
        """
        self.next_time = defaultdict(float)
        self.default_cd = default_cd_seconds

    def check(self, key) -> bool:
        """
        检查是否冷却结束
        :param key: key
        :return: 布尔值
        """
        return bool(time.time() >= self.next_time[key])

    def start_cd(self, key, cd_time=0):
        """
        开始冷却
        :param key: key
        :param cd_time: 冷却时间
        """
        self.next_time[key] = time.time() + (cd_time if cd_time > 0 else self.default_cd)

    def left_time(self, key) -> int:
        """
        剩余冷却时间
        :param key: key
        :return: 剩余冷却时间
        """
        return int(self.next_time[key] - time.time()) + 1


def md5(text: str) -> str:
    """
    md5加密
    :param text: 加密文本
    :return: md5的hexdigest
    """
    md5_ = hashlib.md5()
    md5_.update(text.encode())
    return md5_.hexdigest()


def random_hex(length):
    """
    随机生成指定长度的字符串
    :param length: 长度
    :return: 字符串
    """
    result = hex(random.randint(0, 16 ** length)).replace('0x', '').upper()
    if len(result) < length:
        result = '0' * (length - len(result)) + result
    return result


def replace_all(raw_text: str, text_list: Union[str, List[str]]) -> str:
    """
    批量移除文本中的字符串
    :param raw_text: 被处理文本
    :param text_list: 需移除的文本列表
    :return: 处理后的文本
    """
    if not text_list:
        return raw_text
    else:
        if isinstance(text_list, str):
            text_list = [text_list]
        for text in text_list:
            raw_text = raw_text.replace(text, '')
        return raw_text
