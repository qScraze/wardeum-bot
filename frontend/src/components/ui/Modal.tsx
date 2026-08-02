import React, { useEffect } from 'react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'flex-end',
      }}
    >
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(0,0,0,0.65)',
          backdropFilter: 'blur(6px)',
        }}
      />

      {/* Sheet */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          background: '#1C1C1E',
          borderRadius: '20px 20px 0 0',
          borderTop: '1px solid rgba(255,255,255,0.08)',
          padding: '20px 20px calc(20px + env(safe-area-inset-bottom,0px))',
          maxHeight: '88vh',
          overflowY: 'auto',
        }}
      >
        {/* Handle */}
        <div
          style={{
            width: 36,
            height: 4,
            borderRadius: 4,
            background: 'rgba(255,255,255,0.20)',
            margin: '0 auto 20px',
          }}
        />
        {title && (
          <h3
            style={{
              fontSize: 17,
              fontWeight: 600,
              marginBottom: 20,
              color: '#FFFFFF',
            }}
          >
            {title}
          </h3>
        )}
        {children}
      </div>
    </div>
  )
}
