import React from 'react'
import { ChevronRight, Shield } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Chat } from '../store'

interface ChatCardProps {
  chat: Chat
}

export function ChatCard({ chat }: ChatCardProps) {
  const navigate = useNavigate()
  const s = chat.settings
  const activeCount = [
    s?.captcha_enabled,
    s?.ai_censor_enabled,
    s?.antiraid_enabled,
    s?.clean_chat_enabled,
    s?.link_filter_enabled,
    s?.stop_words_filter_enabled,
  ].filter(Boolean).length

  const suffix = activeCount === 1 ? 'ь' : activeCount < 5 ? 'я' : 'ей'

  return (
    <button
      onClick={() => navigate(`/chat/${chat.id}`)}
      style={{
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '14px 16px',
        background: '#1C1C1E',
        borderRadius: 16,
        border: '1px solid rgba(255,255,255,0.08)',
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'background 0.15s',
      }}
      onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = '#2C2C2E')}
      onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = '#1C1C1E')}
    >
      {/* Icon */}
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: 12,
          background: 'rgba(255,255,255,0.06)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          overflow: 'hidden',
          position: 'relative'
        }}
      >
        <img 
          src={`/api/chats/${chat.id}/avatar`} 
          alt={chat.title}
          style={{ width: '100%', height: '100%', objectFit: 'cover', position: 'absolute', zIndex: 1 }}
          onError={(e) => {
            e.currentTarget.style.display = 'none';
          }}
        />
        <Shield size={20} color="rgba(255,255,255,0.65)" style={{ zIndex: 0 }} />
      </div>

      {/* Info */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 15,
            fontWeight: 600,
            color: '#FFFFFF',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {chat.title}
        </div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.40)', marginTop: 3 }}>
          {activeCount > 0
            ? `${activeCount} модул${suffix} активно`
            : 'Нет активных модулей'}
        </div>
      </div>

      <ChevronRight size={16} color="rgba(255,255,255,0.22)" />
    </button>
  )
}
