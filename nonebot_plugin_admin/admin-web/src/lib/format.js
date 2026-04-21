function toDate(value) {
  if (value === null || value === undefined || value === '') return null
  if (value instanceof Date) return value

  const numeric = Number(value)
  if (Number.isFinite(numeric) && String(value).trim() !== '') {
    const millis = numeric < 1e12 ? numeric * 1000 : numeric
    const date = new Date(millis)
    if (!Number.isNaN(date.getTime())) return date
  }

  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatNumber(value) {
  const numeric = Number(value || 0)
  return Number.isFinite(numeric) ? numeric.toLocaleString('zh-CN') : '--'
}

export function formatDateTime(value) {
  const date = toDate(value)
  if (!date) return '--'
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

export function formatTime(value) {
  const date = toDate(value)
  if (!date) return '--'
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function formatDate(value) {
  const date = toDate(value)
  if (!date) return '--'
  return date.toLocaleDateString('zh-CN')
}

export function formatRelativeMute(timestamp) {
  const numeric = Number(timestamp || 0)
  if (!Number.isFinite(numeric) || numeric <= 0) return '未禁言'
  const now = Date.now() / 1000
  if (numeric <= now) return '未禁言'
  const seconds = Math.max(0, Math.round(numeric - now))
  if (seconds < 60) return `${seconds} 秒后解除`
  if (seconds < 3600) return `${Math.ceil(seconds / 60)} 分钟后解除`
  if (seconds < 86400) return `${Math.ceil(seconds / 3600)} 小时后解除`
  return `${Math.ceil(seconds / 86400)} 天后解除`
}

export function isMemberMuted(member) {
  const numeric = Number(member?.shut_up_timestamp || 0)
  return Number.isFinite(numeric) && numeric > Date.now() / 1000
}

export function levelColor(level) {
  const normalized = String(level || '').toUpperCase()
  if (normalized === 'ERROR') return 'admin-tag admin-tag-error'
  if (normalized === 'WARNING' || normalized === 'WARN') return 'admin-tag admin-tag-warn'
  if (normalized === 'SUCCESS') return 'admin-tag admin-tag-success'
  if (normalized === 'DEBUG') return 'admin-tag admin-tag-debug'
  return 'admin-tag admin-tag-info'
}

export function roleLabel(role) {
  const normalized = String(role || 'member')
  if (normalized === 'owner') return '群主'
  if (normalized === 'admin') return '管理员'
  return '成员'
}

export function initials(text) {
  const raw = String(text || '').trim()
  if (!raw) return '群'
  const safe = raw.replace(/[\s\-_.]+/g, '')
  return safe.slice(0, 2).toUpperCase()
}

export function booleanText(value, trueText = '已启用', falseText = '未启用') {
  return value ? trueText : falseText
}

export function isPlaceholderGroupName(name) {
  const text = String(name || '').trim()
  return /^[?？]\s*\+?\s*\d+$/.test(text)
}

export function isPlaceholderGroupRecord(item) {
  if (!item) return false
  return isPlaceholderGroupName(item.group_name || item.title || item.peer_name || item.peerName || '')
}

export function sumBy(items, key) {
  return (items || []).reduce((sum, item) => sum + Number(item?.[key] || 0), 0)
}

export function parseMessageContent(content) {
  if (!content) return ''
  if (typeof content === 'string') {
    try {
      const parsed = JSON.parse(content)
      return extractTextFromMessage(parsed)
    } catch {
      return content
    }
  }
  return extractTextFromMessage(content)
}

function extractTextFromMessage(data) {
  if (typeof data === 'string') return data
  if (Array.isArray(data)) {
    return data.map(item => {
      if (item.type === 'text' && item.data?.text) return item.data.text
      if (item.type === 'image') return '[图片]'
      if (item.type === 'at') return `@${item.data?.qq || item.data?.name || '用户'}`
      if (item.type === 'face') return '[表情]'
      if (item.type === 'record') return '[语音]'
      if (item.type === 'video') return '[视频]'
      if (item.type === 'file') return '[文件]'
      if (item.type === 'reply') return '[回复]'
      if (item.type === 'forward') return '[转发]'
      if (item.type === 'json') return '[JSON卡片]'
      if (item.type === 'xml') return '[XML卡片]'
      if (item.data?.text) return item.data.text
      return ''
    }).join('').trim()
  }
  if (data.text) return data.text
  if (data.content) return data.content
  return ''
}
