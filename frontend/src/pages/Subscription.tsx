import React, { useState } from 'react'
import { Check, Copy, Tag, Key } from 'lucide-react'
import { useStore } from '../store'
import { useApi } from '../hooks/useApi'
import { getMe, getPlans, applyPromo, activateKey, getReferral } from '../api/client'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { showToast } from '../components/ui/Toast'

interface PlanInfo {
  id: string
  name: string
  price: number
  max_chats: number
  features: string[]
}

interface ReferralInfo {
  code: string
  url: string
  total_referrals: number
  total_bonus_days: number
}

export function Subscription() {
  const { user, setUser } = useStore()
  const [promoCode, setPromoCode] = useState('')
  const [activationKey, setActivationKey] = useState('')
  const [applyingPromo, setApplyingPromo] = useState(false)
  const [activatingKey, setActivatingKey] = useState(false)

  const { data: plans, loading: plansLoading } = useApi<PlanInfo[]>(getPlans, [])
  const { data: referral } = useApi<ReferralInfo>(getReferral, [])

  const refreshUser = async () => {
    try {
      const updatedUser = await getMe()
      setUser(updatedUser)
    } catch {
      // ignore
    }
  }

  const now = new Date()
  const subEnd = user?.subscription_end ? new Date(user.subscription_end) : null
  const daysLeft = subEnd
    ? Math.max(0, Math.ceil((subEnd.getTime() - now.getTime()) / 86400000))
    : 0

  const handleApplyPromo = async () => {
    if (!promoCode.trim()) return
    setApplyingPromo(true)
    try {
      const result = await applyPromo(promoCode.trim())
      showToast(result.message, 'success')
      setPromoCode('')
      await refreshUser()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      showToast(err?.response?.data?.detail ?? 'Промокод не подходит', 'error')
    } finally {
      setApplyingPromo(false)
    }
  }

  const handleActivateKey = async () => {
    if (!activationKey.trim()) return
    setActivatingKey(true)
    try {
      const result = await activateKey(activationKey.trim())
      showToast(result.message, 'success')
      setActivationKey('')
      await refreshUser()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      showToast(err?.response?.data?.detail ?? 'Ключ не подходит', 'error')
    } finally {
      setActivatingKey(false)
    }
  }

  const copy = (text: string, msg = 'Скопировано') => {
    navigator.clipboard.writeText(text).then(() => showToast(msg, 'success'))
  }

  const currentPlan = user?.plan ?? 'none'

  return (
    <div className="page fade-in" style={{ paddingTop: 20 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 20 }}>
        Подписка
      </h1>

      {/* Current plan card */}
      <div
        className="card"
        style={{ padding: '18px 20px', marginBottom: 24 }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.40)', marginBottom: 6 }}>
              Текущий тариф
            </p>
            <Badge plan={currentPlan} style={{ fontSize: 13, padding: '4px 12px' }} />
          </div>
          <div style={{ textAlign: 'right' }}>
            {subEnd && daysLeft > 0 ? (
              <>
                <p style={{ fontSize: 20, fontWeight: 700 }}>{daysLeft}</p>
                <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.40)' }}>дней осталось</p>
              </>
            ) : (
              <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.35)' }}>Нет активной подписки</p>
            )}
          </div>
        </div>
      </div>

      {/* Plans */}
      {plansLoading ? (
        <div className="skeleton" style={{ height: 200, marginBottom: 20 }} />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
          {plans?.map((plan) => {
            const isActive = plan.id === currentPlan
            return (
              <div
                key={plan.id}
                className="card"
                style={{
                  padding: '16px 18px',
                  border: isActive
                    ? '1px solid rgba(255,255,255,0.25)'
                    : '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 16, fontWeight: 700 }}>{plan.name}</span>
                    {isActive && (
                      <Badge variant="success" style={{ fontSize: 10 }}>Активен</Badge>
                    )}
                  </div>
                  <span style={{ fontSize: 16, fontWeight: 600 }}>
                    {plan.price}
                    <span style={{ fontSize: 12, fontWeight: 400, color: 'rgba(255,255,255,0.45)' }}>
                      {' '} ₽/мес
                    </span>
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)', marginBottom: 10 }}>
                  До {plan.max_chats} чатов
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {plan.features.map((f) => (
                    <div key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                      <Check size={13} color="rgba(255,255,255,0.45)" style={{ flexShrink: 0, marginTop: 1 }} />
                      <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.55)', lineHeight: 1.4 }}>{f}</span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Promo code */}
      <p className="section-label">Промокод</p>
      <div className="card" style={{ padding: '16px', marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 10 }}>
          <div style={{ flex: 1 }}>
            <Input
              placeholder="WARDEUM2024"
              value={promoCode}
              onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
              icon={<Tag size={16} />}
            />
          </div>
          <Button
            loading={applyingPromo}
            onClick={handleApplyPromo}
            disabled={!promoCode.trim()}
            size="md"
          >
            Применить
          </Button>
        </div>
      </div>

      {/* Activation key */}
      <p className="section-label">Ключ активации</p>
      <div className="card" style={{ padding: '16px', marginBottom: 20 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Input
            placeholder="XXXX-XXXX-XXXXX-XXXXX"
            value={activationKey}
            onChange={(e) => setActivationKey(e.target.value.toUpperCase())}
            icon={<Key size={16} />}
            hint="Формат: XXXX-XXXX-XXXXX-XXXXX"
          />
          <Button
            loading={activatingKey}
            onClick={handleActivateKey}
            disabled={!activationKey.trim()}
            style={{ width: '100%' }}
          >
            Активировать
          </Button>
        </div>
      </div>

      {/* Referral */}
      {referral && (
        <>
          <p className="section-label">Реферальная программа</p>
          <div className="card" style={{ padding: '16px', marginBottom: 8 }}>
            <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.40)', marginBottom: 12, lineHeight: 1.5 }}>
              Приглашайте друзей и получайте +5 бесплатных дней за каждого оплатившего подписку
            </p>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 10,
                padding: '10px 14px',
                marginBottom: 10,
              }}
            >
              <span style={{ fontFamily: 'monospace', fontSize: 15, letterSpacing: '0.1em', color: '#FFFFFF' }}>
                {referral.code}
              </span>
              <button
                onClick={() => copy(referral.url, 'Ссылка скопирована')}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'rgba(255,255,255,0.50)',
                  display: 'flex',
                  padding: 4,
                }}
              >
                <Copy size={16} />
              </button>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div
                style={{
                  flex: 1,
                  background: 'rgba(255,255,255,0.04)',
                  borderRadius: 10,
                  padding: '10px 14px',
                  textAlign: 'center',
                }}
              >
                <p style={{ fontSize: 20, fontWeight: 700 }}>{referral.total_referrals}</p>
                <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.38)', marginTop: 2 }}>Рефералов</p>
              </div>
              <div
                style={{
                  flex: 1,
                  background: 'rgba(255,255,255,0.04)',
                  borderRadius: 10,
                  padding: '10px 14px',
                  textAlign: 'center',
                }}
              >
                <p style={{ fontSize: 20, fontWeight: 700 }}>{referral.total_bonus_days}</p>
                <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.38)', marginTop: 2 }}>Бонусных дней</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
