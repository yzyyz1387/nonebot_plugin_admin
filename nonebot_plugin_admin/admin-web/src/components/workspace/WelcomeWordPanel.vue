<template>
  <section class="admin-section-card admin-switch-panel">
    <LoadingBar :active="saving" />
    <div class="admin-card-head admin-card-head-tight admin-panel-head">
      <h3 class="admin-card-title">群欢迎词</h3>
      <span class="admin-inline-stat">入群通知</span>
    </div>
    <div class="admin-card-content">
      <div v-if="storageAvailable" class="admin-form-block">
        <label class="admin-form-label" for="welcome-word-input">欢迎词内容</label>
        <div class="mdui-textfield admin-flat-field">
          <textarea id="welcome-word-input" v-model="draft" class="mdui-textfield-input" maxlength="1000" placeholder="留空后保存可删除欢迎词"></textarea>
        </div>
        <div class="admin-switch-actions">
          <button class="mdui-btn mdui-color-theme mdui-ripple" type="button" :disabled="saving" @click="$emit('save', draft)">
            <i class="material-icons">save</i> 保存
          </button>
          <button class="mdui-btn mdui-ripple" type="button" :disabled="saving || !draft.trim()" @click="$emit('remove')">
            <i class="material-icons">delete_outline</i> 删除
          </button>
        </div>
      </div>
      <EmptyState v-else icon="storage" title="欢迎词数据库不可用" description="请检查 ORM 数据库配置后重试。" />
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
import EmptyState from '../common/EmptyState.vue'
import LoadingBar from '../common/LoadingBar.vue'

const props = defineProps({
  word: { type: String, default: '' },
  storageAvailable: { type: Boolean, default: true },
  saving: { type: Boolean, default: false }
})

defineEmits(['save', 'remove'])

const draft = ref('')

watch(() => props.word, (word) => {
  draft.value = word || ''
}, { immediate: true })
</script>
