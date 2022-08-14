import json
from pathlib import Path
from typing import Union, Optional, Tuple
from ssl import SSLCertVerificationError

import httpx
from PIL import Image
from . import aiorequests
import tqdm.asyncio


def load_image(
        path: Union[Path, str],
        *,
        size: Optional[Union[Tuple[int, int], float]] = None,
        crop: Optional[Tuple[int, int, int, int]] = None,
        mode: Optional[str] = None,
):
    """
    说明：
        读取图像，并预处理
    参数：
        :param path: 图片路径
        :param size: 预处理尺寸
        :param crop: 预处理裁剪大小
        :param mode: 预处理图像模式
        :return: 图像对象
    """
    img = Image.open(path)
    if size:
        if isinstance(size, float):
            img = img.resize((int(img.size[0] * size), int(img.size[1] * size)), Image.ANTIALIAS)
        elif isinstance(size, tuple):
            img = img.resize(size, Image.ANTIALIAS)
    if crop:
        img = img.crop(crop)
    if mode:
        img = img.convert(mode)
    return img


def load_json(path: Union[Path, str], encoding: str = 'utf-8') -> dict:
    """
    说明：
        读取本地json文件，返回json字典。
    参数：
        :param path: 文件路径
        :param encoding: 编码，默认为utf-8
        :return: json字典
    """
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        save_json({}, path, encoding)
    return json.load(path.open('r', encoding=encoding))


async def load_json_from_url(url: str, path: Union[Path, str] = None, force_refresh: bool = False) -> dict:
    """
        从网络url中读取json，当有path参数时，如果path文件不存在，就会从url下载保存到path，如果path文件存在，则直接读取path
        :param url: url
        :param path: 本地json文件路径
        :param force_refresh: 是否强制重新下载
        :return: json字典
    """
    if path and Path(path).exists() and not force_refresh:
        return load_json(path=path)
    else:
        try:
            resp = await aiorequests.get(url)
        except SSLCertVerificationError:
            resp = await aiorequests.get(url.replace('https', 'http'))
        data = resp.json()
        if path and not Path(path).exists():
            save_json(data=data, path=path)
        return data


def save_json(data: dict, path: Union[Path, str] = None, encoding: str = 'utf-8'):
    """
    保存json文件
    :param data: json数据
    :param path: 保存路径
    :param encoding: 编码
    """
    if isinstance(path, str):
        path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(data, path.open('w', encoding=encoding), ensure_ascii=False, indent=4)


async def download(url: str, save_path: Path):
    """
    下载文件(带进度条)
    :param url: url
    :param save_path: 保存路径
    """
    save_path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient().stream(method='GET', url=url, follow_redirects=True) as datas:
        size = int(datas.headers['Content-Length'])
        f = save_path.open('wb')
        async for chunk in tqdm.asyncio.tqdm(iterable=datas.aiter_bytes(1),
                                             desc=url.split('/')[-1],
                                             unit='iB',
                                             unit_scale=True,
                                             unit_divisor=1024,
                                             total=size,
                                             colour='green'):
            f.write(chunk)
        f.close()


# async def check_resources(resources: list, save_path: Union[Path, str], logger=None):
#     """
#     检查资源是否存在，不存在就下载
#     :param resources: 资源列表
#     :param save_path: 保存路径
#     :param logger: 日志对象
#     """
#     if isinstance(save_path, str):
#         save_path = Path(save_path)
#     for resource in resources:
#         resource_url = resource['url']
#         resource_hash = resource['hash']
#         resource_path = save_path / resource_url
#         if resource_path.exists() and hashlib.md5(resource_path.read_bytes()).hexdigest() == resource_hash:
#             continue
#         if logger:
#             logger.info(f'资源不存在，开始下载：{resource_url}')
#         for i in range(3):
#             try:
#                 await download_resource(resource_url, resource_path)
#             except Exception as e:
#                 if logger:
#                     logger.warning(f'资源下载失败：{resource_url}, 重试第{i + 1}次：{e}')
#                 await asyncio.sleep(2)
