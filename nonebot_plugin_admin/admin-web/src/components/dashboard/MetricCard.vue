<template>
  <div class="admin-section-card admin-metric-card admin-hover-surface" :class="`is-${tone}`">
    <div class="admin-metric-head">
      <div class="admin-metric-label">{{ label }}</div>
      <div class="admin-metric-icon">
        <i class="material-icons">{{ icon }}</i>
      </div>
    </div>
    <div class="admin-metric-value">{{ value }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  icon: { type: String, default: 'insights' },
  tone: { type: String, default: 'primary' }
})
</script>
