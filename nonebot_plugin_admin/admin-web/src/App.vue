<template>
  <div v-if="!isAuthenticated" class="admin-root mdui-theme-primary-indigo mdui-theme-accent-blue" :class="themeLayoutClass">
    <LoginPage @login="handleLogin" />
  </div>
  <div v-else class="admin-root mdui-theme-primary-indigo mdui-theme-accent-blue" :class="themeLayoutClass">
    <AppHeader
      :title="title"
      :page-label="pageLabel"
      :connection-text="connectionText"
      :theme-mode="themeMode"
      @refresh="refreshCurrentPage"
      @open-config="showConfig = true"
      @toggle-nav="toggleSidebar"
      @toggle-theme="toggleTheme"
    />

    <ConfigDialog
      :open="showConfig"
      :api-base="settings.apiBase"
      :token="settings.token"
      @close="showConfig = false"
      @save="saveConfig"
    />

    <div class="admin-shell" :class="{ 'is-sidebar-collapsed': desktopSidebarCollapsed, 'is-sidebar-hover': sidebarHoverExpand, 'is-mobile-nav-open': showMobileNav }">
      <aside class="admin-sidebar" :class="{ 'is-collapsed': desktopSidebarCollapsed, 'is-hover-expand': sidebarHoverExpand, 'is-mobile-open': showMobileNav && !isDesktop }"
        @mouseenter="onSidebarEnter"
        @mouseleave="onSidebarLeave"
      >
        <div class="admin-sidebar-scroll">
          <button
            v-for="item in pages"
            :key="item.key"
            type="button"
            class="admin-sidebar-item mdui-ripple"
            :class="{ 'is-active': currentPage === item.key }"
            @click="setPage(item.key)"
          >
            <i class="material-icons">{{ item.icon }}</i>
            <span class="admin-sidebar-text">{{ item.label }}</span>
          </button>
        </div>
      </aside>

      <div v-if="showMobileNav && !isDesktop" class="admin-sidebar-backdrop" @click="showMobileNav = false"></div>

      <main class="admin-app-main" :class="{ 'is-sidebar-collapsed': desktopSidebarCollapsed }">
        <DashboardPage
          v-show="currentPage === 'dashboard'"
          :api-base="settings.apiBase"
          :token="settings.token"
          :active="currentPage === 'dashboard'"
          :refresh-key="refreshKey"
          @notify="notify"
          @connection="updateConnection"
        />
        <LogsPage
          v-show="currentPage === 'logs'"
          :api-base="settings.apiBase"
          :token="settings.token"
          :active="currentPage === 'logs'"
          :refresh-key="refreshKey"
          @notify="notify"
          @connection="updateConnection"
        />
        <WorkspacePage
          v-show="currentPage === 'workspace'"
          :api-base="settings.apiBase"
          :token="settings.token"
          :active="currentPage === 'workspace'"
          :refresh-key="refreshKey"
          @notify="notify"
          @connection="updateConnection"
        />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import AppHeader from './components/common/AppHeader.vue'
import ConfigDialog from './components/common/ConfigDialog.vue'
import DashboardPage from './pages/DashboardPage.vue'
import LogsPage from './pages/LogsPage.vue'
import WorkspacePage from './pages/WorkspacePage.vue'
import LoginPage from './pages/LoginPage.vue'
import { DEFAULT_API_BASE, DEFAULT_DASHBOARD_TITLE, DASHBOARD_BOOTSTRAP, apiRequest, extractErrorMessage, normalizeApiBase } from './lib/api'

const STORAGE_KEYS = {
  apiBase: 'nb-admin-web:api-base',
  token: 'nb-admin-web:session-token',
  tokenTs: 'nb-admin-web:session-token-ts',
  page: 'nb-admin-web:page',
  sidebar: 'nb-admin-web:sidebar-collapsed',
  theme: 'nb-admin-web:theme'
}

var TOKEN_TTL_MS = 24 * 60 * 60 * 1000

const pages = [
  { key: 'dashboard', label: '数据面板', icon: 'dashboard' },
  { key: 'logs', label: '日志中心', icon: 'description' },
  { key: 'workspace', label: '操作台', icon: 'forum' }
]

function restoreSessionToken() {
  try {
    var ts = window.sessionStorage.getItem(STORAGE_KEYS.tokenTs)
    if (ts && Date.now() - parseInt(ts, 10) > TOKEN_TTL_MS) {
      window.sessionStorage.removeItem(STORAGE_KEYS.token)
      window.sessionStorage.removeItem(STORAGE_KEYS.tokenTs)
      return ''
    }
    return window.sessionStorage.getItem(STORAGE_KEYS.token) || ''
  } catch (error) {
    return ''
  }
}

function persistSessionToken(token) {
  try {
    if (token) {
      window.sessionStorage.setItem(STORAGE_KEYS.token, token)
      window.sessionStorage.setItem(STORAGE_KEYS.tokenTs, String(Date.now()))
    } else {
      window.sessionStorage.removeItem(STORAGE_KEYS.token)
      window.sessionStorage.removeItem(STORAGE_KEYS.tokenTs)
    }
  } catch (error) {
    // ignore
  }
}

const settings = reactive({
  apiBase: normalizeApiBase(localStorage.getItem(STORAGE_KEYS.apiBase) || DEFAULT_API_BASE),
  token: restoreSessionToken()
})

const isAuthenticated = ref(!!settings.token)
const meta = reactive({
  title: DEFAULT_DASHBOARD_TITLE,
  base_path: DASHBOARD_BOOTSTRAP.basePath || '',
  auth_required: !!DASHBOARD_BOOTSTRAP.authRequired,
  frontend_enabled: true
})
const currentPage = ref(resolvePage())
const connectionText = ref('未连接')
const refreshKey = ref(0)
const showConfig = ref(false)
const showMobileNav = ref(false)
const isDesktop = ref(window.innerWidth >= 1024)
const sidebarCollapsed = ref(localStorage.getItem(STORAGE_KEYS.sidebar) === '1')
const themeMode = ref(localStorage.getItem(STORAGE_KEYS.theme) || 'light')
const sidebarHoverExpand = ref(false)

const title = computed(() => meta.title || DEFAULT_DASHBOARD_TITLE)
const pageLabel = computed(() => pages.find((item) => item.key === currentPage.value)?.label || '数据面板')
const desktopSidebarCollapsed = computed(() => isDesktop.value && sidebarCollapsed.value)
const themeLayoutClass = computed(() => {
  if (themeMode.value === 'dark') return 'mdui-theme-layout-dark'
  return ''
})

function resolvePage() {
  const hash = String(window.location.hash || '').replace(/^#/, '')
  if (pages.some((item) => item.key === hash)) return hash
  const cached = localStorage.getItem(STORAGE_KEYS.page) || 'dashboard'
  return pages.some((item) => item.key === cached) ? cached : 'dashboard'
}

function handleLogin(token) {
  settings.token = token
  persistSessionToken(token)
  isAuthenticated.value = true
  loadMeta()
}

function updateConnection(text) {
  connectionText.value = text || '未连接'
}

function notify(payload) {
  const message = typeof payload === 'string' ? payload : payload?.message
  if (!message) return
  if (window.mdui?.snackbar) {
    window.mdui.snackbar({
      message,
      timeout: payload?.type === 'error' ? 5000 : 3000,
      position: 'right-top'
    })
  } else {
    console.log(message)
  }
}

function setPage(page) {
  currentPage.value = page
  window.location.hash = page
  localStorage.setItem(STORAGE_KEYS.page, page)
  if (!isDesktop.value) showMobileNav.value = false
}

function refreshCurrentPage() {
  refreshKey.value += 1
  loadMeta()
}

async function loadMeta() {
  try {
    const payload = await apiRequest(settings.apiBase, settings.token, '/meta')
    Object.assign(meta, payload || {})
    document.title = meta.title || DEFAULT_DASHBOARD_TITLE
    connectionText.value = '已连接'
    if (meta.auth_required && !settings.token) {
      isAuthenticated.value = false
    }
  } catch (error) {
    if (error.status === 401) {
      isAuthenticated.value = false
      persistSessionToken('')
      return
    }
    connectionText.value = '未连接'
    notify({ message: `Meta 加载失败：${extractErrorMessage(error)}`, type: 'error' })
  }
}

function saveConfig(payload) {
  settings.apiBase = normalizeApiBase(payload.apiBase)
  settings.token = String(payload.token || '').trim()
  localStorage.setItem(STORAGE_KEYS.apiBase, settings.apiBase)
  persistSessionToken(settings.token)
  isAuthenticated.value = !!settings.token || !meta.auth_required
  showConfig.value = false
  notify('配置已保存。')
  refreshCurrentPage()
}

function syncViewport() {
  isDesktop.value = window.innerWidth >= 1024
  if (isDesktop.value) {
    showMobileNav.value = false
  }
}

function toggleSidebar() {
  if (isDesktop.value) {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem(STORAGE_KEYS.sidebar, sidebarCollapsed.value ? '1' : '0')
    return
  }
  showMobileNav.value = !showMobileNav.value
}

function onSidebarEnter() {
  if (isDesktop.value && desktopSidebarCollapsed.value) {
    sidebarHoverExpand.value = true
  }
}

function onSidebarLeave() {
  sidebarHoverExpand.value = false
}

function toggleTheme() {
  const modes = ['light', 'dark']
  const currentIdx = modes.indexOf(themeMode.value)
  themeMode.value = modes[(currentIdx + 1) % modes.length]
  localStorage.setItem(STORAGE_KEYS.theme, themeMode.value)
  const labels = { light: '亮色模式', dark: '暗色模式' }
  notify(`已切换到${labels[themeMode.value]}`)
}

watch(
  () => currentPage.value,
  () => {
    window.mdui?.mutation?.()
  }
)

function onHashChange() {
  currentPage.value = resolvePage()
}

onMounted(() => {
  window.addEventListener('hashchange', onHashChange)
  window.addEventListener('resize', syncViewport)
  syncViewport()
  if (isAuthenticated.value) {
    loadMeta()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('hashchange', onHashChange)
  window.removeEventListener('resize', syncViewport)
})
</script>
