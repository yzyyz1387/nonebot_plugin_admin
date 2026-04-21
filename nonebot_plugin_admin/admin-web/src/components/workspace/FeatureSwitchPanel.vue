<template>
  <div class="admin-section-card admin-switch-panel">
    <LoadingBar :active="saving" />
    <div class="admin-card-head admin-card-head-tight admin-panel-head">
      <h3 class="admin-card-title">功能开关</h3>
      <span class="admin-inline-stat">{{ switches.length }} 项</span>
    </div>
    <div class="admin-card-content">
      <div v-if="switches.length" class="admin-switch-grid">
        <div v-for="item in switches" :key="item.key" class="admin-switch-row">
          <div class="admin-switch-main">
            <div class="admin-switch-label">{{ item.label }}</div>
            <div class="admin-switch-meta">默认 {{ item.default_enabled ? '开启' : '关闭' }} · {{ item.notify_when_disabled ? '关闭时提示' : '关闭时静默' }}</div>
          </div>
          <label class="mdui-switch">
            <input :checked="item.enabled" type="checkbox" :disabled="savingKey === item.key" @change="$emit('toggle', item, $event.target.checked)" />
            <i class="mdui-switch-icon"></i>
          </label>
        </div>
      </div>
      <EmptyState v-else icon="tune" title="暂无功能开关" description="当前群没有加载到可展示的功能开关。" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import EmptyState from '../common/EmptyState.vue'
import LoadingBar from '../common/LoadingBar.vue'

const props = defineProps({
  switches: { type: Array, default: () => [] },
  savingKey: { type: String, default: '' }
})

const saving = computed(() => Boolean(props.savingKey))

defineEmits(['toggle'])
</script>
