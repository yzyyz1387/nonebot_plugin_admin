<template>
  <section class="admin-page">
    <div class="admin-section-card admin-hover-surface">
      <div class="admin-card-head">
        <h3 class="admin-card-title">日志中心</h3>
        <div class="admin-inline-meta">共 {{ formatNumber(totalCount) }} 条</div>
      </div>

      <div class="admin-card-content">
        <div class="admin-filter-bar">
          <div class="admin-filter-chips">
            <button
              v-for="item in levelOptions"
              :key="item.value"
              type="button"
              class="admin-filter-chip"
              :class="{ 'is-active': filters.level === item.value }"
              @click="changeLevel(item.value)"
            >
              {{ item.label }}
            </button>
          </div>

          <div class="admin-filter-chips mdui-m-t-1">
            <button
              v-for="item in sourceOptions"
              :key="item.value"
              type="button"
              class="admin-filter-chip"
              :class="{ 'is-active': filters.source === item.value }"
              @click="changeSource(item.value)"
            >
              {{ item.label }}
            </button>
          </div>

          <div v-if="filters.source === 'dashboard_oplog'" class="admin-filter-chips mdui-m-t-1">
            <button
              v-for="item in actionOptions"
              :key="item.key"
              type="button"
              class="admin-filter-chip"
              :class="{ 'is-active': filters.action === item.key }"
              @click="changeAction(item.key)"
            >
              {{ item.label }}
            </button>
          </div>

          <div class="admin-filter-actions">
            <div class="mdui-textfield admin-flat-field admin-search-field">
              <input v-model.trim="filters.keyword" class="mdui-textfield-input" type="text" placeholder="搜索模块、群号、消息内容" @keyup.enter="resetAndLoad()" />
            </div>
            <button class="mdui-btn mdui-ripple" type="button" @click="clearKeyword">清空</button>
            <button class="mdui-btn mdui-color-theme mdui-ripple" type="button" @click="resetAndLoad()">刷新</button>
          </div>
        </div>

        <div class="admin-quick-stats">
          <span class="admin-quick-stat">运行日志：{{ logsOverview.runtime_log_enabled ? '已启用' : '未启用' }}</span>
          <span class="admin-quick-stat">插件错误：{{ formatNumber(logsOverview.plugin_error_total) }}</span>
          <span class="admin-quick-stat">操作日志：{{ logsOverview.oplog_enabled ? `${formatNumber(logsOverview.oplog_total || 0)} 条` : '未启用' }}</span>
        </div>
      </div>
    </div>

    <div class="admin-section-card admin-hover-surface mdui-m-t-2 admin-log-terminal-card">
      <div class="admin-log-terminal-bar">
        <span class="admin-log-terminal-title">Terminal</span>
        <span class="admin-log-terminal-meta">{{ formatNumber(totalCount) }} 条记录</span>
      </div>

      <div class="admin-log-indeterminate-bar" :class="{ 'is-active': loadingMore || loading }">
        <div class="admin-log-indeterminate-bar-inner"></div>
      </div>

      <div ref="terminalRef" class="admin-log-terminal" :class="{ 'is-ready': terminalReady }" @scroll="onTerminalScroll" @wheel="onTerminalWheel">
        <div class="admin-log-load-hint" :class="{ 'is-visible': showLoadHint, 'is-loading': loadingMore }">
          <template v-if="loadingMore">加载更早日志...</template>
          <template v-else>继续上划以加载更多日志</template>
        </div>

        <div v-for="item in displayItems" :key="item.id" class="admin-log-line">
          <span class="admin-log-timestamp">{{ formatTimestamp(item.timestamp) }}</span>
          <span class="admin-log-level" :class="'is-' + (item.level || 'INFO').toLowerCase()">[{{ item.level || 'INFO' }}]</span>
          <span class="admin-log-module">{{ formatModule(item) }}</span>
          <span v-if="item.group_id" class="admin-log-group">| 群:{{ item.group_id }}</span>
          <span v-if="item.user_id" class="admin-log-user">| 用户:{{ item.user_id }}</span>
          <span class="admin-log-content">{{ item.detail || item.message || '' }}</span>
        </div>

        <div v-if="!displayItems.length && !loading" class="admin-log-empty">
          暂无匹配日志
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { apiRequest, extractErrorMessage } from '../lib/api'
import { formatNumber } from '../lib/format'

const props = defineProps({
  apiBase: { type: String, required: true },
  token: { type: String, default: '' },
  active: { type: Boolean, default: false },
  refreshKey: { type: Number, default: 0 }
})

const emit = defineEmits(['notify', 'connection'])

const loading = ref(false)
const loadingMore = ref(false)
const allItems = ref([])
const currentPage = ref(1)
const hasOlder = ref(true)
const totalCount = ref(0)
const filters = reactive({ level: '', keyword: '', source: '', action: '' })
const actionOptionsData = ref([])
const sourcesData = ref([])
const logsOverview = reactive({ runtime_log_enabled: false, runtime_log_total: 0, plugin_error_total: 0, runtime_log_file_path: '', oplog_enabled: false, oplog_total: 0 })

const terminalRef = ref(null)
const terminalReady = ref(false)
const showLoadHint = ref(false)

const displayItems = computed(() => {
  return [...allItems.value].reverse()
})

const levelOptions = computed(() => [
  { label: '全部', value: '' },
  { label: 'ERROR', value: 'ERROR' },
  { label: 'WARNING', value: 'WARNING' },
  { label: 'INFO', value: 'INFO' },
  { label: 'SUCCESS', value: 'SUCCESS' },
  { label: 'DEBUG', value: 'DEBUG' }
])

const sourceOptions = computed(() => {
  const sources = sourcesData.value || []
  const opts = [{ label: '全部来源', value: '' }]
  for (const s of sources) {
    opts.push({ label: `${s.label}${s.enabled ? '' : ' (未启用)'}`, value: s.key })
  }
  return opts
})

const actionOptions = computed(() => {
  const options = actionOptionsData.value || []
  return [{ key: '', label: '全部操作' }, ...options]
})

function formatTimestamp(ts) {
  if (!ts) return '--:--:--'
  try {
    const d = new Date(ts)
    if (isNaN(d.getTime())) return String(ts).slice(0, 19)
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const hh = String(d.getHours()).padStart(2, '0')
    const mi = String(d.getMinutes()).padStart(2, '0')
    const ss = String(d.getSeconds()).padStart(2, '0')
    return `${mm}-${dd} ${hh}:${mi}:${ss}`
  } catch {
    return String(ts).slice(0, 19)
  }
}

function formatModule(item) {
  if (item.source === 'dashboard_oplog') {
    return item.action_label || item.action || '操作日志'
  }
  return item.module || item.source || '--'
}

function scrollToBottom() {
  nextTick(() => {
    setTimeout(() => {
      const el = terminalRef.value
      if (el) el.scrollTop = el.scrollHeight
      terminalReady.value = true
    }, 60)
  })
}

async function loadPage(page, append = false) {
  if (!append) {
    loading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    const isOplogMode = filters.source === 'dashboard_oplog'
    let newItems = []
    let pagination = {}
    let overviewPayload = null

    if (isOplogMode) {
      const [overview, oplogPayload] = await Promise.all([
        apiRequest(props.apiBase, props.token, '/logs/overview'),
        apiRequest(props.apiBase, props.token, '/oplog', {
          params: {
            page,
            page_size: 50,
            action: filters.action,
            level: filters.level,
            keyword: filters.keyword
          }
        })
      ])
      overviewPayload = overview
      const oplogData = oplogPayload || {}
      newItems = oplogData.items || []
      pagination = oplogData.pagination || {}
      actionOptionsData.value = oplogData.action_options || []
    } else {
      const [overview, logsPayload] = await Promise.all([
        apiRequest(props.apiBase, props.token, '/logs/overview'),
        apiRequest(props.apiBase, props.token, '/logs', {
          params: {
            page,
            page_size: 50,
            level: filters.level,
            keyword: filters.keyword,
            source: filters.source
          }
        })
      ])
      overviewPayload = overview
      const logsData = logsPayload || {}
      newItems = logsData.items || []
      pagination = logsData.pagination || {}
      actionOptionsData.value = []
    }

    if (overviewPayload) {
      Object.assign(logsOverview, overviewPayload)
      sourcesData.value = overviewPayload.sources || sourcesData.value
    }

    if (append) {
      const existingIds = new Set(allItems.value.map(i => i.id))
      const uniqueNew = newItems.filter(i => !existingIds.has(i.id))
      allItems.value = [...allItems.value, ...uniqueNew]
    } else {
      allItems.value = newItems
    }

    currentPage.value = pagination.page || page
    totalCount.value = pagination.total || 0
    hasOlder.value = pagination.has_next || false

    if (!append) {
      scrollToBottom()
    }

    emit('connection', '已连接')
  } catch (error) {
    emit('connection', '连接失败')
    emit('notify', { message: `日志加载失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function onTerminalScroll() {
  const el = terminalRef.value
  if (!el) return
  if (el.scrollTop <= 5 && hasOlder.value && !loadingMore.value) {
    showLoadHint.value = true
  } else {
    showLoadHint.value = false
  }
}

function onTerminalWheel(e) {
  const el = terminalRef.value
  if (!el || loadingMore.value || !hasOlder.value) return
  if (el.scrollTop <= 0 && e.deltaY < 0) {
    e.preventDefault()
    const prevHeight = el.scrollHeight
    loadPage(currentPage.value + 1, true).then(() => {
      nextTick(() => {
        const newHeight = el.scrollHeight
        el.scrollTop = newHeight - prevHeight
      })
    })
  }
}

function resetAndLoad() {
  allItems.value = []
  currentPage.value = 1
  hasOlder.value = true
  terminalReady.value = false
  showLoadHint.value = false
  loadPage(1, false)
}

function changeLevel(level) {
  filters.level = level
  resetAndLoad()
}

function changeSource(source) {
  filters.source = source
  filters.action = ''
  resetAndLoad()
}

function changeAction(action) {
  filters.action = action
  resetAndLoad()
}

function clearKeyword() {
  filters.keyword = ''
  resetAndLoad()
}

watch(
  () => [props.active, props.refreshKey],
  ([active]) => {
    if (!active) return
    resetAndLoad()
  },
  { immediate: true }
)
</script>
