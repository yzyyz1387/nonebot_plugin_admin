<template>
  <div class="admin-section-card admin-group-panel">
    <LoadingBar :active="loading" />
    <div class="admin-card-head admin-card-head-tight admin-panel-head">
      <h3 class="admin-card-title">群列表</h3>
      <button class="mdui-btn mdui-btn-icon mdui-ripple" type="button" @click="$emit('refresh')">
        <i class="material-icons">refresh</i>
      </button>
    </div>

    <div class="admin-card-content admin-group-panel-body">
      <div class="admin-panel-toolbar">
        <div class="mdui-textfield admin-textfield-plain admin-panel-search">
          <input :value="search" class="mdui-textfield-input" type="text" placeholder="搜索群名 / 群号" @input="$emit('update:search', $event.target.value)" />
        </div>
        <span class="admin-inline-meta">{{ pagination.total || 0 }} 个</span>
      </div>

      <div class="admin-group-list mdui-m-t-1">
        <div
          v-for="item in groups"
          :key="item.group_id"
          class="admin-list-item"
          :class="{ 'is-active': selectedGroupId === item.group_id }"
          @click="$emit('select', item.group_id)"
        >
          <div class="admin-list-item-avatar">{{ initials(item.group_name) }}</div>
          <div class="admin-list-item-content">
            <div class="admin-list-item-title">{{ item.group_name }}</div>
            <div class="admin-list-item-sub">{{ item.group_id }} · 今日 {{ formatNumber(item.today_message_count) }} · 成员 {{ formatNumber(item.member_count) }}</div>
          </div>
        </div>
        <div v-if="!groups.length && !loading" class="admin-list-empty">
          <span>暂无群组</span>
        </div>
      </div>
    </div>

    <div class="admin-pagination">
      <div class="admin-pagination-text">{{ pagination.page || 1 }} / {{ pagination.totalPages || 1 }}</div>
      <div>
        <button class="mdui-btn mdui-ripple" type="button" :disabled="!pagination.hasPrev" @click="$emit('prev-page')">上一页</button>
        <button class="mdui-btn mdui-ripple" type="button" :disabled="!pagination.hasNext" @click="$emit('next-page')">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import LoadingBar from '../common/LoadingBar.vue'
import { formatNumber, initials } from '../../lib/format'

defineProps({
  groups: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  search: { type: String, default: '' },
  selectedGroupId: { type: String, default: '' },
  pagination: {
    type: Object,
    default: () => ({ page: 1, totalPages: 1, hasPrev: false, hasNext: false, total: 0, pageSize: 0 })
  }
})

defineEmits(['select', 'update:search', 'prev-page', 'next-page', 'refresh'])
</script>
