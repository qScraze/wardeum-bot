import React from 'react'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  icon?: React.ReactNode
  rightElement?: React.ReactNode
}

export function Input({ label, error, hint, icon, rightElement, style, ...props }: InputProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {label && (
        <label
          style={{
            fontSize: 12,
            fontWeight: 500,
            color: 'rgba(255,255,255,0.45)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
          }}
        >
          {label}
        </label>
      )}
      <div style={{ position: 'relative' }}>
        {icon && (
          <span
            style={{
              position: 'absolute',
              left: 14,
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'rgba(255,255,255,0.30)',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {icon}
          </span>
        )}
        <input
          {...props}
          style={{
            width: '100%',
            background: 'rgba(255,255,255,0.05)',
            border: `1px solid ${error ? 'rgba(255,69,58,0.4)' : 'rgba(255,255,255,0.08)'}`,
            borderRadius: 12,
            padding: `12px ${rightElement ? '44px' : '16px'} 12px ${icon ? '42px' : '16px'}`,
            fontSize: 15,
            color: '#FFFFFF',
            fontFamily: 'Inter, sans-serif',
            outline: 'none',
            transition: 'border-color 0.2s',
            ...style,
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = error
              ? 'rgba(255,69,58,0.7)'
              : 'rgba(255,255,255,0.28)'
            props.onFocus?.(e)
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = error
              ? 'rgba(255,69,58,0.4)'
              : 'rgba(255,255,255,0.08)'
            props.onBlur?.(e)
          }}
        />
        {rightElement && (
          <span
            style={{
              position: 'absolute',
              right: 12,
              top: '50%',
              transform: 'translateY(-50%)',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {rightElement}
          </span>
        )}
      </div>
      {error && <p style={{ fontSize: 12, color: 'rgba(255,69,58,0.85)' }}>{error}</p>}
      {hint && !error && <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.30)' }}>{hint}</p>}
    </div>
  )
}
