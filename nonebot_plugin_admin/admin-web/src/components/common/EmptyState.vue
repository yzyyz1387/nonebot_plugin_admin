<template>
  <div class="admin-empty">
    <i class="material-icons">{{ icon }}</i>
    <div class="mdui-typo-title">{{ title }}</div>
    <div class="mdui-typo-caption">{{ description }}</div>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: 'inbox' },
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '当前没有可以展示的内容。' }
})
</script>
