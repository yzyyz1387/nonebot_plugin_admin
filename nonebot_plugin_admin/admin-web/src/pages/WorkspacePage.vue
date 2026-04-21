<template>
  <section class="admin-page admin-page-workspace">
    <div class="admin-workspace-sticky-stack">
      <div class="admin-workspace-main">
        <GroupListPanel
          :groups="pagedGroups"
          :loading="groupLoading"
          :search="groupSearch"
          :selected-group-id="selectedGroupId"
          :pagination="groupPagination"
          @select="handleSelectGroup"
          @update:search="handleGroupSearch"
          @prev-page="changeGroupPage(-1)"
          @next-page="changeGroupPage(1)"
          @refresh="loadGroups(true)"
        />

        <div class="admin-workspace-center">
          <div v-if="selectedGroupId" class="admin-chat-header-bar">
            <div class="admin-chat-header-name">{{ workspace.group_profile?.group_name || selectedGroupId }}</div>
            <div class="admin-chat-header-id">{{ selectedGroupId }}</div>
          </div>
          <TabPanel
            v-if="selectedGroupId"
            :tabs="centerTabs"
            :active-tab="centerActiveTab"
            @update:active-tab="handleTabChange"
          >
            <template #chat>
              <ChatPanel
                :messages="workspace.messages.items || []"
                :has-more="Boolean(workspace.messages.pagination?.has_more)"
                :composer="composer"
                :whole-ban="Boolean(workspace.group_profile?.group_all_shut)"
                :sending="sending"
                :loading="workspaceLoading || messagesLoading"
                :bot-self-id="workspace.bot_profile?.self_id || ''"
                @update:composer="updateComposer"
                @load-older="loadOlderMessages"
                @reload="loadLatestMessages"
                @mark-read="markGroupRead"
                @toggle-whole-ban="toggleWholeBan"
                @send="sendMessage"
              />
            </template>
            <template #announcements>
              <div class="admin-section-card admin-tab-content-card">
                <div class="admin-card-content">
                  <div v-if="tabLoading.announcements" class="admin-tab-loading">
                    <div class="mdui-spinner mdui-spinner-colorful"></div>
                  </div>
                  <template v-else>
                  <div v-if="workspace.announcements.items?.length" class="admin-tab-list">
                    <div v-for="item in workspace.announcements.items" :key="item.notice_id" class="admin-list-item">
                      <i class="material-icons admin-list-item-icon">campaign</i>
                      <div class="admin-list-item-content">
                        <div class="admin-list-item-title">{{ item.text || '公告' }}</div>
                        <div class="admin-list-item-sub">
                          <span v-if="item.sender_id">发布者: {{ item.sender_id }}</span>
                          <span v-if="item.publish_time">{{ item.publish_time }}</span>
                          <span v-if="item.image_count">{{ item.image_count }} 张图片</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <EmptyState v-else icon="campaign" title="暂无公告" description="当前群没有公告。" />
                  </template>
                </div>
              </div>
            </template>
            <template #files>
              <div class="admin-section-card admin-tab-content-card">
                <div class="admin-card-content">
                  <div v-if="tabLoading.files" class="admin-tab-loading">
                    <div class="mdui-spinner mdui-spinner-colorful"></div>
                  </div>
                  <template v-else>
                  <div v-if="workspace.files.files?.length || workspace.files.folders?.length" class="admin-tab-list">
                    <div v-for="folder in workspace.files.folders || []" :key="folder.id || folder.folder_id" class="admin-list-item">
                      <i class="material-icons admin-list-item-icon">folder</i>
                      <div class="admin-list-item-content">
                        <div class="admin-list-item-title">{{ folder.name || folder.folder_name }}</div>
                        <div class="admin-list-item-sub">文件夹</div>
                      </div>
                    </div>
                    <div v-for="file in workspace.files.files || []" :key="file.id || file.file_id" class="admin-list-item">
                      <i class="material-icons admin-list-item-icon">insert_drive_file</i>
                      <div class="admin-list-item-content">
                        <div class="admin-list-item-title">{{ file.name || file.file_name }}</div>
                        <div class="admin-list-item-sub">{{ formatFileSize(file.size || file.file_size) }}</div>
                      </div>
                    </div>
                  </div>
                  <EmptyState v-else icon="folder" title="暂无文件" description="当前群没有共享文件。" />
                  </template>
                </div>
              </div>
            </template>
            <template #essence>
              <div class="admin-section-card admin-tab-content-card">
                <div class="admin-card-content">
                  <div v-if="tabLoading.essence" class="admin-tab-loading">
                    <div class="mdui-spinner mdui-spinner-colorful"></div>
                  </div>
                  <template v-else>
                  <div v-if="workspace.essence.items?.length" class="admin-tab-list">
                    <div v-for="item in workspace.essence.items" :key="item.id || item.message_id" class="admin-list-item">
                      <div class="admin-list-item-avatar">{{ initials(item.sender_name || item.sender_id || '?') }}</div>
                      <div class="admin-list-item-content">
                        <div class="admin-list-item-title">{{ item.sender_name || item.sender_id || '未知用户' }}</div>
                        <div class="admin-list-item-sub">{{ parseMessageContent(item.content || item.plain_text) }}</div>
                      </div>
                    </div>
                  </div>
                  <EmptyState v-else icon="star" title="暂无精华消息" description="当前群没有精华消息。" />
                  </template>
                </div>
              </div>
            </template>
            <template #honors>
              <div class="admin-section-card admin-tab-content-card">
                <div class="admin-card-content">
                  <div v-if="tabLoading.honors" class="admin-tab-loading">
                    <div class="mdui-spinner mdui-spinner-colorful"></div>
                  </div>
                  <template v-else>
                  <div v-if="workspace.honors.sections?.length" class="admin-honor-list">
                    <div v-for="section in workspace.honors.sections" :key="section.title" class="admin-honor-section">
                      <h4 class="admin-honor-title">{{ section.title }}</h4>
                      <div class="admin-tab-list">
                        <div v-for="item in section.items || []" :key="item.user_id || item.id" class="admin-list-item">
                          <div class="admin-list-item-avatar">{{ initials(item.name || item.nickname || '用户') }}</div>
                          <div class="admin-list-item-content">
                            <div class="admin-list-item-title">{{ item.name || item.nickname }}</div>
                            <div class="admin-list-item-sub">{{ item.description || item.honor_name }}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <EmptyState v-else icon="military_tech" title="暂无群荣誉" description="当前群没有荣誉信息。" />
                  </template>
                </div>
              </div>
            </template>
          </TabPanel>
          <div v-else class="admin-section-card admin-hover-surface admin-workspace-empty-card">
            <EmptyState icon="forum" title="请选择群聊" description="从左侧列表选择一个群后开始操作。" />
          </div>

          <FeatureSwitchPanel
            v-if="selectedGroupId"
            :switches="workspace.detail.feature_switches || []"
            :saving-key="savingSwitchKey"
            :loading="workspaceLoading"
            @toggle="toggleSwitch"
          />
        </div>

        <MemberPanel
          v-if="selectedGroupId"
          :members="workspace.members.items || []"
          :loading="workspaceLoading || memberLoading"
          :search="memberSearch"
          :pagination="workspace.members.pagination || {}"
          @update:search="handleMemberSearch"
          @prev-page="changeMemberPage(-1)"
          @next-page="changeMemberPage(1)"
          @member-context="openMemberMenu"
        />
        <div v-else class="admin-section-card admin-hover-surface admin-workspace-empty-card">
          <EmptyState icon="groups" title="成员面板" description="右键成员后可执行禁言、头衔、踢出等操作。" />
        </div>
      </div>
    </div>

    <MemberContextMenu
      :open="memberMenu.open"
      :x="memberMenu.x"
      :y="memberMenu.y"
      :member="memberMenu.member"
      :bot-profile="workspace.bot_profile"
      @action="handleMemberMenuAction"
    />

    <div v-if="titleDialog.open" class="admin-dialog-overlay" @click.self="closeTitleDialog">
      <div class="admin-dialog">
        <div class="admin-dialog-head">
          <div class="admin-dialog-title">设置专属头衔</div>
        </div>
        <div class="admin-dialog-body">
          <div class="admin-note-block">{{ titleDialog.member?.display_name }}（{{ titleDialog.member?.user_id }}）</div>
          <div class="admin-form-block mdui-m-t-2">
            <label class="admin-form-label">头衔内容</label>
            <div class="mdui-textfield admin-flat-field">
              <input v-model="titleDialog.value" class="mdui-textfield-input" type="text" maxlength="32" placeholder="留空可清空专属头衔" />
            </div>
          </div>
        </div>
        <div class="admin-dialog-actions">
          <button class="mdui-btn mdui-ripple" type="button" @click="closeTitleDialog">取消</button>
          <button class="mdui-btn mdui-color-theme mdui-ripple" type="button" @click="submitTitle">保存</button>
        </div>
      </div>
    </div>

    <div v-if="kickDialog.open" class="admin-dialog-overlay" @click.self="closeKickDialog">
      <div class="admin-dialog">
        <div class="admin-dialog-head">
          <div class="admin-dialog-title">确认踢出成员</div>
        </div>
        <div class="admin-dialog-body">
          <div class="admin-note-block">{{ kickDialog.member?.display_name }}（{{ kickDialog.member?.user_id }}）</div>
        </div>
        <div class="admin-dialog-actions">
          <button class="mdui-btn mdui-ripple" type="button" @click="closeKickDialog">取消</button>
          <button class="mdui-btn mdui-color-theme mdui-ripple" type="button" @click="submitKick">确认踢出</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import GroupListPanel from '../components/workspace/GroupListPanel.vue'
import ChatPanel from '../components/workspace/ChatPanel.vue'
import MemberPanel from '../components/workspace/MemberPanel.vue'
import FeatureSwitchPanel from '../components/workspace/FeatureSwitchPanel.vue'
import MemberContextMenu from '../components/workspace/MemberContextMenu.vue'
import TabPanel from '../components/workspace/TabPanel.vue'
import EmptyState from '../components/common/EmptyState.vue'
import { apiRequest, extractErrorMessage } from '../lib/api'
import { isPlaceholderGroupRecord, initials, parseMessageContent } from '../lib/format'

const POLL_INTERVAL = 5000
let pollTimer = null

const props = defineProps({
  apiBase: { type: String, required: true },
  token: { type: String, default: '' },
  active: { type: Boolean, default: false },
  refreshKey: { type: Number, default: 0 }
})

const emit = defineEmits(['notify', 'connection'])

const groupLoading = ref(false)
const workspaceLoading = ref(false)
const messagesLoading = ref(false)
const groupSearch = ref('')
const groupPage = ref(1)
const groupPageSize = 12
const selectedGroupId = ref('')
const sending = ref(false)
const memberLoading = ref(false)
const savingSwitchKey = ref('')
const composer = ref('')
const memberSearch = ref('')
const allGroups = ref([])
const centerActiveTab = ref('chat')
const tabLoaded = reactive({
  announcements: false,
  files: false,
  essence: false,
  honors: false
})
const tabLoading = reactive({
  announcements: false,
  files: false,
  essence: false,
  honors: false
})

const centerTabs = computed(() => [
  { key: 'chat', label: '聊天', icon: 'chat' },
  { key: 'announcements', label: '公告', icon: 'notifications', count: workspace.announcements.items?.length },
  { key: 'files', label: '文件', icon: 'folder', count: (workspace.files.files?.length || 0) + (workspace.files.folders?.length || 0) },
  { key: 'essence', label: '精华', icon: 'star', count: workspace.essence.items?.length },
  { key: 'honors', label: '荣誉', icon: 'military_tech' }
])

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const workspace = reactive({
  detail: { summary: {}, statistics: {}, feature_switches: [], feature_switches_summary: {} },
  group_profile: {},
  bot_profile: { capabilities: {} },
  messages: { items: [], pagination: {} },
  members: { items: [], pagination: {} },
  announcements: { items: [] },
  essence: { items: [] },
  honors: { sections: [] },
  files: { files: [], folders: [] }
})

const memberMenu = reactive({ open: false, x: 0, y: 0, member: null })
const titleDialog = reactive({ open: false, member: null, value: '' })
const kickDialog = reactive({ open: false, member: null })

const visibleGroups = computed(() => {
  const query = groupSearch.value.trim().toLowerCase()
  return (allGroups.value || [])
    .filter((item) => !isPlaceholderGroupRecord(item))
    .filter((item) => {
      if (!query) return true
      return String(item.group_id || '').toLowerCase().includes(query) || String(item.group_name || '').toLowerCase().includes(query)
    })
    .sort((a, b) => Number(b.today_message_count || 0) - Number(a.today_message_count || 0))
})

const groupPagination = computed(() => {
  const total = visibleGroups.value.length
  const totalPages = Math.max(1, Math.ceil(total / groupPageSize))
  const page = Math.min(groupPage.value, totalPages)
  return {
    page,
    total,
    totalPages,
    pageSize: groupPageSize,
    hasPrev: page > 1,
    hasNext: page < totalPages
  }
})

const pagedGroups = computed(() => {
  const page = groupPagination.value.page
  const start = (page - 1) * groupPageSize
  return visibleGroups.value.slice(start, start + groupPageSize)
})

function closeMemberMenu() {
  memberMenu.open = false
}

function resetWorkspace() {
  stopPolling()
  workspace.detail = { summary: {}, statistics: {}, feature_switches: [], feature_switches_summary: {} }
  workspace.group_profile = {}
  workspace.bot_profile = { capabilities: {} }
  workspace.messages = { items: [], pagination: {} }
  workspace.members = { items: [], pagination: {} }
  workspace.announcements = { items: [] }
  workspace.essence = { items: [] }
  workspace.honors = { sections: [] }
  workspace.files = { files: [], folders: [] }
}

function messageKey(item) {
  return String(item?.id ?? item?.message_id ?? item?.real_id ?? item?.real_seq ?? Math.random())
}

function dedupeMessages(items) {
  const map = new Map()
  items.forEach((item) => {
    map.set(messageKey(item), item)
  })
  return Array.from(map.values()).sort((a, b) => Number(a.id || a.message_id || 0) - Number(b.id || b.message_id || 0))
}

async function loadGroups(autoSelect = false) {
  groupLoading.value = true
  try {
    const payload = await apiRequest(props.apiBase, props.token, '/groups')
    allGroups.value = Array.isArray(payload?.items) ? payload.items : []
    emit('connection', '已连接')

    const visible = visibleGroups.value
    if (!visible.length) {
      selectedGroupId.value = ''
      resetWorkspace()
      return
    }

    const stillExists = visible.some((item) => String(item.group_id) === String(selectedGroupId.value))
    if (autoSelect || !selectedGroupId.value || !stillExists) {
      await handleSelectGroup(visible[0].group_id)
    }
  } catch (error) {
    emit('connection', '连接失败')
    emit('notify', { message: `群列表加载失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    groupLoading.value = false
  }
}

async function handleSelectGroup(groupId) {
  if (!groupId) return
  selectedGroupId.value = String(groupId)
  memberSearch.value = ''
  closeMemberMenu()
  await loadWorkspace(groupId)
}

async function loadWorkspace(groupId) {
  workspaceLoading.value = true
  try {
    const [profilePayload, messagesPayload, membersPayload, detailPayload] = await Promise.all([
      apiRequest(props.apiBase, props.token, `/groups/${groupId}/profile`, { timeout: 30000 }).catch(() => ({})),
      apiRequest(props.apiBase, props.token, `/groups/${groupId}/messages`, { params: { limit: 60 }, timeout: 30000 }).catch(() => ({ items: [], pagination: {} })),
      apiRequest(props.apiBase, props.token, `/groups/${groupId}/members`, { params: { page: 1, page_size: 30 }, timeout: 30000 }).catch(() => ({ items: [], pagination: {} })),
      apiRequest(props.apiBase, props.token, `/groups/${groupId}/feature-switches`, { timeout: 30000 }).catch(() => [])
    ])
    workspace.group_profile = profilePayload || {}
    workspace.messages = messagesPayload || { items: [], pagination: {} }
    workspace.members = membersPayload || { items: [], pagination: {} }
    workspace.detail.feature_switches = Array.isArray(detailPayload) ? detailPayload : (detailPayload?.switches || [])
    workspace.bot_profile = { capabilities: {} }
    try {
      const botProfile = await apiRequest(props.apiBase, props.token, `/groups/${groupId}/bot-profile`, { timeout: 15000 })
      workspace.bot_profile = botProfile || { capabilities: {} }
    } catch {}
    workspace.announcements = { items: [] }
    workspace.files = { files: [], folders: [] }
    workspace.essence = { items: [] }
    workspace.honors = { sections: [] }
    tabLoaded.announcements = false
    tabLoaded.files = false
    tabLoaded.essence = false
    tabLoaded.honors = false
    emit('connection', '已连接')
    await nextTick()
    window.mdui?.mutation?.()
    if (centerActiveTab.value === 'chat') startPolling()
  } catch (error) {
    emit('connection', '连接失败')
    const errorMsg = error?.isTimeout ? '加载超时，该群数据量较大，请稍后重试' : extractErrorMessage(error)
    emit('notify', { message: `群工作台加载失败：${errorMsg}`, type: 'error' })
  } finally {
    workspaceLoading.value = false
  }
}

async function loadTabData(tabKey) {
  if (!selectedGroupId.value || tabLoaded[tabKey] || tabLoading[tabKey]) return
  tabLoading[tabKey] = true
  await nextTick()
  window.mdui?.mutation?.()
  const startTime = Date.now()
  try {
    if (tabKey === 'announcements') {
      const data = await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/announcements`, { timeout: 30000 })
      workspace.announcements = data || { items: [] }
      tabLoaded.announcements = true
    } else if (tabKey === 'files') {
      const data = await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/files`, { timeout: 30000 })
      workspace.files = data || { files: [], folders: [] }
      tabLoaded.files = true
    } else if (tabKey === 'essence') {
      const data = await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/essence`, { timeout: 30000 })
      workspace.essence = data || { items: [] }
      tabLoaded.essence = true
    } else if (tabKey === 'honors') {
      const data = await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/honors`, { timeout: 30000 })
      workspace.honors = data || { sections: [] }
      tabLoaded.honors = true
    }
  } catch (error) {
    emit('notify', { message: `数据加载失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    const elapsed = Date.now() - startTime
    if (elapsed < 500) {
      await new Promise(resolve => setTimeout(resolve, 500 - elapsed))
    }
    tabLoading[tabKey] = false
  }
}

function handleTabChange(tabKey) {
  centerActiveTab.value = tabKey
  if (tabKey === 'chat') {
    startPolling()
  } else {
    stopPolling()
    console.log('Tab change to:', tabKey, 'tabLoaded:', tabLoaded[tabKey], 'tabLoading:', tabLoading[tabKey])
    loadTabData(tabKey)
  }
}

async function loadMembers(page = 1) {
  if (!selectedGroupId.value) return
  memberLoading.value = true
  try {
    workspace.members = await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/members`, {
      params: {
        page,
        page_size: 30,
        keyword: memberSearch.value
      }
    })
  } catch (error) {
    emit('notify', { message: `成员加载失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    memberLoading.value = false
  }
}

async function loadLatestMessages() {
  if (!selectedGroupId.value) return
  messagesLoading.value = true
  try {
    workspace.messages = await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/messages`, {
      params: { limit: 60 }
    })
  } catch (error) {
    emit('notify', { message: `消息刷新失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    messagesLoading.value = false
  }
}

async function pollNewMessages() {
  if (!selectedGroupId.value || centerActiveTab.value !== 'chat') return
  const latestId = workspace.messages.pagination?.latest_id
  if (!latestId) return
  try {
    const result = await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/messages`, {
      params: { limit: 60, after_id: latestId }
    })
    const newItems = result?.items || []
    if (newItems.length > 0) {
      workspace.messages = {
        ...result,
        items: dedupeMessages([...(workspace.messages.items || []), ...newItems]),
        pagination: result.pagination || workspace.messages.pagination
      }
    }
  } catch {}
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(pollNewMessages, POLL_INTERVAL)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function loadOlderMessages() {
  if (!selectedGroupId.value || !workspace.messages.pagination?.has_more) return
  messagesLoading.value = true
  try {
    const older = await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/messages`, {
      params: {
        limit: 60,
        before_id: workspace.messages.pagination?.next_before_id
      }
    })
    workspace.messages = {
      ...older,
      items: dedupeMessages([...(older.items || []), ...(workspace.messages.items || [])]),
      pagination: older.pagination || workspace.messages.pagination
    }
  } catch (error) {
    emit('notify', { message: `更早消息加载失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    messagesLoading.value = false
  }
}

async function sendMessage() {
  if (!selectedGroupId.value) return
  const message = composer.value.trim()
  if (!message) {
    emit('notify', { message: '请输入消息内容。', type: 'warn' })
    return
  }
  sending.value = true
  try {
    await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/messages`, {
      method: 'POST',
      body: { message }
    })
    composer.value = ''
    emit('notify', { message: '消息已发送。', type: 'success' })
    await loadLatestMessages()
  } catch (error) {
    emit('notify', { message: `发送失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    sending.value = false
  }
}

async function markGroupRead() {
  if (!selectedGroupId.value) return
  messagesLoading.value = true
  try {
    await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/actions/mark-read`, { method: 'POST' })
    emit('notify', { message: '已标记群消息为已读。', type: 'success' })
  } catch (error) {
    emit('notify', { message: `标记已读失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    messagesLoading.value = false
  }
}

async function toggleWholeBan(enabled) {
  if (!selectedGroupId.value) return
  messagesLoading.value = true
  try {
    await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/actions/whole-ban`, {
      method: 'POST',
      body: { enabled }
    })
    workspace.group_profile = { ...workspace.group_profile, group_all_shut: enabled }
    emit('notify', { message: enabled ? '已开启全员禁言。' : '已关闭全员禁言。', type: 'success' })
  } catch (error) {
    emit('notify', { message: `切换全员禁言失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    messagesLoading.value = false
  }
}

async function toggleSwitch(item, enabled) {
  if (!selectedGroupId.value || !item?.key) return
  savingSwitchKey.value = item.key
  try {
    await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/feature-switches/${item.key}`, {
      method: 'POST',
      body: { enabled }
    })
    workspace.detail.feature_switches = (workspace.detail.feature_switches || []).map((current) =>
      current.key === item.key ? { ...current, enabled } : current
    )
    const enabledCount = workspace.detail.feature_switches.filter((current) => current.enabled).length
    workspace.detail.feature_switches_summary = {
      ...(workspace.detail.feature_switches_summary || {}),
      enabled_count: enabledCount,
      disabled_count: Math.max(0, workspace.detail.feature_switches.length - enabledCount)
    }
    emit('notify', { message: `${item.label} 已${enabled ? '开启' : '关闭'}。`, type: 'success' })
  } catch (error) {
    emit('notify', { message: `切换功能失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    savingSwitchKey.value = ''
  }
}

function openMemberMenu(member, event) {
  memberMenu.member = member
  memberMenu.x = Math.min(event.clientX, window.innerWidth - 220)
  memberMenu.y = Math.min(event.clientY, window.innerHeight - 220)
  memberMenu.open = true
}

async function muteMember(member, duration) {
  if (!selectedGroupId.value || !member?.user_id) return
  memberLoading.value = true
  try {
    await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/actions/mute`, {
      method: 'POST',
      body: { user_id: member.user_id, duration }
    })
    emit('notify', { message: duration > 0 ? '禁言操作已提交。' : '已解除禁言。', type: 'success' })
    await loadMembers(Number(workspace.members.pagination?.page || 1))
  } catch (error) {
    emit('notify', { message: `禁言操作失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    memberLoading.value = false
  }
}

function handleMemberMenuAction(payload) {
  closeMemberMenu()
  const member = payload?.member
  if (!member) return
  if (payload.key === 'mute_10m') {
    muteMember(member, 600)
    return
  }
  if (payload.key === 'mute_1h') {
    muteMember(member, 3600)
    return
  }
  if (payload.key === 'unmute') {
    muteMember(member, 0)
    return
  }
  if (payload.key === 'set_title') {
    titleDialog.member = member
    titleDialog.value = member.title || ''
    titleDialog.open = true
    return
  }
  if (payload.key === 'kick') {
    kickDialog.member = member
    kickDialog.open = true
  }
}

function closeTitleDialog() {
  titleDialog.open = false
  titleDialog.member = null
  titleDialog.value = ''
}

async function submitTitle() {
  if (!selectedGroupId.value || !titleDialog.member?.user_id) return
  memberLoading.value = true
  try {
    await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/actions/special-title`, {
      method: 'POST',
      body: { user_id: titleDialog.member.user_id, special_title: titleDialog.value }
    })
    emit('notify', { message: '专属头衔已更新。', type: 'success' })
    closeTitleDialog()
    await loadMembers(Number(workspace.members.pagination?.page || 1))
  } catch (error) {
    emit('notify', { message: `设置头衔失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    memberLoading.value = false
  }
}

function closeKickDialog() {
  kickDialog.open = false
  kickDialog.member = null
}

async function submitKick() {
  if (!selectedGroupId.value || !kickDialog.member?.user_id) return
  memberLoading.value = true
  try {
    await apiRequest(props.apiBase, props.token, `/groups/${selectedGroupId.value}/actions/kick`, {
      method: 'POST',
      body: { user_id: kickDialog.member.user_id, reject_add_request: false }
    })
    emit('notify', { message: '成员已踢出。', type: 'success' })
    closeKickDialog()
    await loadMembers(Number(workspace.members.pagination?.page || 1))
    await loadGroups(false)
  } catch (error) {
    emit('notify', { message: `踢出成员失败：${extractErrorMessage(error)}`, type: 'error' })
  } finally {
    memberLoading.value = false
  }
}

function updateComposer(value) {
  composer.value = value
}

function handleGroupSearch(value) {
  groupSearch.value = value
  groupPage.value = 1
}

function handleMemberSearch(value) {
  memberSearch.value = value
  loadMembers(1)
}

function changeGroupPage(offset) {
  const next = groupPagination.value.page + offset
  if (next < 1 || next > groupPagination.value.totalPages) return
  groupPage.value = next
}

function changeMemberPage(offset) {
  const current = Number(workspace.members.pagination?.page || 1)
  const next = current + offset
  if (next < 1) return
  loadMembers(next)
}

function onGlobalPointer() {
  closeMemberMenu()
}

onMounted(() => {
  window.addEventListener('click', onGlobalPointer)
  window.addEventListener('resize', onGlobalPointer)
  window.addEventListener('scroll', onGlobalPointer, true)
})

onBeforeUnmount(() => {
  stopPolling()
  window.removeEventListener('click', onGlobalPointer)
  window.removeEventListener('resize', onGlobalPointer)
  window.removeEventListener('scroll', onGlobalPointer, true)
})

watch(
  () => [props.active, props.refreshKey],
  ([active]) => {
    if (!active) return
    loadGroups(true)
  },
  { immediate: true }
)

watch(
  () => visibleGroups.value.length,
  () => {
    const totalPages = groupPagination.value.totalPages
    if (groupPage.value > totalPages) {
      groupPage.value = totalPages
    }
  }
)
</script>
