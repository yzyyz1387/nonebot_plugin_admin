<template>
  <div v-if="open" class="admin-dialog-overlay" @click.self="$emit('close')">
    <div class="admin-dialog admin-dialog-config">
      <div class="admin-dialog-head">
        <div class="admin-dialog-title">连接设置</div>
      </div>

      <div class="admin-dialog-body">
        <div class="admin-form-block">
          <label class="admin-form-label">API Base</label>
          <div class="mdui-textfield admin-flat-field">
            <input v-model="localApiBase" class="mdui-textfield-input" type="text" placeholder="/admin-dashboard/api" />
          </div>
          <div class="admin-note-inline">支持相对路径或完整 URL。</div>
        </div>

        <div class="admin-form-block mdui-m-t-2">
          <label class="admin-form-label">X-Admin-Token</label>
          <div class="mdui-textfield admin-flat-field">
            <input v-model="localToken" class="mdui-textfield-input" type="text" placeholder="未启用鉴权可留空" />
          </div>
        </div>

        <div class="admin-note-block mdui-m-t-2">
          若直接使用插件内置前端，默认接口地址通常会跟随后端当前配置自动推导。
        </div>
      </div>

      <div class="admin-dialog-actions">
        <button type="button" class="mdui-btn mdui-ripple" @click="$emit('close')">取消</button>
        <button type="button" class="mdui-btn mdui-ripple" @click="handleReset">恢复默认</button>
        <button type="button" class="mdui-btn mdui-color-theme mdui-ripple" @click="handleSave">保存</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { DEFAULT_API_BASE } from '../../lib/api'

const props = defineProps({
  open: { type: Boolean, default: false },
  apiBase: { type: String, default: DEFAULT_API_BASE },
  token: { type: String, default: '' }
})

const emit = defineEmits(['close', 'save'])

const localApiBase = ref(props.apiBase || DEFAULT_API_BASE)
const localToken = ref(props.token || '')

watch(
  () => props.open,
  (value) => {
    if (!value) return
    localApiBase.value = props.apiBase || DEFAULT_API_BASE
    localToken.value = props.token || ''
  }
)

function handleReset() {
  localApiBase.value = DEFAULT_API_BASE
  localToken.value = ''
}

function handleSave() {
  emit('save', { apiBase: localApiBase.value, token: localToken.value })
}
</script>
