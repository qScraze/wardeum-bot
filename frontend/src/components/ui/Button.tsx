import React from 'react'

type Variant = 'primary' | 'ghost' | 'danger' | 'surface'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  children: React.ReactNode
}

const VARIANTS: Record<Variant, React.CSSProperties> = {
  primary: {
    background: '#FFFFFF',
    color: '#0A0A0A',
    border: 'none',
  },
  ghost: {
    background: 'transparent',
    color: '#FFFFFF',
    border: '1px solid rgba(255,255,255,0.18)',
  },
  danger: {
    background: 'rgba(255,69,58,0.10)',
    color: 'rgba(255,69,58,0.9)',
    border: '1px solid rgba(255,69,58,0.18)',
  },
  surface: {
    background: 'rgba(255,255,255,0.07)',
    color: '#FFFFFF',
    border: '1px solid rgba(255,255,255,0.08)',
  },
}

const SIZES: Record<Size, React.CSSProperties> = {
  sm: { padding: '6px 12px', fontSize: 13, borderRadius: 10, gap: 6 },
  md: { padding: '10px 18px', fontSize: 14, borderRadius: 12, gap: 8 },
  lg: { padding: '14px 24px', fontSize: 15, borderRadius: 14, gap: 8 },
}

const Spinner = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    style={{ animation: 'spin 0.8s linear infinite' }}
  >
    <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>
    <circle cx="12" cy="12" r="9" strokeDasharray="28" strokeDashoffset="8" strokeLinecap="round" />
  </svg>
)

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  disabled,
  style,
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'Inter, sans-serif',
        fontWeight: 500,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.4 : 1,
        transition: 'opacity 0.15s, transform 0.1s',
        userSelect: 'none',
        ...VARIANTS[variant],
        ...SIZES[size],
        ...style,
      }}
      onMouseDown={(e) => {
        ;(e.currentTarget as HTMLButtonElement).style.transform = 'scale(0.96)'
        props.onMouseDown?.(e)
      }}
      onMouseUp={(e) => {
        ;(e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)'
        props.onMouseUp?.(e)
      }}
      onMouseLeave={(e) => {
        ;(e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)'
        props.onMouseLeave?.(e)
      }}
    >
      {loading && <Spinner />}
      {children}
    </button>
  )
}
