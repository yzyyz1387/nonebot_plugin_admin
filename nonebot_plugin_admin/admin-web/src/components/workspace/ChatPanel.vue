<template>
  <div class="admin-section-card admin-chat-panel">
    <LoadingBar :active="loading || sending" />
    <div class="admin-chat-header">
      <h3 class="admin-card-title">聊天</h3>
      <div class="admin-chat-toolbar">
        <span class="admin-inline-meta">最近 {{ messages.length }} 条</span>
        <button class="mdui-btn mdui-ripple" type="button" :disabled="!hasMore || loading" @click="$emit('load-older')">更早消息</button>
        <button class="mdui-btn mdui-ripple" type="button" :disabled="loading" @click="$emit('reload')">刷新</button>
        <button class="mdui-btn mdui-ripple" type="button" @click="$emit('mark-read')">标记已读</button>
        <label class="mdui-switch">
          <input :checked="wholeBan" type="checkbox" @change="$emit('toggle-whole-ban', $event.target.checked)" />
          <i class="mdui-switch-icon"></i>
        </label>
        <span class="admin-inline-meta">全员禁言</span>
      </div>
    </div>

    <div ref="messageBoxRef" class="admin-chat-messages">
      <template v-if="messages.length">
        <div v-for="item in messages" :key="item.id" class="admin-message-row" :class="{ 'is-self': isBotMessage(item) }">
          <template v-if="isBotMessage(item)">
            <div class="admin-message-bubble is-self">
              <div class="admin-message-meta">
                <span class="admin-message-time">{{ formatTime(item.created_at || item.message_date) }}</span>
              </div>
              <div class="admin-message-content">{{ item.plain_text || item.raw_message || '[非文本消息]' }}</div>
            </div>
            <div class="admin-message-avatar is-self">{{ initials(item.display_name || 'Bot') }}</div>
          </template>
          <template v-else>
            <div class="admin-message-avatar">{{ initials(item.display_name || item.user_id || '?') }}</div>
            <div class="admin-message-bubble">
              <div class="admin-message-meta">
                <span class="admin-message-author">{{ item.display_name || item.user_id || '未知用户' }}</span>
                <span class="admin-message-time">{{ formatTime(item.created_at || item.message_date) }}</span>
              </div>
              <div class="admin-message-content">{{ item.plain_text || item.raw_message || '[非文本消息]' }}</div>
            </div>
          </template>
        </div>
      </template>
      <EmptyState v-else icon="chat" title="暂无消息记录" description="当前群尚未获取到可显示的消息。" />
    </div>

    <div class="admin-message-input">
      <div class="admin-message-compose">
        <div class="mdui-textfield admin-textfield-plain admin-message-textfield">
          <textarea
            :value="composer"
            class="mdui-textfield-input"
            rows="2"
            placeholder="发送群消息，Ctrl + Enter 快速发送"
            @input="$emit('update:composer', $event.target.value)"
            @keydown.ctrl.enter.prevent="$emit('send')"
          ></textarea>
        </div>
        <button class="mdui-btn mdui-color-theme mdui-ripple admin-send-btn" type="button" :disabled="sending" @click="$emit('send')">
          <i class="material-icons">send</i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import EmptyState from '../common/EmptyState.vue'
import LoadingBar from '../common/LoadingBar.vue'
import { formatTime, initials } from '../../lib/format'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  hasMore: { type: Boolean, default: false },
  composer: { type: String, default: '' },
  wholeBan: { type: Boolean, default: false },
  sending: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  botSelfId: { type: String, default: '' }
})

defineEmits(['load-older', 'reload', 'mark-read', 'toggle-whole-ban', 'update:composer', 'send'])

const messageBoxRef = ref(null)

function isBotMessage(item) {
  if (!props.botSelfId || !item.user_id) return false
  return String(item.user_id) === String(props.botSelfId)
}

watch(
  () => props.messages,
  async () => {
    await nextTick()
    const el = messageBoxRef.value
    if (!el) return
    el.scrollTop = el.scrollHeight
  },
  { deep: true }
)
</script>