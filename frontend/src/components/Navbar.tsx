import React, { useRef, useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { MessageSquare, CreditCard, ShieldOff, User } from 'lucide-react'

const TABS = [
  { id: 'home',         path: '/',             label: 'Чаты',     Icon: MessageSquare },
  { id: 'subscription', path: '/subscription', label: 'Тариф',    Icon: CreditCard },
  { id: 'blacklist',    path: '/blacklist',    label: 'ЧС',       Icon: ShieldOff },
  { id: 'profile',      path: '/profile',      label: 'Профиль',  Icon: User },
]

export function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()
  const navRef = useRef<HTMLDivElement>(null)
  const [pill, setPill] = useState({ left: 0, width: 0, ready: false })

  const activeIdx = Math.max(
    0,
    TABS.findIndex((t) => t.path === location.pathname)
  )

  useEffect(() => {
    const nav = navRef.current
    if (!nav) return
    const tabs = nav.querySelectorAll('[data-tab-btn]')
    const el = tabs[activeIdx] as HTMLElement | undefined
    if (el) {
      setPill({ left: el.offsetLeft, width: el.offsetWidth, ready: true })
    }
  }, [activeIdx])

  return (
    <nav
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        background: 'rgba(10,10,10,0.88)',
        backdropFilter: 'blur(22px) saturate(180%)',
        WebkitBackdropFilter: 'blur(22px) saturate(180%)',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        paddingBottom: 'env(safe-area-inset-bottom, 0px)',
      }}
    >
      <div
        ref={navRef}
        style={{ position: 'relative', display: 'flex', padding: '8px 6px 2px' }}
      >
        {/* Liquid glass pill indicator */}
        {pill.ready && (
          <div
            style={{
              position: 'absolute',
              top: 8,
              left: pill.left,
              width: pill.width,
              height: 'calc(100% - 10px)',
              background: 'rgba(255,255,255,0.09)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: 50,
              transition: pill.ready
                ? 'left 0.38s cubic-bezier(0.34,1.56,0.64,1), width 0.38s cubic-bezier(0.34,1.56,0.64,1)'
                : 'none',
              pointerEvents: 'none',
            }}
          />
        )}

        {TABS.map((tab, i) => {
          const isActive = i === activeIdx
          return (
            <button
              key={tab.id}
              data-tab-btn={tab.id}
              onClick={() => navigate(tab.path)}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 3,
                padding: '8px 4px 10px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: isActive ? '#FFFFFF' : 'rgba(255,255,255,0.30)',
                transition: 'color 0.2s ease',
                position: 'relative',
                zIndex: 1,
                minWidth: 0,
              }}
            >
              <tab.Icon
                size={22}
                strokeWidth={isActive ? 2.2 : 1.5}
                style={{ transition: 'stroke-width 0.2s' }}
              />
              {isActive && (
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 600,
                    letterSpacing: '-0.01em',
                    lineHeight: 1,
                    animation: 'fadeIn 0.15s ease',
                  }}
                >
                  {tab.label}
                </span>
              )}
            </button>
          )
        })}
      </div>
    </nav>
  )
}
