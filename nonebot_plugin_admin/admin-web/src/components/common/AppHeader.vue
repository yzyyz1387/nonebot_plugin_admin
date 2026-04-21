<template>
  <div class="mdui-appbar mdui-appbar-fixed admin-appbar">
    <div class="mdui-toolbar mdui-color-theme admin-toolbar">
      <button class="mdui-btn mdui-btn-icon mdui-ripple" type="button" mdui-tooltip="{content: '菜单'}" @click="$emit('toggle-nav')">
        <i class="material-icons">menu</i>
      </button>

      <div class="admin-toolbar-heading">
        <span class="admin-toolbar-title">{{ title }}</span>
        <span class="admin-toolbar-page">{{ pageLabel }}</span>
      </div>

      <div class="mdui-toolbar-spacer"></div>

      <div class="admin-status-indicator">
        <span class="admin-status-dot" :class="statusClass"></span>
        <span class="admin-status-text">{{ connectionText }}</span>
      </div>

      <button class="mdui-btn mdui-btn-icon mdui-ripple" type="button" :title="themeLabel" @click="$emit('toggle-theme')">
        <i class="material-icons">{{ themeIcon }}</i>
      </button>
      <button class="mdui-btn mdui-btn-icon mdui-ripple" type="button" mdui-tooltip="{content: '刷新当前页面'}" @click="$emit('refresh')">
        <i class="material-icons">refresh</i>
      </button>
      <button class="mdui-btn mdui-btn-icon mdui-ripple" type="button" mdui-tooltip="{content: '接口设置'}" @click="$emit('open-config')">
        <i class="material-icons">settings</i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '机器人管理后台' },
  pageLabel: { type: String, default: '' },
  connectionText: { type: String, default: '未连接' },
  themeMode: { type: String, default: 'light' }
})

defineEmits(['refresh', 'open-config', 'toggle-nav', 'toggle-theme'])

const statusClass = computed(() => {
  const text = props.connectionText.toLowerCase()
  if (text.includes('已连接') || text.includes('在线')) return 'is-connected'
  if (text.includes('连接中') || text.includes('加载')) return 'is-connecting'
  return 'is-disconnected'
})

const themeIcon = computed(() => {
  if (props.themeMode === 'dark') return 'brightness_high'
  return 'brightness_low'
})

const themeLabel = computed(() => {
  if (props.themeMode === 'dark') return '切换到亮色模式'
  return '切换到暗色模式'
})
</script>
