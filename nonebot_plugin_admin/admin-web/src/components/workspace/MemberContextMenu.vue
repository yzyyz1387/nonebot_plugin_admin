<template>
  <div v-if="open && member" class="admin-context-menu" :style="styleObject" @click.stop>
    <button type="button" :disabled="disabledAction('mute')" @click="$emit('action', { key: 'mute_10m', member })">禁言 10 分钟</button>
    <button type="button" :disabled="disabledAction('mute')" @click="$emit('action', { key: 'mute_1h', member })">禁言 1 小时</button>
    <button type="button" :disabled="disabledAction('mute')" @click="$emit('action', { key: 'unmute', member })">解除禁言</button>
    <div class="admin-context-divider"></div>
    <button type="button" :disabled="disabledAction('title')" @click="$emit('action', { key: 'set_title', member })">设置专属头衔</button>
    <button type="button" :disabled="disabledAction('kick')" @click="$emit('action', { key: 'kick', member })">踢出群聊</button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  member: { type: Object, default: null },
  botProfile: { type: Object, default: () => ({ capabilities: {} }) }
})

defineEmits(['action'])

const styleObject = computed(() => ({ left: `${props.x}px`, top: `${props.y}px` }))

function disabledAction(type) {
  const capabilities = props.botProfile?.capabilities || {}
  const role = String(props.member?.role || 'member')
  if (role === 'owner') return true
  if (type === 'mute') return !capabilities.can_mute_members
  if (type === 'title') return !capabilities.can_set_special_title
  if (type === 'kick') return !capabilities.can_kick_members
  return false
}
</script>
