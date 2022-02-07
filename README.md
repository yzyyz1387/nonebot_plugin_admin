<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://raw.githubusercontent.com/nonebot/nonebot2/master/docs/.vuepress/public/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

# 简易群管

_✨ NoneBot2 (有点不)简易群管_ ✨_

</div>

踢 改 禁.......  
**欢迎 issue pr**

**权限说明：见下方指令↓**

## 安装💿
`pip install nonebot-plugin-admin`

请注意与nonebot版本适配，匹配请查看：[更新](#%E6%9B%B4%E6%96%B0-1)

## 更新

`pip install --upgrade nonebot-plugin-admin `


## 导入📲
在**bot.py** 导入，语句：
`nonebot.load_plugin("nonebot_plugin_admin")`

## 指令💻

**Tips:** 

- 关于命令，对/sp这类`斜杠+英文`的命令做了保留，汉字命令去除了`/`若使用者担心错误触发，可下载源码自行修改`__init__.py`
- 为了防止错误触发，相同操作的` +` ` -`都写(复制)了两段代码 
- 群词云功能所用库 wordcloud 未写入依赖，请自行安装：`pip install wordcloud` 安装失败参考：[WordCloud 第三方库安装失败原因及解决方法](https://www.freesion.com/article/4756295761/)
- matcher权重请自行查看代码
```
【初始化】：
  群管初始化 ：初始化插件

【群管】：
权限：permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER
  禁言:
    禁 @某人 时间（s）[1,2591999]
    禁 @某人 缺省时间则随机
    禁 @某人 0 可解禁
    解 @某人
  全群禁言（好像没用？）
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
违禁词检测：将禁言随机时间
```

**给个star吧~**

### 其他插件
- [随机黑丝](https://github.com/yzyyz1387/nonebot_plugin_heisi "随机黑丝") 
- [工作性价比](https://github.com/yzyyz1387/nonebot_plugin_workscore) 
- [在线运行代码](https://github.com/yzyyz1387/nonebot_plugin_code)

## 截图🖼

暂无

## TODO
- [x] 加群自动审批[#issues1](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/1)
- [x] /sp在未配置群聊中的提示  
- [x] /删头衔bug修复  
- [x] 加群处理状态分群分用户发送[#issues2](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/2)
- [x] 关键词禁言，图片鉴黄（简单实现），[#issues3](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/3)
- [ ] 恶意检测， [#issues3](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/3)
- [ ] 鉴黄置信度呈现
- [ ] 潜水查询
- [ ] 群聊内容分析
- [ ] 其他功能...

##  更新

- ~~0.3.8 0.3.10~~ 0.3.12（b1）
  - 修复启动时`word_analyze`报错
  - 修复词云路径错误
  - 分词优化
  - 图片鉴黄
  - 违禁词检测 违禁词词库整理上传于：[f_words](https://github.com/yzyyz1387/nwafu/tree/main/f_words)

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

