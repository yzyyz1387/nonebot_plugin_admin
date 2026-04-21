<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>



<div align="center">  
  
**你的star是我的动力**  
**↓**  
<img src="https://img.shields.io/github/stars/yzyyz1387/nonebot_plugin_admin.svg?style=social">  
# （不）简易群管   
  _✨ NoneBot2 (有点不)简易群管✨ _    

 
[//]: # ([![wakatime]&#40;https://wakatime.com/badge/user/e4795d94-d154-4c3d-a94b-b655c82e57f4/project/d4a8cb5e-ee86-4ad9-99e5-48873f38c3bd.svg&#41;]&#40;https://wakatime.com/badge/user/e4795d94-d154-4c3d-a94b-b655c82e57f4/project/d4a8cb5e-ee86-4ad9-99e5-48873f38c3bd&#41;)


踢 改 禁.......  
**欢迎 ISSUES PR**
</div>  

# nonebot\_plugin\_admin

`nonebot_plugin_admin` 是一个基于 NoneBot2 的群管理插件集合，当前包含基础群管、入群审批、内容审核、统计分析、广播、事件提醒、成员清理等功能。

当前 `main-check` 分支正在做结构整理与重构优化，目标是先稳定现有能力，再逐步清理历史耦合与文档遗留问题。现阶段目录结构和部分实现已经完成分域拆分，根目录说明文档也已按当前代码状态更新。

## 当前能力

- 基础群管：禁言、解禁、改名片、踢人、拉黑、管理员增减、头衔、撤回、精华消息
- 入群审批：审批词条、拒绝词条、分群管理员、手动处理请求、AI 广告拦截
- 内容审核：违禁词检查、图片审核
- 统计分析：消息记录、发言排行、群词云、停用词、早晚安群消息
- 广播：广播预览、二次确认、排除群维护
- 事件提醒：防撤回、事件通知
- 成员清理：规则筛选、清理锁
- Dashboard：Web 管理面板、API 接口、操作日志

## 安装

```bash
pip install nonebot-plugin-admin
```

或使用 `nb`：

```bash
nb plugin install nonebot-plugin-admin
```

## 导入

在 `bot.py` 中加载插件：

```python
nonebot.load_plugin("nonebot_plugin_admin")
```

推荐 Python 3.9 及以上版本。

## 依赖说明

依赖会在安装插件时自动安装，如果你是从仓库下载的插件，则需要：

```bash
pip install -r requirements.txt
```

## 配置

以下配置写入 `.env` 或 `.env.prod` 等 NoneBot 配置文件。

### 基础配置

| 配置项                 | 必填 | 默认值       | 说明                    |
| ------------------- | -- | --------- | --------------------- |
| `tenid`             | 否  | `xxxxxx`  | 腾讯云 SecretId（图片安全审核）  |
| `tenkeys`           | 否  | `xxxxxx`  | 腾讯云 SecretKey（图片安全审核） |
| `callback_notice`   | 否  | `true`    | 是否发送操作成功提示            |
| `ban_rand_time_min` | 否  | `60`      | 随机禁言最短时间（秒）           |
| `ban_rand_time_max` | 否  | `2591999` | 随机禁言最长时间（秒）           |

> ⚠️ 腾讯云图片安全审核为古早版本加入的功能，目前不太推荐使用。如需图片审核能力，建议评估其他方案。

### AI 入群审核（推荐使用）

| 配置项                   | 必填 | 默认值    | 推荐启用？  | 说明                   |
| --------------------- | -- | ------ | :----- | -------------------- |
| `ai_verify_api_key`   | 否  | （空）    | 推荐     | OpenAI 兼容接口 API Key  |
| `ai_verify_base_url`  | 否  | （空）    | 推荐     | OpenAI 兼容接口 Base URL |
| `ai_verify_model`     | 否  | （空）    | 推荐     | 使用的模型名称              |
| `ai_verify_proxy`     | 否  | （空）    | <br /> | AI 审核请求代理地址          |
| `ai_verify_use_proxy` | 否  | `true` | <br /> | 是否启用代理               |

说明：

- `ai_verify_use_proxy=false` 时，AI 审核请求不会走代理
- `ai_verify_proxy` 仅影响 AI 审核请求，不影响插件内其他网络请求
- 未配置 `ai_verify_api_key` 时，AI 审核功能会自动退化为不可用状态
- 会拒绝“请通过一下，谢谢！”这类及机器人加群

### 早晚安群消息

> ⚠️ 此功能由用户 PR 加入，完成度一般，无需求可不用。

| 配置项                     | 必填 | 默认值      | 说明                      |
| ----------------------- | -- | -------- | ----------------------- |
| `send_group_id`         | 是  | （空）      | 推送目标群号，JSON 数组或逗号分隔     |
| `send_switch_morning`   | 否  | `true`   | 是否启用早安推送                |
| `send_switch_night`     | 否  | `true`   | 是否启用晚安推送                |
| `send_mode`             | 否  | `2`      | 推送模式：`1`=自定义句子，`2`=随机一言 |
| `send_sentence_morning` | 否  | （空）      | 早安自定义句子列表（mode=1 时生效）   |
| `send_sentence_night`   | 否  | （空）      | 晚安自定义句子列表（mode=1 时生效）   |
| `send_time_morning`     | 否  | `"7 0"`  | 早安推送时间，格式 `"时 分"`       |
| `send_time_night`       | 否  | `"22 0"` | 晚安推送时间，格式 `"时 分"`       |

说明：

- `send_mode=1` 时，使用自定义句子列表
- `send_mode=2` 时，使用插件内置随机句子逻辑（调用一言 API）
- `send_group_id` 支持 JSON 数组，也支持逗号分隔字符串

### 统计 ORM（推荐使用）

| 配置项                                      | 必填 | 默认值     |  推荐使用？ | 说明              |
| ---------------------------------------- | -- | ------- | :----: | --------------- |
| `statistics_orm_enabled`                 | 否  | `false` |   推荐   | 是否启用统计 ORM 存储，填写 `tortoise_orm_db_url` 后自动开启 |
| `statistics_orm_capture_message_content` | 否  | `true`  |   推荐   | ORM 启用时是否记录消息原文 |
| `tortoise_orm_db_url`                    | 否  | （空）     | <br /> | 数据库连接 URL       |

说明：

- 填写 `tortoise_orm_db_url` 后 `statistics_orm_enabled` 会自动设为 `true`，无需手动开启
- 消息记录会同时写入数据库
- 启用后插件会在初始化时自动检测历史文件数据并迁移至数据库，迁移记录通过数据库中的 MD5 去重，避免重复导入

#### `tortoise_orm_db_url` 填写示例

使用 SQLite 时，URL 格式为 `sqlite:///` 加数据库文件路径：

**Linux 示例**：

```env
tortoise_orm_db_url=sqlite:////home/bot/data/admin3-statistics.db
```

> 四个 `/`：`sqlite://` 是协议前缀，`/home/bot/data/admin3-statistics.db` 是绝对路径。

**Windows 示例**：

```env
tortoise_orm_db_url=sqlite:///C:/bot/data/admin3-statistics.db
```

> 三个 `/`：`sqlite://` 是协议前缀，`C:/bot/data/admin3-statistics.db` 是 Windows 绝对路径（盘符后用 `/` 代替 `\`）。

**相对路径示例**（相对于 NoneBot 工作目录）：

```env
tortoise_orm_db_url=sqlite:///data/admin3-statistics.db
```

### Dashboard（w）

| 配置项                                | 必填 | 默认值                | 说明                                     |
| ---------------------------------- | -- | ------------------ | -------------------------------------- |
| `dashboard_enabled`                | 否  | `false`            | 是否启用 Dashboard API                     |
| `dashboard_frontend_enabled`       | 否  | `false`            | 是否提供前端入口                               |
| `dashboard_base_path`              | 否  | `/admin-dashboard` | Dashboard 挂载路径                         |
| `dashboard_api_token`              | 否  | （空）                | API 鉴权 Token，非空时受保护接口需 `X-Admin-Token` |
| `dashboard_title`                  | 否  | `Admin Dashboard`  | Dashboard 页面标题                         |
| `dashboard_cors_allow_origins`     | 否  | （空）                | CORS 允许的来源，JSON 数组或逗号分隔                |
| `dashboard_cors_allow_credentials` | 否  | `false`            | CORS 是否允许携带凭证                          |
| `dashboard_log_file_path`          | 否  | （空）                | Dashboard 日志文件路径                       |

说明：

- `dashboard_enabled=true` 后会挂载 dashboard API
- `dashboard_frontend_enabled=true` 后会同时提供前端入口
- 若 `admin-web/dist` 存在，插件会优先提供 `admin-web` 构建产物
- 若 `dist` 不存在，插件会回退到仓库内保留的最小前端页面

## 命令概览

以下为当前版本的高层命令分类，详细矩阵建议查看 [`docs/README.md`](./docs/README.md)。

### 初始化

- `群管初始化`

### 基础群管

- `禁` / `解` / `改` / `踢` / `黑`
- `管理员+` / `管理员-`
- `头衔` / `删头衔`
- `撤回`
- `加精` / `取消精华`

### 入群审批

- `查看词条` / `词条+` / `词条-` / `词条拒绝`
- `所有词条` / `指定词条+` / `指定词条-`
- `分管` / `分管+` / `分管-` / `所有分管` / `接收`
- `请求同意xxx` / `请求拒绝xxx`
- `ai拒绝开` / `ai拒绝关` / `ai拒绝prompt`

**关于分管**：分管（副管理员）是本插件定义的角色，通过 `分管+` 命令由群管指定。分管不是 OneBot 官方管理员，但可以执行以下操作：禁言、解禁、全员禁言、改名、踢人、拉黑、加精、取消精华、撤回。分管**不能**设置管理员/取消管理员/设置头衔。

**词条审核与 AI 审核的区别**：

| 对比项 | 词条审核 | AI 审核 |
|--------|----------|---------|
| 触发方式 | 用户验证消息**包含**词条时自动同意 | AI 判断验证消息是否为广告/人机 |
| 判断逻辑 | 精确字符串匹配（词条在消息中即通过） | AI 语义理解，可识别变体和通用话术 |
| 拒绝能力 | 支持（`词条拒绝` 设置黑名单，匹配则拒绝） | 支持（AI 判定为广告直接拒绝） |
| 自定义规则 | 每群可设置不同的词条 | 每群可设置不同的自定义 prompt |
| 优先级 | 先执行词条审核，再执行 AI 审核 | 词条审核通过后才进入 AI 审核 |
| 适用场景 | 固定格式验证（如"答案：xxx"） | 开放式验证、防广告机器人 |

两者可以同时启用，互不冲突。词条审核优先处理，未命中词条的请求才会进入 AI 审核。

**AI 审核三级判断**（设置自定义 prompt 后生效）：

| AI 返回 | 含义 | 处理方式 |
|---------|------|----------|
| True | 广告/人机 | 直接拒绝 |
| False | 看起来像真人但不符合条件 | 放行给管理员人工处理 |
| Agree | 确定是真人且符合条件 | 机器人直接同意入群，并在群内通知 |

未设置自定义 prompt 时，AI 仅返回 True/False（二级判断，行为不变）。

**自定义 prompt 模板**：

通过 `ai拒绝prompt` 设置自定义规则后，AI 可根据规则直接同意符合条件的用户入群。模板示例：

```
ai拒绝prompt 本群的验证问题为"从哪里知道的本群？"如果用户的回答是一些社交平台，比如b站、bilibili、抖音等，或者包含xxx、xxx关键字时，则判定为直接同意。
```

说明：你可以强调某些条件让 AI 直接同意入群。注意**放行**和**直接同意**是两种不同的处理——放行指放行给管理员处理，直接同意指由机器人直接同意入群。

### 统计分析

- `记录本群` / `停止记录本群`
- `群词云` / `更新mask`
- `今日榜首` / `今日发言排行` / `昨日发言排行`
- `排行` / `发言数` / `今日发言数`

### 广播

- `广播`
- `广播排除`
- `群列表`
- `排除列表`
- `广播帮助`

说明：广播现在会先生成预览，只有再次确认后才会真正发送。

### 事件提醒

- `事件通知`
- `防撤回`

### 成员清理

- `成员清理`
- `清理解锁`

### Dashboard

- `面板地址` / `获取面板` / `dashboard地址`

说明：仅超级管理员可用，返回 Dashboard 访问地址及 Token 提示。

- `数据库地址`

说明：仅超级管理员可用，返回 ORM 数据库连接地址。未配置 `tortoise_orm_db_url` 时会提示配置方法。


## 感谢贡献者们
<!-- readme: BalconyJH,collaborators,contributors -start -->
<table>
	<tbody>
		<tr>
            <td align="center">
                <a href="https://github.com/balconyjh">
                    <img src="https://avatars.githubusercontent.com/u/73932916?v=4" width="100;" alt="balconyjh"/>
                    <br />
                    <sub><b>BalconyJH</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/lakwsh">
                    <img src="https://avatars.githubusercontent.com/u/13025769?v=4" width="100;" alt="lakwsh"/>
                    <br />
                    <sub><b>lakwsh</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/yzyyz1387">
                    <img src="https://avatars.githubusercontent.com/u/51691024?v=4" width="100;" alt="yzyyz1387"/>
                    <br />
                    <sub><b>幼稚园园长</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/tom-snow">
                    <img src="https://avatars.githubusercontent.com/u/79245287?v=4" width="100;" alt="tom-snow"/>
                    <br />
                    <sub><b>A lucky guy</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/NekoPunchs">
                    <img src="https://avatars.githubusercontent.com/u/41229611?v=4" width="100;" alt="NekoPunchs"/>
                    <br />
                    <sub><b>NekoPunch!</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/Redmomn">
                    <img src="https://avatars.githubusercontent.com/u/109732988?v=4" width="100;" alt="Redmomn"/>
                    <br />
                    <sub><b>脑袋里进花生了</b></sub>
                </a>
            </td>
		</tr>
		<tr>
            <td align="center">
                <a href="https://github.com/deepsourcebot">
                    <img src="https://avatars.githubusercontent.com/u/60907429?v=4" width="100;" alt="deepsourcebot"/>
                    <br />
                    <sub><b>DeepSource Bot</b></sub>
                </a>
            </td>
		</tr>
	<tbody>
</table>
<!-- readme: BalconyJH,collaborators,contributors -end -->
