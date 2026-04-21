# admin-web

基于 **Vue 3 + Vite + MDUI v1 (`mdui@1.0.2`) + ECharts** 的 NoneBot2 管理后台前端工程。

这版是在上一版基础上继续重构的，重点是把整体壳子改成更规整的后台结构：顶部应用栏、左侧可折叠导航、数据面板图表化、操作台三栏布局、底部完整功能开关区，并且统一压低圆角和装饰感。

## 这次调整

1. 左侧导航改成 **可折叠侧栏**
   - 顶部三条横线控制展开 / 折叠
   - 折叠后保留一列图标
   - 移动端自动切换为抽屉式侧栏

2. 去掉全站这类“标题下解释说明”的提示文案
   - 不再出现“聊天窗口 / 中间区域固定在页面中...”这类辅助说明

3. 操作台结构重新整理
   - 顶部先显示群信息摘要
   - 中间固定为三栏：群列表 / 聊天窗口 / 群成员
   - 底部单独展示 **完整功能开关**
   - 功能开关不再放在独立滚动容器里，而是直接完整渲染在页面下方

4. 群过滤逻辑统一
   - 所有界面都过滤群名形如 `?123456` / `？123456` 的占位群
   - 数据面板和操作台都不再显示这些群

5. 数据面板增加图表
   - 使用 `vue-echarts + echarts`
   - 当前包含：7 日趋势、群管理构成、活跃群排行

6. 交互强化
   - 卡片、列表、导航、消息气泡都补了 hover 效果
   - 请求加载统一加入 **不确定进度条**

7. 设置弹窗输入框修正
   - 改为非浮动输入结构，避免输入内容和提示文本重叠

## 使用到的后端 API

本项目直接对接你当前已经整理好的 dashboard API：

- `GET /meta`
- `GET /overview`
- `GET /operations/overview`
- `GET /logs/overview`
- `GET /logs`
- `GET /account/overview`
- `GET /contacts/recent`
- `GET /groups`
- `GET /groups/{group_id}/workspace`
- `GET /groups/{group_id}/messages`
- `POST /groups/{group_id}/messages`
- `GET /groups/{group_id}/members`
- `POST /groups/{group_id}/feature-switches/{switch_key}`
- `POST /groups/{group_id}/actions/mark-read`
- `POST /groups/{group_id}/actions/whole-ban`
- `POST /groups/{group_id}/actions/mute`
- `POST /groups/{group_id}/actions/kick`
- `POST /groups/{group_id}/actions/special-title`

## 开发

```bash
npm install
npm run dev
```

## 构建

```bash
npm run build
```

构建产物输出到：

```bash
dist/
```

## 与插件集成

你当前插件的前端静态资源优先会读取：

```text
admin-web/dist
```

所以接入方式就是：

1. 把本项目目录命名为 `admin-web`
2. 放到插件项目根目录
3. 执行 `npm install && npm run build`
4. 确保最终存在 `admin-web/dist`

## 接口设置

页面右上角设置按钮支持：

- API Base
- `X-Admin-Token`

常见 API Base：

```text
/admin-dashboard/api
```
