import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 15000,
})

// Attach Telegram initData as Bearer token
api.interceptors.request.use((config) => {
  const initData = window.Telegram?.WebApp?.initData
  if (initData) {
    config.headers.Authorization = `Bearer ${initData}`
  } else if (import.meta.env.DEV) {
    // Dev fallback — allows testing without real Telegram
    config.headers.Authorization = 'Bearer dev_admin'
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      console.error('[Wardeum] Unauthorized — invalid initData')
    }
    return Promise.reject(err)
  }
)

// ─── User ─────────────────────────────────────────────────────────────────────
export const getMe = () => api.get('/api/me').then((r) => r.data)

// ─── Chats ────────────────────────────────────────────────────────────────────
export const getChats = () => api.get('/api/chats').then((r) => r.data)
export const addChat = (data: { tg_id: number; title: string; username?: string }) =>
  api.post('/api/chats', data).then((r) => r.data)
export const getChat = (id: number) => api.get(`/api/chats/${id}`).then((r) => r.data)
export const updateChatSettings = (id: number, data: Record<string, unknown>) =>
  api.put(`/api/chats/${id}/settings`, data).then((r) => r.data)
export const deleteChat = (id: number) => api.delete(`/api/chats/${id}`)

// ─── Subscription ─────────────────────────────────────────────────────────────
export const getPlans = () => api.get('/api/subscription/plans').then((r) => r.data)
export const applyPromo = (code: string) =>
  api.post('/api/subscription/promo', { code }).then((r) => r.data)
export const activateKey = (key: string) =>
  api.post('/api/subscription/key', { key }).then((r) => r.data)
export const getReferral = () => api.get('/api/subscription/referral').then((r) => r.data)

// ─── Blacklist ────────────────────────────────────────────────────────────────
export const getBlacklist = (page = 1, limit = 20) =>
  api.get(`/api/blacklist?page=${page}&limit=${limit}`).then((r) => r.data)
export const removeFromBlacklist = (tgId: number) =>
  api.delete(`/api/blacklist/${tgId}`)

// ─── Admin ────────────────────────────────────────────────────────────────────
export const getAdminStats = () => api.get('/api/admin/stats').then((r) => r.data)
export const getAdminUsers = (page = 1, search = '') =>
  api.get(`/api/admin/users?page=${page}&search=${encodeURIComponent(search)}`).then((r) => r.data)
export const grantPlan = (tgId: number, plan: string, days: number) =>
  api.post(`/api/admin/users/${tgId}/grant`, { plan, days }).then((r) => r.data)
export const createPromo = (data: unknown) =>
  api.post('/api/admin/promo', data).then((r) => r.data)
export const listPromos = () => api.get('/api/admin/promos').then((r) => r.data)
export const createKeys = (data: unknown) =>
  api.post('/api/admin/keys', data).then((r) => r.data)
export const listKeys = () => api.get('/api/admin/keys').then((r) => r.data)
export const deleteKey = (keyId: number) => api.delete(`/api/admin/keys/${keyId}`)
export const updateForceSub = (data: { enabled: boolean; channel_id?: number | null }) =>
  api.put('/api/admin/force-sub', data).then((r) => r.data)
export const getForceSub = () => api.get('/api/admin/force-sub').then((r) => r.data)
export const getAdminBlacklist = (page = 1, globalOnly = false) =>
  api
    .get(`/api/admin/blacklist?page=${page}&global_only=${globalOnly}`)
    .then((r) => r.data)
export const addToAdminBlacklist = (data: unknown) =>
  api.post('/api/admin/blacklist', data).then((r) => r.data)
export const removeFromAdminBlacklist = (tgId: number) =>
  api.delete(`/api/admin/blacklist/${tgId}`)
