import io
import sys

import setuptools

with open("README.md", "r", encoding="utf-8", errors="ignore") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nonebot-plugin-admin",
    version="0.4.5.3",
    author="yzyyz1387",
    author_email="youzyyz1384@qq.com",
    keywords=("pip", "nonebot2", "nonebot", "admin", "nonebot_plugin"),
    description="""nonebot2 plugin for group administration""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yzyyz1387/nonebot_plugin_admin",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    platforms="any",
    install_requires=["fuzzyfinder", 'nonebot-adapter-onebot>=2.0.0-beta.1', 'nonebot2>=2.0.0-beta'
                                                                                                '.4', "jieba",
                      "httpx", "tencentcloud-sdk-python>=3.0.580", "jinja2", "pyppeteer", "imageio", "numpy",
                      "nonebot_plugin_apscheduler"]
)
