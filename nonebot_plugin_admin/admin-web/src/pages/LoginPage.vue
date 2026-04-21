<template>
  <div class="admin-login-root" :class="{ 'mdui-theme-layout-dark': isDark }">
    <div class="admin-login-card">
      <div class="admin-login-header">
        <i class="material-icons admin-login-icon">admin_panel_settings</i>
        <h1 class="admin-login-title">机器人管理后台</h1>
        <p class="admin-login-subtitle">请输入 Token 以继续</p>
      </div>

      <div class="admin-login-body">
        <div class="admin-login-field">
          <div class="mdui-textfield admin-flat-field">
            <input
              v-model="token"
              class="mdui-textfield-input"
              type="password"
              placeholder="X-Admin-Token"
              @keydown.enter="handleLogin"
            />
          </div>
          <div class="admin-login-hint">Token 仅保存在当前会话中，关闭浏览器或超过24小时后需重新输入。</div>
        </div>

        <div v-if="error" class="admin-login-error">
          <i class="material-icons">error_outline</i>
          <span>{{ error }}</span>
        </div>

        <button
          type="button"
          class="mdui-btn mdui-btn-block mdui-color-theme mdui-ripple admin-login-btn"
          :disabled="loading || !token.trim()"
          @click="handleLogin"
        >
          {{ loading ? '验证中...' : '登 录' }}
        </button>
      </div>

      <div class="admin-login-footer">
        <span>未启用鉴权？</span>
        <button type="button" class="mdui-btn mdui-ripple" @click="handleSkip">跳过登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { DEFAULT_API_BASE, apiRequest, extractErrorMessage, normalizeApiBase } from '../lib/api'

const emit = defineEmits(['login'])

const token = ref('')
const error = ref('')
const loading = ref(false)
const isDark = ref(window.matchMedia?.('(prefers-color-scheme: dark)')?.matches || false)

async function handleLogin() {
  const trimmed = token.value.trim()
  if (!trimmed) return

  loading.value = true
  error.value = ''

  try {
    const apiBase = normalizeApiBase(localStorage.getItem('nb-admin-web:api-base') || DEFAULT_API_BASE)
    await apiRequest(apiBase, trimmed, '/auth/session')
    emit('login', trimmed)
  } catch (err) {
    if (err.status === 401) {
      error.value = 'Token 验证失败，请检查后重试。'
    } else {
      error.value = extractErrorMessage(err)
    }
  } finally {
    loading.value = false
  }
}

function handleSkip() {
  emit('login', '')
}
</script>

<style scoped>
.admin-login-root {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--admin-shell-bg);
  padding: 24px;
}

.admin-login-card {
  width: min(420px, 100%);
  background: var(--admin-surface);
  border: 1px solid var(--admin-border);
  border-radius: 12px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.10);
  overflow: hidden;
}

.admin-login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 36px 32px 20px;
  background: linear-gradient(135deg, #3f51b5, #5c6bc0);
  color: #ffffff;
}

.admin-login-icon {
  font-size: 40px;
  opacity: 0.9;
}

.admin-login-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0;
}

.admin-login-subtitle {
  font-size: 14px;
  opacity: 0.8;
  margin: 0;
}

.admin-login-body {
  padding: 28px 32px 20px;
}

.admin-login-field {
  margin-bottom: 16px;
}

.admin-login-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--admin-text-secondary);
  line-height: 1.5;
}

.admin-login-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 16px;
  border-radius: 6px;
  background: rgba(198, 40, 40, 0.08);
  border: 1px solid rgba(198, 40, 40, 0.16);
  color: var(--admin-error);
  font-size: 13px;
}

.admin-login-error .material-icons {
  font-size: 18px;
  flex-shrink: 0;
}

.admin-login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 2px;
}

.admin-login-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 12px 32px 20px;
  font-size: 13px;
  color: var(--admin-text-secondary);
}

.admin-login-footer .mdui-btn {
  font-size: 13px;
  color: var(--admin-primary);
  min-height: 28px;
  padding: 0 8px;
}
</style>
