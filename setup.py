from pathlib import Path

from setuptools import find_packages, setup


BASE_DIR = Path(__file__).resolve().parent
README_PATH = BASE_DIR / "README.md"

INSTALL_REQUIRES = [
    "nonebot2>=2.2.0",
    "nonebot-adapter-onebot>=2.0.0",
    "fastapi",
    "fuzzyfinder",
    "httpx",
    "jieba",
    "jinja2",
    "nonebot-plugin-apscheduler",
    "nonebot-plugin-htmlrender",
    "nonebot-plugin-tortoise-orm",
    "openai",
    "pydantic",
    "pyppeteer",
    "requests",
    "tencentcloud-sdk-python>=3.0.580",
    "tortoise-orm",
]


setup(
    name="nonebot-plugin-admin",
    version="1.0.2",
    author="yzyyz1387",
    author_email="youzyyz1384@qq.com",
    keywords=["pip", "nonebot2", "nonebot", "admin", "nonebot_plugin"],
    description="nonebot2 plugin for group administration",
    long_description=README_PATH.read_text(encoding="utf-8", errors="ignore"),
    long_description_content_type="text/markdown",
    url="https://github.com/yzyyz1387/nonebot_plugin_admin",
    project_urls={
        "Documentation": "https://github.com/yzyyz1387/nonebot_plugin_admin",
        "Source": "https://github.com/yzyyz1387/nonebot_plugin_admin",
        "Tracker": "https://github.com/yzyyz1387/nonebot_plugin_admin/issues",
    },
    packages=find_packages(include=["nonebot_plugin_admin", "nonebot_plugin_admin.*"]),
    include_package_data=True,
    platforms="any",
    python_requires=">=3.9",
    install_requires=INSTALL_REQUIRES,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ],
)
