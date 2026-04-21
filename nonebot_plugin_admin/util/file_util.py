import os.path
from pathlib import Path


def read_all_text(path: Path) -> str:
    """
    读取all文本
    :param path: 路径对象
    :return: str
    """
    if not os.path.exists(path):
        return ''
    with open(path, mode='r', encoding='utf-8') as c:
        return c.read()


def read_all_lines(path: Path, split: str = '\n') -> list[str]:
    """
    读取alllines
    :param path: 路径对象
    :param split: split 参数
    :return: list[str]
    """
    t = read_all_text(path)
    if t is None:
        return list[str]()
    a = t.split(split)
    return a


def write_all_txt(path: Path, value: str, append: bool):
    """
    写入alltxt
    :param path: 路径对象
    :param value: 值
    :param append: append 参数
    :return: None
    """
    if append:
        mode = 'a'
    else:
        mode = 'w'

    with open(path, mode=mode, encoding='utf-8') as c:
        c.write(value)
