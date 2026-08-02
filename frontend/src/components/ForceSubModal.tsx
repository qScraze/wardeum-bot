import React, { useState } from 'react'
import { ShieldAlert, ExternalLink, RotateCw } from 'lucide-react'
import { useStore } from '../store'
import { checkSubscription } from '../api/client'
import { Button } from './ui/Button'
import { showToast } from './ui/Toast'

export function ForceSubModal() {
  const { user, setUser } = useStore()
  const [checking, setChecking] = useState(false)

  if (!user || user.is_subscribed !== false) {
    return null
  }

  const handleOpenChannel = () => {
    const url = user.force_sub_url || 'https://t.me'
    if (window.Telegram?.WebApp?.openTelegramLink) {
      window.Telegram.WebApp.openTelegramLink(url)
    } else {
      window.open(url, '_blank')
    }
  }

  const handleVerify = async () => {
    setChecking(true)
    try {
      const res = await checkSubscription()
      if (res.is_subscribed) {
        showToast('Подписка подтверждена!', 'success')
        setUser({ ...user, is_subscribed: true })
      } else {
        showToast('Вы всё ещё не подписаны на канал', 'error')
      }
    } catch {
      showToast('Ошибка проверки подписки', 'error')
    } finally {
      setChecking(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(10, 10, 10, 0.88)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
      }}
      className="fade-in"
    >
      <div
        className="card"
        style={{
          maxWidth: 380,
          width: '100%',
          padding: '28px 24px',
          textAlign: 'center',
          background: 'linear-gradient(180deg, #1C1C1E 0%, #121214 100%)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.8)',
          borderRadius: 24,
        }}
      >
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: 'rgba(255, 59, 48, 0.12)',
            border: '1px solid rgba(255, 59, 48, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px auto',
            color: '#FF453A',
          }}
        >
          <ShieldAlert size={32} />
        </div>

        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 10, color: '#FFFFFF', letterSpacing: '-0.01em' }}>
          Обязательная подписка
        </h2>

        <p style={{ fontSize: 14, color: 'rgba(255, 255, 255, 0.65)', lineHeight: 1.5, marginBottom: 24 }}>
          Для использования приложения необходимо подписаться на наш официальный Telegram-канал.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Button
            onClick={handleOpenChannel}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              fontSize: 15,
              fontWeight: 600,
              padding: '14px 18px',
            }}
          >
            <span>Присоединиться к каналу</span>
            <ExternalLink size={16} />
          </Button>

          <Button
            variant="secondary"
            loading={checking}
            onClick={handleVerify}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              fontSize: 14,
              fontWeight: 500,
              padding: '12px 18px',
            }}
          >
            <RotateCw size={15} />
            <span>Проверить подписку</span>
          </Button>
        </div>
      </div>
    </div>
  )
}
