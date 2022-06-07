<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>



<div align="center">  
  
**你的star是我的动力**  
**↓**  
<img src="https://img.shields.io/github/stars/yzyyz1387/nonebot_plugin_admin.svg?style=social">  
# 简易群管 （考研缓更）  
   **pypi没更 github最新**  
  _✨ NoneBot2 (有点不)简易群管✨ _    


  
[![wakatime](https://wakatime.com/badge/user/e4795d94-d154-4c3d-a94b-b655c82e57f4/project/d4a8cb5e-ee86-4ad9-99e5-48873f38c3bd.svg)](https://wakatime.com/badge/user/e4795d94-d154-4c3d-a94b-b655c82e57f4/project/d4a8cb5e-ee86-4ad9-99e5-48873f38c3bd)


踢 改 禁.......  
**欢迎 ISSUES PR**
</div>  

**权限说明：见下方指令↓**

## 安装💿(pip)
`pip install nonebot-plugin-admin`

### 导入📲
在**bot.py** 导入，语句：
`nonebot.load_plugin("nonebot_plugin_admin")`

请注意与nonebot版本适配，匹配请查看：[更新](#%E6%9B%B4%E6%96%B0-1)
**Python 3.9+**

## 安装💿(nb plugin)
`nb plugin install nonebot-plugin-admin`


## 更新

`pip install --upgrade nonebot-plugin-admin `

## 配置
鉴黄配置：  
腾讯云图片安全，开通地址：[https://console.cloud.tencent.com/cms](https://console.cloud.tencent.com/cms)  
文档：[https://cloud.tencent.com/document/product/1125](https://cloud.tencent.com/document/product/1125)

需要使用此功能时在 `.env.*` 文件中加入以下内容，并且设置你自己的 `api id` 与 `api key`【不需要此功能可以不配置】：
```
# 腾讯云图片安全api
tenid="xxxxxx"
tenkeys="xxxxxx"
# 是否开启禁言等操作的成功提示【不开启的话踢人/禁言等成功没有QQ消息提示】
callback_notice=true # 如果不想开启设置成 false 或者不添加此配置项【默认关闭】
```

更多配置项请查看 [config.py](./nonebot_plugin_admin/config.py)


✨Pay tribute to A60 [https://github.com/djkcyl/ABot-Graia](https://github.com/djkcyl/ABot-Graia)



## 指令💻

**Tips:** 

- 关于命令，对/sp这类`斜杠+英文`的命令做了保留，汉字命令去除了`/`若使用者担心错误触发，可下载源码自行修改`__init__.py`
- 群词云功能所用库 wordcloud 未写入依赖，请自行安装：`pip install wordcloud` 安装失败参考：[WordCloud 第三方库安装失败原因及解决方法](https://www.freesion.com/article/4756295761/)
- 一般情况下可正常使用，可能由于权重出现问题，matcher权重请自行查看代码
- 使用`开关状态`指令查看各功能状态，首次使用可能会下载100Mb+的`Chromium`，请耐心等待
```
【初始化】：
  群管初始化 ：初始化插件

【群管】：
权限：permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER
  禁言:
    禁 @某人 时间（s）[1,2591999]
    禁 时间（s）@某人 [1,2591999]
    禁 @某人 缺省时间则随机
    禁 @某人 0 可解禁
    解 @某人
  全群禁言 即使你的命令前缀为空，仍需使用 /all 来触发
    /all 
    /all 解
  改名片
    改 @某人 名片
  改头衔
    头衔 @某人 头衔
    删头衔
  踢出：
    踢 @某人
  踢出并拉黑：
   黑 @某人
  撤回:
   撤回 (回复某条消息即可撤回对应消息)
   撤回 @user [(可选，默认n=5)历史消息倍数n] (实际检查的历史数为 n*19)
   
【管理员】permission=SUPERUSER | GROUP_OWNER
  管理员+ @xxx 设置某人为管理员
  管理员- @xxx 取消某人管理员
  
【加群自动审批】：
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  查看词条 ： 查看本群审批词条   或/审批
  词条+ [词条] ：增加审批词条 或/审批+
  词条- [词条] ：删除审批词条 或/审批-

【superuser】：
  所有词条 ：  查看所有审批词条   或/su审批
  指定词条+ [群号] [词条] ：增加指定群审批词条 或/su审批+
  指定词条- [群号] [词条] ：删除指定群审批词条 或/su审批-
  自动审批处理结果将发送给superuser

【分群管理员设置】*分管：可以接受加群处理结果消息的用户
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  分管+ [user] ：user可用@或qq 添加分群管理员
  分管- [user] ：删除分群管理员
  查看分管 ：查看本群分群管理员

群内或私聊 permission=SUPERUSER
  所有分管 ：查看所有分群管理员
  群管接收 ：打开或关闭超管消息接收（关闭则审批结果不会发送给superusers）
  
【群词云统计】
该功能所用库 wordcloud 未写入依赖，请自行安装
群内发送：
  记录本群 ： 开始统计聊天记录 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  停止记录本群 ：停止统计聊天记录
  群词云 ： 发送词云图片
  
【被动识别】
涩图检测：将禁言随机时间

违禁词检测：已支持正则表达式，可定义触发违禁词操作(默认为禁言+撤回)
定义操作方法：用制表符分隔，左边为触发条件，右边为操作定义($禁言、$撤回)
群内发送：
  简单违禁词 ：简单级别过滤
  严格违禁词 ：严格级别过滤(不建议)
  更新违禁词库 ：手动更新词库
    违禁词库每周一自动更新
    
【功能开关】
群内发送：
  开关xx : 对某功能进行开/关  permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER
  开关状态 ： 查看各功能的状态
  xx in ：
    ['管理', '踢', '禁', '改', '基础群管']  #基础功能 踢、禁、改、管理员+-
    ['加群', '审批', '加群审批', '自动审批'] #加群审批
    ['词云', '群词云', 'wordcloud'] #群词云
    ['违禁词', '违禁词检测'] #违禁词检测
    ['图片检测', '图片鉴黄', '涩图检测', '色图检测'] #图片检测
所有功能默认开

```

**给个star吧~**

### 其他插件
- [随机黑丝](https://github.com/yzyyz1387/nonebot_plugin_heisi "随机黑丝") 
- [工作性价比](https://github.com/yzyyz1387/nonebot_plugin_workscore) 
- [在线运行代码](https://github.com/yzyyz1387/nonebot_plugin_code)

## 截图🖼
**禁 改 踢**   
![](https://cdn.jsdelivr.net/gh/yzyyz1387/blogimages/nonebot/ad_kick.gif)

**管理员+ -**  
![](https://cdn.jsdelivr.net/gh/yzyyz1387/blogimages/nonebot/ad_admin.gif)

**群词云**
![](https://cdn.jsdelivr.net/gh/yzyyz1387/blogimages/nonebot/ad_cloud.gif)

**违禁词检测**
![](https://cdn.jsdelivr.net/gh/yzyyz1387/blogimages/nonebot/ad_autoban.gif)

**图片检测**
![](https://cdn.jsdelivr.net/gh/yzyyz1387/blogimages/nonebot/ad_r18ban.gif)

**功能开关**
![](https://cdn.jsdelivr.net/gh/yzyyz1387/blogimages/nonebot/ad_switcher.gif)
## TODO
- [x] 加群自动审批[#issues1](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/1)
- [x] /sp在未配置群聊中的提示  
- [x] /删头衔bug修复  
- [x] 加群处理状态分群分用户发送[#issues2](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/2)
- [x] 关键词禁言，图片鉴黄（简单实现），[#issues3](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/3)
- [ ] 恶意检测， [#issues3](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/3)
- [ ]  ~~鉴黄置信度呈现~~
- [ ]  头衔命令所有人可用，删头衔命令加权限
- [ ]  修复加群审批默认处理规则
- [ ] 词云停用词优化
- [ ] 分群群词云自定义停用词
- [ ] 违禁词优化
- [ ] 全局开关
- [ ] 潜水查询
- [ ] 群聊内容分析
- [ ] 写一个文档
- [ ] 一些大事

##  更新
-0.3.21
  - 优化默认配置；同时增加一个配置项：设置禁言等基础操作是否在 qq 返回操作结果 [#18](https://github.com/yzyyz1387/nonebot_plugin_admin/pull/18)
  - 修复`禁@xxx`的buggi
- 0.3.19
  - 修复`__init__.py`中的bug🐛 [PULL#17](https://github.com/yzyyz1387/nonebot_plugin_admin/pull/17) [@tom-snow](https://github.com/tom-snow)
  - 优化`禁@xxx`,改善灵活性 [#15](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/15)
  - `switcher.py`网页截图错误捕捉
  - 修改cdn地址
  - 修聊天记录编码问题
  - 改善违禁词检测功能的灵活性[@lakwsh](https://github.com/yzyyz1387/nonebot_plugin_admin/commits?author=lakwsh)
    - 违禁词检测：已支持正则表达式，可定义触发违禁词操作(默认为禁言+撤回)  
    - 定义操作方法：用制表符分隔，左边为触发条件，右边为操作定义($禁言、$撤回)
- 修复触发违禁词不会阻止事件传播的问题[@lakwsh](https://github.com/yzyyz1387/nonebot_plugin_admin/commits?author=lakwsh)
- 修复可能会导致其他插件无法捕获消息的问题[@lakwsh](https://github.com/yzyyz1387/nonebot_plugin_admin/commits?author=lakwsh)
- 修复部分文件编码错误，开关状态图片乱码及SIGINT信号被劫持的问题[@lakwsh](https://github.com/yzyyz1387/nonebot_plugin_admin/commits?author=lakwsh)


- 0.3.18（beta）
  - update LICENSE to AGPL-3.0
  - 🐛修复`管理员-`无效的bug
  - 🐛修复`简单违禁词`、`严格违禁词`无效的bug
  - 🐛修复`禁 解 改`等指令有无空格的问题
  - 禁言命令新增不禁言superuser
  - 鉴黄api改为腾讯云，请自行开通配置
  - 违禁词词库每周一自动更新,手动更新：`更新违禁词库`
  - 分群功能开关
  - 使用`开关状态`指令查看各功能状态，首次使用可能会下载109Mb的`Chromium`
- 0.3.16（b1）
  - 修复启动时`word_analyze`报错
  - 修复词云路径错误
  - 分词优化
  - 图片鉴黄
  - 违禁词检测 违禁词词库整理上传于：[f_words](https://github.com/yzyyz1387/nwafu/tree/main/f_words) 
  - 词库有赘余，欢迎大神pr精简
- 0.3.15（a16）
  - 同 0.3.16   
- 0.3.6（b1)
  - 修复适配错误
  - 补充依赖
- 0.3.5（a16）
  - 补充依赖（谁教教我项目管理..
- 0.3.4 （b1)
- 0.3.3（a16)
  - 修复导入错误
  - 修复路径错误
- 0.2.8  (nonebot b1适配)
  - b1适配，功能同0.2.7
- 0.2.7  (nonebot a16适配)
  - 对应adapter加入依赖
  - 优化代码结构
  - 增加群词云功能
    - 更新后请执行`群管初始化`（不影响已保存的配置）
    - 机器人提示`成功`后开始记录本群所有文本内容
    - 发送`群词云`使用此功能
  - 修复`禁@xxx 60 `这类命令失效的bug
- 0.2.6  (nonebot a16适配)
- 0.2.5  (nonebot b1适配)
  - 代码优化
  - 踢禁改等命令增加权限:机器人主人，群主，群管理员 `permission=SUPERUSER|GROUP_ADMIN | GROUP_OWNER`
  - 增加添加/删除管理员操作,命令：`管理员+@xxx` `管理员-@xxx`
  - 修复 `禁言多人而不带具体时间时只禁言第一位`的bug🐛
- 0.2.4 (nonebot b1适配)
  - 同0.2.3
- 0.2.3  (nonebot a16适配)
  - 代码优化
  - 命令去除 `/`
  - 摒弃英文命令，改为汉字命令
- 0.2.2	（适配 nonebot b1) [issue#2](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/2)

  - **更新后请初始化**:`/spinit`

  - 修复未配置时`/sp`，命令出现错误
  - 修复`/删头衔`的bug
  - 增加分群管理，加群请求处理结果将发送给分群管理 
  - 加群处理结果消息对 superuser 可开启或关闭: `/sumsg`
- **0.2.1**
  - 修复requiers
- **0.1.9**
  - 修复初始化功能
- **0.1.0** [issue#1](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/1)
- 支持入群自动审批
- 支持在线对不同群的关键词进行增减操作
- **0.0.1-4**
  - 支持 踢 、禁 、改 、头衔


## 其他插件
[简易群管](https://github.com/yzyyz1387/nonebot_plugin_admin)  
[在线运行代码](https://github.com/yzyyz1387/nonebot_plugin_code)  
[it咨讯（垃圾插件）](https://github.com/yzyyz1387/nonebot_plugin_itnews "it资讯")  
[工作性价比（还没更新beta不能用）](https://github.com/yzyyz1387/nonebot_plugin_workscore)  
[黑丝插件（jsdelivr问题国内服务器不能用）](https://github.com/yzyyz1387/nonebot_plugin_heisi)  
