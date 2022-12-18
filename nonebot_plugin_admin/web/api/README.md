---
title: admnin-web v1.0.0
language_tabs:
  - shell: Shell
  - http: HTTP
  - javascript: JavaScript
  - ruby: Ruby
  - python: Python
  - php: PHP
  - java: Java
  - go: Go
toc_footers: []
includes: []
search: true
code_clipboard: true
highlight_theme: darkula
headingLevel: 2
generator: "@tarslib/widdershins v4.0.15"


---

# admnin-web

> v1.0.0

# Default

## GET 服务根路径

GET /

如果部署成功，将返回{"message": "this server is for nonebot_plugin_admin"}

> 返回示例

> 成功

```json
{
  "message": "this server is for nonebot_plugin_admin"
}
```

### 返回结果

| 状态码 | 状态码含义                                              | 说明 | 数据模型 |
| ------ | ------------------------------------------------------- | ---- | -------- |
| 200    | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | 成功 | Inline   |

### 返回数据结构

状态码 **200**

| 名称      | 类型   | 必选 | 约束 | 中文名 | 说明 |
| --------- | ------ | ---- | ---- | ------ | ---- |
| » message | string | true | none |        | none |

# msg

## GET 获取指定群记录

GET /msg

获取指定群聊的所有聊天记录，不带 `group_id` 参数则返回所有群聊记录

### 请求参数

| 名称     | 位置  | 类型    | 必选 | 说明                         |
| -------- | ----- | ------- | ---- | ---------------------------- |
| group_id | query | integer | 否   | 不带此参数则返回所有群聊记录 |

> 返回示例

> 成功

```json
[
  {
    "user": 1796031384,
    "group_id": 313626291,
    "update_time": "2022-09-18T08:08:20.286584+00:00",
    "msg": "幼稚园园长",
    "create_time": "2022-09-18T08:08:20.286584+00:00",
    "group_name": "",
    "msg_type": "text",
    "id": 1
  },
  {
    "user": 1796030001,
    "group_id": 132456,
    "update_time": "2022-09-19T05:27:48.076184+00:00",
    "msg": "你好啊",
    "create_time": "2022-09-19T05:27:48.076184+00:00",
    "group_name": "",
    "msg_type": "text",
    "id": 2
  },
  {
    "user": 1796030001,
    "group_id": 132456,
    "update_time": "2022-09-19T05:29:23.487980+00:00",
    "msg": "你好啊",
    "create_time": "2022-09-19T05:29:23.487980+00:00",
    "group_name": "",
    "msg_type": "text",
    "id": 3
  },
  {
    "user": 1796030001,
    "group_id": 132456,
    "update_time": "2022-09-19T05:29:39.143476+00:00",
    "msg": "你好啊",
    "create_time": "2022-09-19T05:29:39.143476+00:00",
    "group_name": "",
    "msg_type": "text",
    "id": 4
  }
]
```

### 返回结果

| 状态码 | 状态码含义                                              | 说明 | 数据模型 |
| ------ | ------------------------------------------------------- | ---- | -------- |
| 200    | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | 成功 | Inline   |

### 返回数据结构

## POST 向数据库添加记录

POST /msg

### 请求参数

| 名称     | 位置  | 类型    | 必选 | 说明                 |
| -------- | ----- | ------- | ---- | -------------------- |
| group_id | query | integer | 是   | 群号                 |
| user     | query | integer | 是   | QQ                   |
| msg      | query | string  | 是   | 消息                 |
| msg_type | query | string  | 否   | 消息类型，默认为text |

> 返回示例

> 成功

```json
{
  "message": "添加成功"
}
```

### 返回结果

| 状态码 | 状态码含义                                              | 说明 | 数据模型 |
| ------ | ------------------------------------------------------- | ---- | -------- |
| 200    | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | 成功 | Inline   |

### 返回数据结构

## GET 获取指定用户的聊天记录

GET /msg/user

获取 `user` 在 `group_id` 的聊天记录，若不带 `group_id` 则返回 `user` 在所有群的聊天记录

### 请求参数

| 名称     | 位置  | 类型    | 必选 | 说明 |
| -------- | ----- | ------- | ---- | ---- |
| user     | query | integer | 是   | QQ   |
| group_id | query | integer | 否   | 群号 |

> 返回示例

> 成功

```json
[
  {
    "user": 1796030001,
    "group_id": 123465,
    "update_time": "2022-09-18T08:08:20.286584+00:00",
    "msg": "这是一条消息",
    "create_time": "2022-09-18T08:08:20.286584+00:00",
    "group_name": "",
    "msg_type": "text",
    "id": 1
  }
]
```

### 返回结果

| 状态码 | 状态码含义                                              | 说明 | 数据模型 |
| ------ | ------------------------------------------------------- | ---- | -------- |
| 200    | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | 成功 | Inline   |

### 返回数据结构

## GET 获取最后一条消息

GET /msg/last

获取 `group_id` 最后一条消息， 不带参数则返回相对所有群的最后一条消息

### 请求参数

| 名称     | 位置  | 类型    | 必选 | 说明 |
| -------- | ----- | ------- | ---- | ---- |
| group_id | query | integer | 否   | none |

> 返回示例

> 成功

```json
{
  "group_id": 132456,
  "id": 4,
  "msg": "你好啊",
  "msg_type": "text",
  "create_time": "2022-09-19T05:29:39.143476+00:00",
  "group_name": "",
  "user": 1796030001,
  "update_time": "2022-09-19T05:29:39.143476+00:00"
}
```

### 返回结果

| 状态码 | 状态码含义                                              | 说明 | 数据模型 |
| ------ | ------------------------------------------------------- | ---- | -------- |
| 200    | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | 成功 | Inline   |

### 返回数据结构

# group

## GET 获取群聊信息

GET /group/

**(没啥用)**
获取 `group_id` 的信息，缺省 `group_id` 则返回整张数据表

### 请求参数

| 名称     | 位置  | 类型    | 必选 | 说明 |
| -------- | ----- | ------- | ---- | ---- |
| group_id | query | integer | 否   | none |

> 返回示例

> 成功

```json
{
  "create_time": "2022-09-19T11:54:59.046832+00:00",
  "group_id": 123456,
  "update_time": "2022-09-19T11:54:59.046832+00:00",
  "group_name": "相亲相爱一家人"
}
```

### 返回结果

| 状态码 | 状态码含义                                              | 说明 | 数据模型 |
| ------ | ------------------------------------------------------- | ---- | -------- |
| 200    | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | 成功 | Inline   |

### 返回数据结构

## POST 添加一条记录

POST /group/add

添加一条记录到 group

### 请求参数

| 名称       | 位置  | 类型    | 必选 | 说明 |
| ---------- | ----- | ------- | ---- | ---- |
| group_id   | query | integer | 是   | none |
| group_name | query | string  | 否   | none |

> 返回示例

> 成功

```json
{
  "message": "添加成功"
}
```

### 返回结果

| 状态码 | 状态码含义                                              | 说明 | 数据模型 |
| ------ | ------------------------------------------------------- | ---- | -------- |
| 200    | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | 成功 | Inline   |

### 返回数据结构

## POST 删除一条信息

POST /group/del

删除 `group_id` 对应的记录

### 请求参数

| 名称     | 位置  | 类型    | 必选 | 说明 |
| -------- | ----- | ------- | ---- | ---- |
| group_id | query | integer | 是   | 群号 |

> 返回示例

> 成功

```json
{
  "message": "删除成功"
}
```

### 返回结果

| 状态码 | 状态码含义                                              | 说明 | 数据模型 |
| ------ | ------------------------------------------------------- | ---- | -------- |
| 200    | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | 成功 | Inline   |

### 返回数据结构

# switcher

## GET 获取某群开关状态

GET /switcher

获取 `group_id` 开关状态，缺省则返回所有群的开关状态

### 请求参数

| 名称     | 位置  | 类型    | 必选 | 说明 |
| -------- | ----- | ------- | ---- | ---- |
| group_id | query | integer | 否   | 群号 |

> 返回示例

> 成功

```json
{
  "group_id": 123456,
  "wordcloud": true,
  "img_check": false,
  "admin": true,
  "word_analyze": true,
  "create_time": "2022-09-22T16:25:41.247832+00:00",
  "update_time": "2022-09-22T16:25:41.247832+00:00",
  "auto_ban": false,
  "requests": true,
  "group_name": ""
}
```

### 返回结果

| 状态码 | 状态码含义                                              | 说明 | 数据模型 |
| ------ | ------------------------------------------------------- | ---- | -------- |
| 200    | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | 成功 | Inline   |

### 返回数据结构

## POST 更改群管插件功能开关

POST /switcher

添加或更改群管插件功能开关， `body`为空（即 `{}` ） 则对 `group_id` 初始化开关状态

> Body 请求参数

```json
{
  "admin": true,
  "requests": true,
  "wordcloud": true,
  "auto_ban": false,
  "img_check": false,
  "word_analyze": true
}
```

### 请求参数

| 名称       | 位置  | 类型    | 必选 | 说明 |
| ---------- | ----- | ------- | ---- | ---- |
| group_id   | query | integer | 是   | 群号 |
| group_name | query | string  | 否   | 群名 |
| body       | body  | object  | 否   | none |

> 返回示例

> 成功

```json
{
  "message": "操作成功",
  "status": {
    "create_time": "2022-09-22T16:30:10.699299+00:00",
    "admin": true,
    "wordcloud": true,
    "img_check": false,
    "requests": true,
    "group_name": "测试群",
    "group_id": 1000001,
    "auto_ban": false,
    "word_analyze": true,
    "update_time": "2022-09-22T16:35:59.132053+00:00"
  }
}
```

### 返回结果

| 状态码 | 状态码含义                                              | 说明 | 数据模型 |
| ------ | ------------------------------------------------------- | ---- | -------- |
| 200    | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | 成功 | Inline   |

### 返回数据结构

# 数据模型

<h2 id="tocS_开关">开关</h2>

<a id="schema开关"></a>
<a id="schema_开关"></a>
<a id="tocS开关"></a>
<a id="tocs开关"></a>

```json
{
  "admin": true,
  "requests": true,
  "wordcloud": true,
  "auto_ban": true,
  "img_check": true,
  "word_analyze": true
}

```

### 属性

| 名称         | 类型    | 必选 | 约束 | 中文名   | 说明                 |
| ------------ | ------- | ---- | ---- | -------- | -------------------- |
| admin        | boolean | true | none | 管理功能 | 控制踢禁改头衔       |
| requests     | boolean | true | none | 审批功能 | 及控制加群审批       |
| wordcloud    | boolean | true | none | 词云功能 | 控制群词云功能       |
| auto_ban     | boolean | true | none | 违禁词   | 控制违禁词自动禁言   |
| img_check    | boolean | true | none | 图片检测 | 控制porn图片自动检测 |
| word_analyze | boolean | true | none | 发言分析 | 控制消息记录和分析   |

