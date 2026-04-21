<template>
  <div class="admin-section-card admin-tab-panel">
    <div class="admin-tab-header">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        class="admin-tab-item"
        :class="{ 'is-active': activeTab === tab.key }"
        @click="$emit('update:activeTab', tab.key)"
      >
        <i class="material-icons">{{ tab.icon }}</i>
        <span>{{ tab.label }}</span>
        <span v-if="tab.count !== undefined" class="admin-tab-count">{{ tab.count }}</span>
      </button>
    </div>
    <div class="admin-tab-content">
      <slot :name="activeTab"></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  tabs: { type: Array, default: () => [] },
  activeTab: { type: String, default: '' }
})

defineEmits(['update:activeTab'])
</script>
