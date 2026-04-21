<template>
  <section class="admin-page">
    <LoadingBar :loading="loading" />

    <div class="admin-bot-header">
      <div class="admin-bot-avatar">
        <span>{{ initials(account.nickname || 'Bot') }}</span>
      </div>
      <div class="admin-bot-info">
        <div class="admin-bot-name">{{ account.nickname || '机器人' }}</div>
        <div class="admin-bot-id">{{ account.self_id || '--' }}</div>
      </div>
      <div class="admin-bot-status">
        <span class="admin-status-dot" :class="account.online ? 'is-connected' : 'is-disconnected'"></span>
        <span>{{ account.online ? '在线' : '离线' }}</span>
      </div>
      <div class="admin-bot-stats">
        <div class="admin-bot-stat">
          <span class="admin-bot-stat-value">{{ formatNumber(visibleGroupCount) }}</span>
          <span class="admin-bot-stat-label">群数</span>
        </div>
        <div class="admin-bot-stat">
          <span class="admin-bot-stat-value">{{ formatNumber(account.friend_count) }}</span>
          <span class="admin-bot-stat-label">好友</span>
        </div>
        <div class="admin-bot-stat">
          <span class="admin-bot-stat-value">{{ formatNumber(todayMessageTotal) }}</span>
          <span class="admin-bot-stat-label">今日消息</span>
        </div>
        <div class="admin-bot-stat">
          <span class="admin-bot-stat-value">{{ formatNumber(activeMemberTotal) }}</span>
          <span class="admin-bot-stat-label">活跃成员</span>
        </div>
        <div class="admin-bot-stat">
          <span class="admin-bot-stat-value">{{ formatNumber(manageableGroupCount) }}</span>
          <span class="admin-bot-stat-label">可管理群</span>
        </div>
        <div class="admin-bot-stat">
          <span class="admin-bot-stat-value">{{ formatNumber(account.client_count) }}</span>
          <span class="admin-bot-stat-label">客户端</span>
        </div>
      </div>
    </div>

    <div class="admin-dashboard-grid mdui-m-t-2">
      <div class="admin-section-card admin-hover-surface admin-span-8">
        <div class="admin-card-head">
          <h3 class="admin-card-title">7 日趋势</h3>
          <div class="admin-inline-meta">{{ formatDateTime(overview.generated_at) }}</div>
        </div>
        <div class="admin-card-content">
          <v-chart v-if="trendItems.length" class="admin-chart" :option="trendOption" autoresize />
          <EmptyState v-else icon="insights" title="暂无趋势数据" description="当前没有可用统计。" />
        </div>
      </div>

      <div class="admin-section-card admin-hover-surface admin-span-4 admin-chart-match-trend">
        <div class="admin-card-head">
          <h3 class="admin-card-title">群管理构成</h3>
        </div>
        <div class="admin-card-content">
          <v-chart v-if="visibleGroupCount" class="admin-chart" :option="manageOption" autoresize />
          <EmptyState v-else icon="pie_chart" title="暂无分布数据" description="当前没有可用群组。" />
        </div>
      </div>

      <div class="admin-section-card admin-hover-surface admin-span-6">
        <div class="admin-card-head">
          <h3 class="admin-card-title">活跃群排行</h3>
        </div>
        <div class="admin-card-content">
          <v-chart v-if="topGroupRows.length" class="admin-chart admin-chart-compact" :option="topGroupsOption" autoresize />
          <EmptyState v-else icon="leaderboard" title="暂无群排行" description="当前没有可用群统计。" />
        </div>
      </div>

      <div class="admin-section-card admin-hover-surface admin-span-6">
        <div class="admin-card-head">
          <h3 class="admin-card-title">最近会话</h3>
        </div>
        <div class="admin-card-content">
          <div v-if="recentContacts.length" class="admin-tab-list">
            <div v-for="item in recentContacts" :key="`${item.chat_kind || item.chatType}-${item.peer_id || item.peerUin}-${item.message_id || item.msgId}`" class="admin-list-item">
              <div class="admin-list-item-avatar">{{ initials(item.title || item.peer_name || item.peerName) }}</div>
              <div class="admin-list-item-content">
                <div class="admin-list-item-title">{{ item.title || item.peer_name || item.peerName || '未命名会话' }}</div>
                <div class="admin-list-item-sub">{{ item.preview || item.last_message || '暂无文本预览' }}</div>
              </div>
            </div>
          </div>
          <EmptyState v-else icon="chat_bubble_outline" title="暂无最近会话" description="当前没有最近会话数据。" />
        </div>
      </div>

      <div class="admin-section-card admin-hover-surface admin-span-12">
        <div class="admin-card-head">
          <h3 class="admin-card-title">今日高活跃群</h3>
        </div>
        <div class="admin-card-content admin-table-wrap">
          <table v-if="topGroupRows.length" class="mdui-table mdui-table-hoverable">
            <thead>
              <tr>
                <th>群名</th>
                <th>群号</th>
                <th class="mdui-table-col-numeric">今日消息</th>
                <th class="mdui-table-col-numeric">历史消息</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in topGroupRows" :key="item.group_id">
                <td>{{ item.group_name }}</td>
                <td>{{ item.group_id }}</td>
                <td class="mdui-table-col-numeric">{{ formatNumber(item.today_message_count) }}</td>
                <td class="mdui-table-col-numeric">{{ formatNumber(item.history_message_count) }}</td>
              </tr>
            </tbody>
          </table>
          <EmptyState v-else icon="forum" title="暂无群组数据" description="当前没有可以展示的群统计排行。" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import EmptyState from '../components/common/EmptyState.vue'
import LoadingBar from '../components/common/LoadingBar.vue'
import { apiRequest, extractErrorMessage } from '../lib/api'
import { formatDateTime, formatNumber, initials, isPlaceholderGroupRecord, isPlaceholderGroupName, sumBy } from '../lib/format'

use([CanvasRenderer, LineChart, BarChart, PieChart, TooltipComponent, GridComponent, LegendComponent])

const props = defineProps({
  apiBase: { type: String, required: true },
  token: { type: String, default: '' },
  active: { type: Boolean, default: false },
  refreshKey: { type: Number, default: 0 }
})

const emit = defineEmits(['notify', 'connection'])

const loading = ref(false)
const overview = reactive({
  group_count: 0,
  today_message_count: 0,
  active_members: 0,
  top_groups: [],
  daily_trend: [],
  generated_at: null
})
const operations = reactive({ manageable_group_count: 0 })
const account = reactive({ available: false, online: false, nickname: '', self_id: '', friend_count: 0, client_count: 0 })
const contacts = reactive({ items: [] })
const logsOverview = reactive({ runtime_log_enabled: false, runtime_log_file_path: null, plugin_error_total: 0, runtime_log_total: 0, total: 0 })
const groups = ref([])

const realGroups = computed(() => (groups.value || []).filter((item) => !isPlaceholderGroupRecord(item)))
const visibleGroupCount = computed(() => realGroups.value.length)
const activeMemberTotal = computed(() => sumBy(realGroups.value, 'active_members'))
const topGroupRows = computed(() => [...realGroups.value].sort((a, b) => Number(b.today_message_count || 0) - Number(a.today_message_count || 0)).slice(0, 8))
const todayMessageTotal = computed(() => {
  const sum = sumBy(realGroups.value, 'today_message_count')
  return sum || Number(overview.today_message_count || 0)
})
const manageableGroupCount = computed(() => {
  const raw = Number(operations.manageable_group_count || 0)
  return visibleGroupCount.value ? Math.min(raw, visibleGroupCount.value) : raw
})
const recentContacts = computed(() => (contacts.items || []).filter((item) => !isPlaceholderGroupName(item.title || item.peer_name || item.peerName || '')).slice(0, 8))
const trendItems = computed(() => (overview.daily_trend || []).slice(-7))

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { top: 0, right: 0 },
  grid: { left: 44, right: 16, top: 36, bottom: 24 },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: trendItems.value.map((item) => String(item.date || '').slice(5) || item.date),
    axisTick: { show: false }
  },
  yAxis: [
    {
      type: 'value',
      splitLine: { lineStyle: { color: '#eceff1' } }
    },
    {
      type: 'value',
      splitLine: { show: false }
    }
  ],
  series: [
    {
      name: '消息量',
      type: 'line',
      smooth: true,
      symbolSize: 6,
      areaStyle: { opacity: 0.08 },
      data: trendItems.value.map((item) => Number(item.message_count || 0))
    },
    {
      name: '活跃成员',
      type: 'line',
      smooth: true,
      symbolSize: 6,
      yAxisIndex: 1,
      data: trendItems.value.map((item) => Number(item.active_members || 0))
    }
  ]
}))

const topGroupsOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 96, right: 16, top: 16, bottom: 16 },
  xAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#eceff1' } }
  },
  yAxis: {
    type: 'category',
    axisTick: { show: false },
    data: [...topGroupRows.value].reverse().map((item) => item.group_name)
  },
  series: [
    {
      type: 'bar',
      barWidth: 16,
      data: [...topGroupRows.value].reverse().map((item) => Number(item.today_message_count || 0))
    }
  ]
}))

const manageOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [
    {
      type: 'pie',
      radius: ['52%', '74%'],
      avoidLabelOverlap: false,
      label: { formatter: '{b}\n{c}' },
      data: [
        { name: '可管理', value: Math.max(0, manageableGroupCount.value) },
        { name: '其他', value: Math.max(0, visibleGroupCount.value - manageableGroupCount.value) }
      ]
    }
  ]
}))

async function loadData() {
  loading.value = true
  try {
    const [overviewPayload, operationsPayload, accountPayload, contactsPayload, logsPayload, groupsPayload] = await Promise.all([
      apiRequest(props.apiBase, props.token, '/overview'),
      apiRequest(props.apiBase, props.token, '/operations/overview'),
      apiRequest(props.apiBase, props.token, '/account/overview'),
      apiRequest(props.apiBase, props.token, '/contacts/recent', { params: { count: 8 } }),
      apiRequest(props.apiBase, props.token, '/logs/overview'),
      apiRequest(props.apiBase, props.token, '/groups')
    ])

    Object.assign(overview, overviewPayload || {})
    Object.assign(operations, operationsPayload || {})
    Object.assign(account, accountPayload || {})
    Object.assign(contacts, contactsPayload || {})
    Object.assign(logsOverview, logsPayload || {})
    groups.value = Array.isArray(groupsPayload?.items) ? groupsPayload.items : []
    emit('connection', '已连接')
  } catch (error) {
    emit('connection', '连接失败')
    emit('notify', { message: `首页数据加载失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.active, props.refreshKey],
  ([active]) => {
    if (!active) return
    loadData()
  },
  { immediate: true }
)
</script>
