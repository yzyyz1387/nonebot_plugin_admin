# 开发说明

适用范围：`nonebot_plugin_admin`

## 项目结构

```
nonebot_plugin_admin/
├── approval/            入群审批与 AI 审核
├── basic_group_admin/   基础群管（禁言、踢人、头衔、精华、撤回）
├── broadcasting/        广播
├── content_guard/       内容审核（违禁词 + 图片审核）
├── core/                公共层（配置、路径、开关、工具函数）
├── dashboard/           Web 管理面板（FastAPI + 内置前端）
├── event_notice/        事件通知（撤回转发、特定事件提醒）
├── member_cleanup/      成员清理
├── migration/           本地数据迁移（JSON → ORM）
├── statistics/          统计分析（发言记录、排行、词云）
├── util/                通用工具
├── admin-web/           独立前端工程（Vue + Vite，构建后嵌入 dashboard）
├── docs/                文档
└── scripts/             测试与运维脚本
```

每个业务域内部通常按以下模式拆分：

| 后缀 | 职责 |
|------|------|
| `*_store.py` | 数据读写 |
| `*_flow.py` | 业务逻辑 |
| `*_text.py` | 提示文案 |
| matcher 文件 | NoneBot 命令/事件注册 |

## 开发环境

1. 克隆仓库后安装依赖：

```bash
pip install -r requirements.txt
```

2. 如需前端开发，进入 `admin-web/` 安装 Node 依赖：

```bash
cd admin-web && npm install
```

3. 在 NoneBot 项目的 `.env` 中配置插件所需环境变量，参考 README.md。

## 测试脚本

`scripts/` 目录下存放烟雾检查脚本，用于在不启动完整机器人服务的前提下，快速验证各业务域的核心逻辑和 matcher 注册是否正常。

### 运行方式

在项目根目录执行：

```bash
python scripts/<脚本名>.py
```

所有脚本通过 `asyncio.run()` 直接运行，无需 pytest 或 nonebug。脚本内部会自行完成 NoneBot 初始化、模块加载和临时目录隔离，不会污染本地数据。

### 脚本说明

| 脚本 | 覆盖域 | 验证内容 |
|------|--------|----------|
| `approval_smoke_check.py` | 审批 | 审批词条增删、黑名单管理、分群管理员、AI 审核开关与 prompt、入群请求处理、matcher 注册与权限 |
| `basic_admin_smoke_check.py` | 基础群管 | 禁言时长解析、踢人逻辑、管理员设置、精华消息、撤回流程、matcher 注册 |
| `content_guard_smoke_check.py` | 内容审核 | 违禁词匹配（含正则、仅撤回、仅禁言、群限定、排除词）、图片审核结果判定与处罚、matcher 注册 |
| `member_cleanup_smoke_check.py` | 成员清理 | 锁机制、等级/发言时间筛选、清理执行、预览构建、matcher 注册 |
| `statistics_smoke_check.py` | 统计分析 | 记录开关、消息记录与统计、ORM 读写、停用词、排行构建、词云生成、定时消息、matcher 注册与权限 |
| `event_notice_smoke_check.py` | 事件通知 | 撤回转发判定与消息构建、各类通知事件识别与消息构建、matcher 注册 |
| `dashboard_smoke_check.py` | 管理面板 | 完整插件加载、FastAPI TestClient 验证所有 API 端点、前端页面、操作（禁言/踢人/头衔/广播/开关） |
| `integration_smoke_check.py` | 集成 | 插件完整加载、`__init__` 入口、模块注册、启动初始化、开关完整性检查 |

### 运维脚本

| 脚本 | 用途 |
|------|------|
| `statistics_orm_import.py` | 将本地 JSON/TXT 统计数据导入 ORM 数据库。需要已安装 `nonebot_plugin_tortoise_orm` 并在环境中开启 `statistics_orm_enabled` |

运行方式：

```bash
python scripts/statistics_orm_import.py
```

可通过环境变量覆盖默认配置：

```bash
tortoise_orm_db_url=sqlite:///data/admin-stats.db statistics_orm_enabled=true python scripts/statistics_orm_import.py
```

### 建议的检查顺序

改动后建议按以下顺序验证：

1. 先运行改动所在业务域的 smoke check
2. 再运行 `integration_smoke_check.py` 确认整体加载无异常
3. 如涉及面板，运行 `dashboard_smoke_check.py`

## 群管菜单

发送 **群管菜单** 即可查看所有可用命令，以 HTML 截图形式展示，截图失败时自动降级为文字。权限不限，所有人可用。

### 菜单注册机制

菜单项通过 `core/menu_registry.py` 提供的 `menu_registry` 单例管理，支持两种注册方式：

**方式一**：在 `core/menu_items.py` 中追加（推荐，集中管理）

```python
_reg.register("分类名", "命令名", "用法说明", permission="管理员", aliases=["别名1", "别名2"])
```

**方式二**：在新功能模块中直接调用

```python
from ..core.menu_registry import menu_registry
menu_registry.register("分类名", "命令名", "用法说明", permission="管理员")
```

`permission` 参数用于菜单展示，可选值：`所有人`、`管理员`、`群主`、`超管`。新增分类只需首次使用新的 `category` 名称即可自动创建。

### 相关文件

| 文件 | 职责 |
|------|------|
| `core/menu_registry.py` | 菜单注册中心（`MenuRegistry`、`MenuItem`、`MenuCategory`） |
| `core/menu_items.py` | 集中注册所有菜单项，模块导入时自动执行 |
| `core/menu_command.py` | `群管菜单` 命令处理，HTML 渲染截图 |
| `core/menu.html` | Jinja2 模板，卡片式布局按分类展示 |

## 提交 PR

1. Fork 仓库并创建特性分支
2. 确保改动所在业务域的 smoke check 通过
3. 运行 `integration_smoke_check.py` 确认无回归
4. 如涉及面板 API 变更，运行 `dashboard_smoke_check.py`
5. 提交 PR 并描述改动范围和测试结果

## 可选依赖

部分功能依赖可选包，缺失时对应功能退化而非报错：

| 依赖 | 功能 | 缺失影响 |
|------|------|----------|
| `pyppeteer` | 截图渲染 | 开关状态/词云退回文字模式 |
| `nonebot_plugin_apscheduler` | 定时群消息 | 早安晚安不可用 |
| `wordcloud` + `jieba` | 词云图片 | 群词云不可用 |
| `tencentcloud-sdk-python` | 图片审核 | 被动图片审核失效 |
| `openai` | AI 入群审核 | AI 审核功能失效 |
| `nonebot_plugin_tortoise_orm` | ORM 统计 | 统计数据退回本地 JSON |
