import { useEffect } from 'react'

// Extend Window for Telegram types
declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        ready: () => void
        expand: () => void
        close: () => void
        setHeaderColor: (color: string) => void
        setBackgroundColor: (color: string) => void
        initData: string
        initDataUnsafe: {
          user?: {
            id: number
            first_name: string
            last_name?: string
            username?: string
            is_premium?: boolean
          }
          start_param?: string
        }
        colorScheme: 'light' | 'dark'
        HapticFeedback: {
          impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
          notificationOccurred: (type: 'error' | 'success' | 'warning') => void
          selectionChanged: () => void
        }
        BackButton: {
          show: () => void
          hide: () => void
          onClick: (fn: () => void) => void
          offClick: (fn: () => void) => void
          isVisible: boolean
        }
        showAlert: (message: string, callback?: () => void) => void
        showConfirm: (message: string, callback?: (ok: boolean) => void) => void
      }
    }
  }
}

export function useTelegram() {
  const tg = window.Telegram?.WebApp

  useEffect(() => {
    if (tg) {
      tg.ready()
      tg.expand()
      tg.setHeaderColor('#0A0A0A')
      tg.setBackgroundColor('#0A0A0A')
    }
  }, [])

  return {
    tg,
    user: tg?.initDataUnsafe?.user,
    initData: tg?.initData ?? '',
    colorScheme: tg?.colorScheme ?? 'dark',
    haptic: tg?.HapticFeedback,
    backButton: tg?.BackButton,
  }
}
