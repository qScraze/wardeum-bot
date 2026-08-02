import React from 'react'
import { Lock } from 'lucide-react'
import { Toggle } from './ui/Toggle'

interface ProtectionModuleProps {
  icon: React.ReactNode
  title: string
  description: string
  enabled: boolean
  onChange: (v: boolean) => void
  disabled?: boolean
  requiredPlan?: string
  isLast?: boolean
}

const PLAN_LABELS: Record<string, string> = {
  pro: 'Про+',
  corporate: 'Корп',
}

export function ProtectionModule({
  icon,
  title,
  description,
  enabled,
  onChange,
  disabled = false,
  requiredPlan,
  isLast = false,
}: ProtectionModuleProps) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '14px 16px',
        borderBottom: isLast ? 'none' : '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {/* Icon */}
      <div
        style={{
          color: disabled ? 'rgba(255,255,255,0.20)' : 'rgba(255,255,255,0.65)',
          flexShrink: 0,
          display: 'flex',
        }}
      >
        {icon}
      </div>

      {/* Label */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 15,
            fontWeight: 500,
            color: disabled ? 'rgba(255,255,255,0.32)' : '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          {title}
          {disabled && requiredPlan && (
            <span
              style={{
                fontSize: 10,
                fontWeight: 500,
                background: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(255,255,255,0.09)',
                borderRadius: 4,
                padding: '1px 5px',
                color: 'rgba(255,255,255,0.28)',
              }}
            >
              {PLAN_LABELS[requiredPlan] ?? requiredPlan}
            </span>
          )}
        </div>
        <div
          style={{
            fontSize: 12,
            color: 'rgba(255,255,255,0.32)',
            marginTop: 2,
            lineHeight: 1.45,
          }}
        >
          {description}
        </div>
      </div>

      {/* Control */}
      {disabled ? (
        <Lock size={16} color="rgba(255,255,255,0.18)" style={{ flexShrink: 0 }} />
      ) : (
        <Toggle checked={enabled} onChange={onChange} />
      )}
    </div>
  )
}
