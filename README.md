<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://raw.githubusercontent.com/nonebot/nonebot2/master/docs/.vuepress/public/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

# 简易群管

_✨ NoneBot2 简易群管_ ✨_

</div>

踢 改 禁.......  
**欢迎 issue pr**

**权限说明：见下方指令↓**

## 安装💿
`pip install nonebot-plugin-admin`

请注意与nonebot版本适配，匹配请查看：[更新](https://github.com/yzyyz1387/nonebot_plugin_admin#%E6%9B%B4%E6%96%B0-1)

## 更新

`pip install --upgrade nonebot-plugin-admin `


## 导入📲
在**bot.py** 导入，语句：
`nonebot.load_plugin("nonebot_plugin_admin")`

## 指令💻

**Tips:** 关于命令，对/sp这类`斜杠+英文`的命令做了保留，汉字命令去除了`/`若使用者担心错误触发，可下载源码自行修改`__init__.py`

```
【初始化】：
  群管初始化 ：初始化插件
  
【加群自动审批】：
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  查看词条 ： 查看本群审批词条   或/sp /审批
  词条+ [词条] ：增加审批词条   或/sp+ /审批+
  词条- [词条] ：删除审批词条   或/sp- /审批-
  
【superuser】：
  所有词条 ：  查看所有审批词条   或/susp /su审批
  指定词条+ [群号] [词条] ：增加指定群审批词条 或/susp+ /su审批+
  指定词条- [群号] [词条] ：删除指定群审批词条 或/susp+ /su审批-
  自动审批处理结果将发送给superuser

【分群管理员设置】
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  分管+ [user] ：user可用@或qq 添加分群管理员 或/gad+
  分管- [user] ：删除分群管理员 或/gad-
  查看分管 ：查看本群分群管理员  或/gad
  
群内或私聊 permission=SUPERUSER
  所有分管 ：查看所有分群管理员 或/sugad
  群管接收 ：打开或关闭超管消息接收（关闭则审批结果不会发送给superusers） 或/sumsg
    
【群管】：
权限：permission=SUPERUSER
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
```


**给个star吧~**

其他插件
[it咨询](https://github.com/yzyyz1387/nonebot_plugin_itnews "it资讯")  [工作性价比](https://github.com/yzyyz1387/nonebot_plugin_workscore)  [在线运行代码](https://github.com/yzyyz1387/nonebot_plugin_code)

## 截图🖼

暂无

## TODO

- 其他功能...  

##  更新

- 0.2.4 (nonebot b1适配)

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

