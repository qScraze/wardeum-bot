import React, { useState, useCallback } from 'react'

interface ToastProps { message: string; type?: 'success' | 'error' | 'info' }

let showToastFn: ((msg: string, type?: ToastProps['type']) => void) | null = null

export function showToast(message: string, type: ToastProps['type'] = 'success') {
  showToastFn?.(message, type)
}

export function ToastProvider() {
  const [toasts, setToasts] = useState<(ToastProps & { id: number })[]>([])

  const show = useCallback((message: string, type: ToastProps['type'] = 'success') => {
    const id = Date.now()
    setToasts((t) => [...t, { id, message, type }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3000)
  }, [])

  showToastFn = show

  const COLORS: Record<string, string> = {
    success: 'rgba(48,209,88,0.12)',
    error:   'rgba(255,69,58,0.12)',
    info:    'rgba(255,255,255,0.08)',
  }
  const TEXT: Record<string, string> = {
    success: 'rgba(48,209,88,0.95)',
    error:   'rgba(255,69,58,0.95)',
    info:    '#FFFFFF',
  }
  const BORDER: Record<string, string> = {
    success: 'rgba(48,209,88,0.22)',
    error:   'rgba(255,69,58,0.22)',
    info:    'rgba(255,255,255,0.12)',
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 16,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        alignItems: 'center',
        width: 'calc(100% - 32px)',
        maxWidth: 360,
      }}
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          style={{
            background: COLORS[t.type ?? 'info'],
            border: `1px solid ${BORDER[t.type ?? 'info']}`,
            borderRadius: 12,
            padding: '10px 16px',
            fontSize: 14,
            fontWeight: 500,
            color: TEXT[t.type ?? 'info'],
            backdropFilter: 'blur(20px)',
            animation: 'fadeIn 0.2s ease',
            width: '100%',
            textAlign: 'center',
          }}
        >
          {t.message}
        </div>
      ))}
    </div>
  )
}
