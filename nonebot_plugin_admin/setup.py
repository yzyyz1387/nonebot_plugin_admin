from setuptools import setup,find_packages
setup(name='nonebot_plugin_admin_hello',
      version='0.0.1',
      description='nonebot_plugin_admin_hello',
      author='HuYihe',
      author_email='2812856215@qq.com',
      packages=find_packages(),  # 系统自动从当前目录开始找包
      requires=[  'aiofiles',
                  'fuzzyfinder',
                  'httpx',
                  'jieba',
                  'nonebot-adapter-onebot>=2.0.0-beta.1'
                  'nonebot2>=2.0.0-beta.4',
                  'tencentcloud-sdk-python>=3.0.580',
                  'setuptools',
                  'jinja2',
                  'pyppeteer',
                  'imageio',
                  'numpy',
                  'nonebot-plugin-apscheduler>=0.1.2',
                  'nonebot-plugin-htmlrender>=0.0.4.6',
                  'beautifulsoup4>=4.10.0',
                  'httpx>=0.23.0',
                  'lxml>=4.8.0',
                  'Pillow>=9.1.1',
                  'matplotlib>=3.5.1',
                  'xlsxwriter>=3.0.3',
                  'sqlitedict>=2.0.0',
                  'aiofiles>=0.8.0',
                  'littlepaimon_utils>=1.0.2',
                ],
      )

