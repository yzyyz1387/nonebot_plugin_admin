<template>
  <div class="admin-info-strip">
    <div class="admin-section-card admin-info-card">
      <div class="admin-info-card-head">
        <div class="admin-info-card-title">群信息</div>
        <span :class="profile.group_all_shut ? 'admin-tag admin-tag-error' : 'admin-tag admin-tag-success'">
          {{ profile.group_all_shut ? '全员禁言中' : '全员禁言关闭' }}
        </span>
      </div>
      <div class="admin-info-card-value">{{ profile.group_name || detail.summary?.group_name || '未选择群' }}</div>
      <div class="admin-info-card-foot">{{ groupId || '--' }} · {{ formatNumber(profile.member_count || detail.summary?.member_count) }} / {{ formatNumber(profile.max_member_count) }}</div>
    </div>

    <div class="admin-section-card admin-info-card">
      <div class="admin-info-card-head">
        <div class="admin-info-card-title">消息</div>
        <span class="admin-tag admin-tag-info">{{ detail.statistics?.record_enabled ? '已记录' : '未记录' }}</span>
      </div>
      <div class="admin-info-card-value">{{ formatNumber(detail.summary?.today_message_count) }}</div>
      <div class="admin-info-card-foot">历史 {{ formatNumber(detail.summary?.history_message_count) }} · 活跃 {{ formatNumber(detail.summary?.today_active_members) }}</div>
    </div>

    <div class="admin-section-card admin-info-card">
      <div class="admin-info-card-head">
        <div class="admin-info-card-title">扩展</div>
        <span class="admin-tag admin-tag-info">Bot {{ roleLabel(botProfile.role) }}</span>
      </div>
      <div class="admin-info-card-value">{{ formatNumber((announcements.items?.length || 0) + (essence.items?.length || 0)) }}</div>
      <div class="admin-info-card-foot">公告 {{ formatNumber(announcements.items?.length) }} · 精华 {{ formatNumber(essence.items?.length) }} · 荣誉 {{ honorCount }} · 文件 {{ fileCount }}</div>
    </div>

    <div class="admin-section-card admin-info-card">
      <div class="admin-info-card-head">
        <div class="admin-info-card-title">功能</div>
        <span class="admin-tag admin-tag-success">开启 {{ formatNumber(detail.feature_switches_summary?.enabled_count) }}</span>
      </div>
      <div class="admin-info-card-value">{{ formatNumber(detail.feature_switches_summary?.disabled_count) }}</div>
      <div class="admin-info-card-foot">已关闭 · 防撤回 {{ detail.summary?.anti_recall_enabled ? '开' : '关' }} · 事件提醒 {{ detail.summary?.event_notice_enabled ? '开' : '关' }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatNumber, roleLabel } from '../../lib/format'

const props = defineProps({
  groupId: { type: String, default: '' },
  detail: { type: Object, default: () => ({}) },
  profile: { type: Object, default: () => ({}) },
  botProfile: { type: Object, default: () => ({}) },
  announcements: { type: Object, default: () => ({ items: [] }) },
  essence: { type: Object, default: () => ({ items: [] }) },
  honors: { type: Object, default: () => ({ sections: [] }) },
  files: { type: Object, default: () => ({ files: [], folders: [] }) }
})

const honorCount = computed(() => (props.honors.sections || []).reduce((sum, item) => sum + Number(item.count || 0), 0))
const fileCount = computed(() => Number(props.files.files?.length || 0) + Number(props.files.folders?.length || 0))
</script>
