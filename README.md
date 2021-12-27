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



## 更新

`pip install --upgrade nonebot-plugin-admin `




## 导入📲
在**bot.py** 导入，语句：
`nonebot.load_plugin("nonebot_plugin_admin")`



## 指令💻
```
【superuser】：
  /susp  查看所有审批词条   或/su审批
  /susp+ [群号] [词条]增加指定群审批词条 或/sp审批+
  /susp- [群号] [词条]删除指定群审批词条 或/sp审批-
  自动审批处理结果将发送给superuser
  
【加群自动审批】：
群内发送 permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
  /审批  查看本群审批词条   或/sp
  /审批+ [词条]增加审批词条 或/sp+
  /审批- [词条]删除审批词条 或/sp-
  
【群管】：
权限：permission=SUPERUSER
  禁言:
    /禁 @某人 时间（s）[1,2591999]
    /禁 @某人 缺省时间则随机
    /禁 @某人 0 可解禁
    /解 @某人
  全群禁言（好像没用？）
    /all 
    /all 解
  改名片
    /改 @某人 名片
  改头衔
    /头衔 @某人 头衔
    /删头衔
  踢出：
    /踢 @某人
  提出并拉黑：
   /黑 @某人
```


**给个star吧~**

其他插件
[it咨询](https://github.com/yzyyz1387/nonebot_plugin_itnews "it资讯")
[工作性价比](https://github.com/yzyyz1387/nonebot_plugin_workscore)

[在线运行代码](https://github.com/yzyyz1387/nonebot_plugin_code)

## 截图🖼

暂无



##  更新

**0.1.0** [issue#1](https://github.com/yzyyz1387/nonebot_plugin_admin/issues/1)

支持入群自动审批

支持在线对不同群的关键词进行增减操作



**0.0.1-4**

支持 踢 、禁 、改 、头衔

