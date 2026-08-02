import React from 'react'

type BadgeVariant = 'none' | 'lite' | 'pro' | 'corporate' | 'global' | 'success' | 'danger'

const STYLES: Record<BadgeVariant, React.CSSProperties> = {
  none:      { background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.35)', border: '1px solid rgba(255,255,255,0.08)' },
  lite:      { background: 'rgba(255,255,255,0.07)', color: 'rgba(255,255,255,0.55)', border: '1px solid rgba(255,255,255,0.10)' },
  pro:       { background: 'rgba(255,255,255,0.12)', color: '#FFFFFF',                border: '1px solid rgba(255,255,255,0.20)' },
  corporate: { background: 'rgba(255,255,255,0.15)', color: '#FFFFFF',                border: '1px solid rgba(255,255,255,0.25)', fontWeight: 600 },
  global:    { background: 'rgba(255,69,58,0.10)',   color: 'rgba(255,69,58,0.85)',   border: '1px solid rgba(255,69,58,0.18)' },
  success:   { background: 'rgba(48,209,88,0.10)',   color: 'rgba(48,209,88,0.85)',   border: '1px solid rgba(48,209,88,0.18)' },
  danger:    { background: 'rgba(255,69,58,0.10)',   color: 'rgba(255,69,58,0.85)',   border: '1px solid rgba(255,69,58,0.18)' },
}

const PLAN_LABELS: Record<string, string> = {
  none: 'Без тарифа', lite: 'Лайт', pro: 'Про', corporate: 'Корп'
}

interface BadgeProps {
  variant?: BadgeVariant
  children?: React.ReactNode
  plan?: string
  className?: string
  style?: React.CSSProperties
}

export function Badge({ variant, children, plan, style }: BadgeProps) {
  const v: BadgeVariant = variant ?? (plan as BadgeVariant) ?? 'none'
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: 20,
        fontSize: 11,
        fontWeight: 500,
        letterSpacing: '-0.01em',
        ...STYLES[v],
        ...style,
      }}
    >
      {children ?? (plan ? PLAN_LABELS[plan] ?? plan : '')}
    </span>
  )
}
