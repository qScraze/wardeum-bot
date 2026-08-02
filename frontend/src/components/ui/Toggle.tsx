import React from 'react'

interface ToggleProps {
  checked: boolean
  onChange: (v: boolean) => void
  disabled?: boolean
  size?: 'sm' | 'md'
}

export function Toggle({ checked, onChange, disabled = false, size = 'md' }: ToggleProps) {
  const W = size === 'md' ? 44 : 36
  const H = size === 'md' ? 26 : 20
  const D = size === 'md' ? 20 : 14
  const GAP = 3

  return (
    <button
      role="switch"
      aria-checked={checked}
      aria-disabled={disabled}
      onClick={() => !disabled && onChange(!checked)}
      style={{
        width: W,
        height: H,
        borderRadius: H / 2,
        background: checked ? 'rgba(255,255,255,0.92)' : 'rgba(255,255,255,0.14)',
        position: 'relative',
        cursor: disabled ? 'not-allowed' : 'pointer',
        border: 'none',
        outline: 'none',
        transition: 'background 0.25s ease',
        opacity: disabled ? 0.38 : 1,
        flexShrink: 0,
      }}
    >
      <span
        style={{
          position: 'absolute',
          top: GAP,
          width: D,
          height: D,
          borderRadius: '50%',
          background: checked ? '#0A0A0A' : '#FFFFFF',
          left: checked ? W - D - GAP : GAP,
          transition: 'left 0.28s cubic-bezier(0.34,1.56,0.64,1), background 0.25s ease',
          boxShadow: '0 1px 4px rgba(0,0,0,0.35)',
        }}
      />
    </button>
  )
}
