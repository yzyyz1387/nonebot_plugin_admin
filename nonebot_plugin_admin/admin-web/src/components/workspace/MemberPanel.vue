<template>
  <div class="admin-section-card admin-member-panel">
    <LoadingBar :active="loading" />
    <div class="admin-member-header">
      <div class="admin-panel-toolbar admin-panel-toolbar-stacked">
        <h3 class="admin-card-title">成员</h3>
        <div class="mdui-textfield admin-textfield-plain admin-panel-search">
          <input :value="search" class="mdui-textfield-input" type="text" placeholder="搜索成员" @input="$emit('update:search', $event.target.value)" />
        </div>
      </div>
    </div>

    <div class="admin-card-content admin-member-panel-body">
      <div class="admin-member-list">
        <div
          v-for="item in members"
          :key="item.user_id"
          class="admin-list-item"
          @contextmenu.prevent="$emit('member-context', item, $event)"
        >
          <div class="admin-list-item-avatar">{{ initials(item.display_name) }}</div>
          <div class="admin-list-item-content">
            <div class="admin-list-item-header">
              <span class="admin-list-item-title">{{ item.display_name }}</span>
              <span v-if="item.role === 'owner'" class="admin-tag admin-tag-owner">群主</span>
              <span v-else-if="item.role === 'admin'" class="admin-tag admin-tag-admin">管理员</span>
            </div>
            <div class="admin-list-item-sub">
              <span>{{ item.user_id }}</span>
              <span>等级 {{ item.level || '--' }}</span>
              <span v-if="item.title" class="admin-member-title">{{ item.title }}</span>
            </div>
            <div v-if="item.shut_up_timestamp && item.shut_up_timestamp > Date.now() / 1000" class="admin-list-item-muted">{{ formatRelativeMute(item.shut_up_timestamp) }}</div>
          </div>
        </div>
        <div v-if="!members.length && !loading" class="admin-list-empty">
          <span>暂无成员</span>
        </div>
      </div>
    </div>

    <div class="admin-pagination">
      <div class="admin-pagination-text">{{ pagination.total || 0 }} 名成员</div>
      <div>
        <button class="mdui-btn mdui-ripple" type="button" :disabled="!pagination.has_prev" @click="$emit('prev-page')">上一页</button>
        <button class="mdui-btn mdui-ripple" type="button" :disabled="!pagination.has_next" @click="$emit('next-page')">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import LoadingBar from '../common/LoadingBar.vue'
import { formatRelativeMute, initials } from '../../lib/format'

defineProps({
  members: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  search: { type: String, default: '' },
  pagination: {
    type: Object,
    default: () => ({ total: 0, has_prev: false, has_next: false })
  }
})

defineEmits(['update:search', 'prev-page', 'next-page', 'member-context'])
</script>
