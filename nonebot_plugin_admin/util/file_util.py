import os.path
from pathlib import Path


def read_all_text(path: Path) -> str:
    if not os.path.exists(path):
        return ''
    with open(path, mode='r', encoding='utf-8') as c:
        return c.read()


def read_all_lines(path: Path, split: str = '\n') -> list[str]:
    t = read_all_text(path)
    if t is None:
        return list[str]()
    a = t.split(split)
    return a


def write_all_txt(path: Path, value: str, append: bool):
    if append:
        mode = 'a'
    else:
        mode = 'w'

    with open(path, mode=mode, encoding='utf-8') as c:
        c.write(value)
