import React, { useEffect } from 'react'
import { Copy, MessageCircle } from 'lucide-react'
import { useStore } from '../store'
import { useTelegram } from '../hooks/useTelegram'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { showToast } from '../components/ui/Toast'
import { useNavigate } from 'react-router-dom'
import { getMe } from '../api/client'

const PLAN_NAMES: Record<string, string> = {
  none: 'Без тарифа', lite: 'Лайт', pro: 'Про', corporate: 'Корпоративный',
}

export function Profile() {
  const { user, setUser } = useStore()
  const navigate = useNavigate()

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => {})
  }, [setUser])


  if (!user) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div className="skeleton" style={{ width: 80, height: 80, borderRadius: '50%' }} />
      </div>
    )
  }

  const { user: tgUser } = useTelegram()
  const photoUrl = tgUser?.photo_url

  const initials = user.first_name.slice(0, 2).toUpperCase()
  const hue = user.first_name.split('').reduce((a, c) => a + c.charCodeAt(0), 0) % 360
  const plan = user.plan ?? 'none'
  const subEnd = user.subscription_end ? new Date(user.subscription_end) : null
  const daysLeft = subEnd
    ? Math.max(0, Math.ceil((subEnd.getTime() - Date.now()) / 86400000))
    : 0

  const copy = (text: string) => navigator.clipboard.writeText(text).then(() => showToast('Скопировано'))

  return (
    <div className="page fade-in" style={{ paddingTop: 32 }}>
      {/* Avatar */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 28 }}>
        {photoUrl ? (
          <img
            src={photoUrl}
            alt={user.first_name}
            style={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              objectFit: 'cover',
              border: '1px solid rgba(255,255,255,0.12)',
              marginBottom: 12,
              boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
            }}
          />
        ) : (
          <div
            style={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              background: `hsl(${hue},18%,22%)`,
              border: '1px solid rgba(255,255,255,0.10)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 28,
              fontWeight: 700,
              color: `hsl(${hue},45%,68%)`,
              marginBottom: 12,
            }}
          >
            {initials}
          </div>
        )}
        <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>{user.first_name}</h1>
        {user.username && (
          <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.40)' }}>@{user.username}</p>
        )}
      </div>

      {/* Subscription card */}
      <p className="section-label">Подписка</p>
      <div className="card" style={{ padding: '16px 18px', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <span style={{ fontSize: 14, color: 'rgba(255,255,255,0.50)' }}>Тариф</span>
          <Badge plan={plan}>{PLAN_NAMES[plan]}</Badge>
        </div>
        {subEnd && daysLeft > 0 ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <span style={{ fontSize: 14, color: 'rgba(255,255,255,0.50)' }}>Истекает</span>
              <span style={{ fontSize: 14, fontWeight: 500 }}>
                {subEnd.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' })}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 14, color: 'rgba(255,255,255,0.50)' }}>Осталось дней</span>
              <span style={{ fontSize: 14, fontWeight: 600 }}>{daysLeft}</span>
            </div>
          </>
        ) : (
          <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.30)' }}>Подписка не активна</p>
        )}
      </div>

      {/* Referral */}
      <p className="section-label">Реферальная ссылка</p>
      <div className="card" style={{ padding: '14px 18px', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
          <span style={{ fontSize: 13, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', color: '#FFFFFF', maxWidth: '70%' }}>
            {`https://t.me/wardeum_bot?start=ref_${user.tg_id}`}
          </span>
          <button
            onClick={() => copy(`https://t.me/wardeum_bot?start=ref_${user.tg_id}`)}
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 8,
              cursor: 'pointer',
              color: 'rgba(255,255,255,0.55)',
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              padding: '6px 10px',
              fontSize: 12,
            }}
          >
            <Copy size={13} />
            Копировать
          </button>
        </div>
      </div>

      {/* Admin panel link */}
      {user.is_admin && (
        <>
          <p className="section-label">Администрирование</p>
          <div className="card" style={{ overflow: 'hidden', marginBottom: 20 }}>
            <button
              onClick={() => navigate('/admin')}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 18px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: '#FFFFFF',
                fontSize: 15,
                fontWeight: 500,
              }}
            >
              Панель администратора
              <span style={{ color: 'rgba(255,255,255,0.30)', fontSize: 18 }}>›</span>
            </button>
          </div>
        </>
      )}

      {/* Support */}
      <Button
        variant="ghost"
        style={{ width: '100%' }}
        onClick={() => window.open('tg://resolve?domain=wardeum_support', '_blank')}
      >
        <MessageCircle size={16} />
        Написать в поддержку
      </Button>
    </div>
  )
}
