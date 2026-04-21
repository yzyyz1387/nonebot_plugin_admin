export const DEFAULT_API_BASE = import.meta.env.VITE_DEFAULT_API_BASE || '/admin-dashboard/api'

function trimTrailingSlash(value) {
  const text = String(value || '').trim()
  if (!text || text === '/') return text
  return text.replace(/\/+$/, '')
}

export function normalizeApiBase(value) {
  return trimTrailingSlash(value || DEFAULT_API_BASE) || DEFAULT_API_BASE
}

function buildRequestUrl(apiBase, path, params) {
  const normalizedBase = normalizeApiBase(apiBase)
  const normalizedPath = String(path || '').startsWith('/') ? String(path) : `/${path || ''}`
  const rawUrl = normalizedBase.startsWith('http://') || normalizedBase.startsWith('https://')
    ? `${normalizedBase}${normalizedPath}`
    : `${window.location.origin}${normalizedBase}${normalizedPath}`
  const url = new URL(rawUrl)

  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    url.searchParams.set(key, String(value))
  })

  return url.toString()
}

export function extractErrorMessage(error) {
  if (!error) return '请求失败'
  if (typeof error === 'string') return error
  if (error?.message) return error.message
  return '请求失败'
}

export async function apiRequest(apiBase, token, path, options = {}) {
  const { method = 'GET', params, body, headers = {}, timeout = 30000 } = options
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(buildRequestUrl(apiBase, path, params), {
      method,
      headers: {
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { 'X-Admin-Token': token } : {}),
        ...headers
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal
    })

    const contentType = response.headers.get('content-type') || ''
    const payload = contentType.includes('application/json') ? await response.json() : await response.text()

    if (!response.ok) {
      const detail = typeof payload === 'object' && payload !== null
        ? payload.detail || payload.message || JSON.stringify(payload)
        : String(payload)
      const error = new Error(detail || `HTTP ${response.status}`)
      error.status = response.status
      error.payload = payload
      throw error
    }

    return payload
  } catch (error) {
    if (error.name === 'AbortError') {
      const timeoutError = new Error('请求超时，请稍后重试')
      timeoutError.isTimeout = true
      throw timeoutError
    }
    throw error
  } finally {
    clearTimeout(timeoutId)
  }
}
