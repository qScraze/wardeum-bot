import { create } from 'zustand'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface UserProfile {
  id: number
  tg_id: number
  username?: string
  first_name: string
  plan: 'none' | 'lite' | 'pro' | 'corporate'
  subscription_end?: string
  extra_days: number
  referral_code: string
  is_admin: boolean
}

export interface ChatSettings {
  ai_censor_enabled: boolean
  captcha_enabled: boolean
  antiraid_enabled: boolean
  clean_chat_enabled: boolean
  link_filter_enabled: boolean
  stop_words_filter_enabled: boolean
  stop_words: string[]
  antiraid_threshold: number
  antiraid_window: number
  captcha_timeout: number
}

export interface Chat {
  id: number
  tg_id: number
  title: string
  username?: string
  is_active: boolean
  settings: ChatSettings
}

interface AppState {
  user: UserProfile | null
  chats: Chat[]
  isInitialized: boolean
  isLoading: boolean
  // actions
  setUser: (user: UserProfile | null) => void
  setChats: (chats: Chat[]) => void
  addChat: (chat: Chat) => void
  removeChat: (chatId: number) => void
  updateChatSettings: (chatId: number, settings: Partial<ChatSettings>) => void
  setInitialized: (v: boolean) => void
  setLoading: (v: boolean) => void
}

// ─── Store ────────────────────────────────────────────────────────────────────

export const useStore = create<AppState>((set) => ({
  user: null,
  chats: [],
  isInitialized: false,
  isLoading: false,

  setUser: (user) => set({ user }),
  setChats: (chats) => set({ chats }),
  addChat: (chat) => set((s) => ({ chats: [...s.chats, chat] })),
  removeChat: (chatId) =>
    set((s) => ({ chats: s.chats.filter((c) => c.id !== chatId) })),
  updateChatSettings: (chatId, settings) =>
    set((s) => ({
      chats: s.chats.map((c) =>
        c.id === chatId ? { ...c, settings: { ...c.settings, ...settings } } : c
      ),
    })),
  setInitialized: (isInitialized) => set({ isInitialized }),
  setLoading: (isLoading) => set({ isLoading }),
}))
