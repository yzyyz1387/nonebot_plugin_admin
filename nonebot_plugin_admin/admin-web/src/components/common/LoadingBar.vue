<template>
  <div v-if="visible" class="admin-progress-line">
    <div class="mdui-progress">
      <div class="mdui-progress-indeterminate"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
  active: { type: Boolean, default: false }
})

const visible = computed(() => Boolean(props.loading || props.active))
</script>
