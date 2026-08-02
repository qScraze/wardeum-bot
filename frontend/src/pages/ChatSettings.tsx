import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ChevronLeft, Shield, Zap, Brain, Link, AlertTriangle,
  Trash2, Trash,
} from 'lucide-react'
import { useStore } from '../store'
import { updateChatSettings, deleteChat } from '../api/client'
import { ProtectionModule } from '../components/ProtectionModule'
import { Button } from '../components/ui/Button'
import { Modal } from '../components/ui/Modal'
import { showToast } from '../components/ui/Toast'
import { useState } from 'react'

type Plan = 'none' | 'lite' | 'pro' | 'corporate'

function isPro(plan: Plan) { return plan === 'pro' || plan === 'corporate' }

export function ChatSettings() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { chats, user, updateChatSettings: storeUpdate, removeChat } = useStore()
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const chat = chats.find((c) => c.id === Number(id))

  if (!chat) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100dvh' }}>
        <p style={{ color: 'rgba(255,255,255,0.40)' }}>Чат не найден</p>
      </div>
    )
  }

  const plan: Plan = (user?.plan ?? 'none') as Plan
  const s = chat.settings

  const toggle = async (field: string, value: boolean) => {
    // Optimistic update
    storeUpdate(chat.id, { [field]: value })
    try {
      await updateChatSettings(chat.id, { [field]: value })
      showToast(value ? 'Включено' : 'Выключено', 'success')
    } catch (e: unknown) {
      // Revert
      storeUpdate(chat.id, { [field]: !value })
      const err = e as { response?: { data?: { detail?: string } } }
      showToast(err?.response?.data?.detail ?? 'Ошибка', 'error')
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await deleteChat(chat.id)
      removeChat(chat.id)
      showToast('Чат удалён', 'success')
      navigate('/')
    } catch {
      showToast('Ошибка удаления', 'error')
    } finally {
      setDeleting(false)
      setShowDeleteModal(false)
    }
  }

  const SectionCard = ({ children }: { children: React.ReactNode }) => (
    <div className="card" style={{ overflow: 'hidden', marginBottom: 8 }}>
      {children}
    </div>
  )

  return (
    <div style={{ minHeight: '100dvh', paddingBottom: 40 }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '16px 16px 12px',
          position: 'sticky',
          top: 0,
          background: 'rgba(10,10,10,0.90)',
          backdropFilter: 'blur(12px)',
          zIndex: 10,
          borderBottom: '1px solid rgba(255,255,255,0.05)',
        }}
      >
        <button
          onClick={() => navigate('/')}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'rgba(255,255,255,0.70)',
            display: 'flex',
            padding: 4,
          }}
        >
          <ChevronLeft size={22} />
        </button>
        <div style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, overflow: 'hidden', flexShrink: 0, position: 'relative', background: 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <img 
              src={`/api/chats/${chat.id}/avatar`} 
              alt={chat.title}
              style={{ width: '100%', height: '100%', objectFit: 'cover', position: 'absolute', zIndex: 1 }}
              onError={(e) => {
                e.currentTarget.style.display = 'none';
              }}
            />
            <Shield size={16} color="rgba(255,255,255,0.65)" style={{ zIndex: 0 }} />
          </div>
          <h1
            style={{
              fontSize: 17,
              fontWeight: 600,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {chat.title}
          </h1>
        </div>
      </div>

      <div style={{ padding: '16px 16px 0' }}>
        {/* СЕКЦИЯ: Защита от ботов */}
        <p className="section-label">Защита от ботов</p>
        <SectionCard>
          <ProtectionModule
            icon={<Shield size={20} />}
            title="GIF-Капча"
            description="Анимированная капча в личных сообщениях для новичков"
            enabled={s.captcha_enabled}
            onChange={(v) => toggle('captcha_enabled', v)}
          />
          <ProtectionModule
            icon={<Zap size={20} />}
            title="Anti-Raid"
            description="Автоматическая защита от массовых атак ботов"
            enabled={s.antiraid_enabled}
            onChange={(v) => toggle('antiraid_enabled', v)}
            disabled={!isPro(plan)}
            requiredPlan="pro"
            isLast
          />
        </SectionCard>

        {/* СЕКЦИЯ: Контент */}
        <p className="section-label" style={{ marginTop: 20 }}>Контент</p>
        <SectionCard>
          <ProtectionModule
            icon={<Brain size={20} />}
            title="ИИ-Цензор"
            description="Gemini 2.0 Flash анализирует сообщения в реальном времени"
            enabled={s.ai_censor_enabled}
            onChange={(v) => toggle('ai_censor_enabled', v)}
            disabled={!isPro(plan)}
            requiredPlan="pro"
          />
          <ProtectionModule
            icon={<Link size={20} />}
            title="Фильтр ссылок"
            description="Автоматически удаляет внешние ссылки и инвайт-ссылки"
            enabled={s.link_filter_enabled}
            onChange={(v) => toggle('link_filter_enabled', v)}
          />
          <ProtectionModule
            icon={<AlertTriangle size={20} />}
            title="Стоп-слова"
            description="Блокировка сообщений с запрещёнными словами"
            enabled={s.stop_words_filter_enabled}
            onChange={(v) => toggle('stop_words_filter_enabled', v)}
            isLast
          />
        </SectionCard>

        {/* СЕКЦИЯ: Утилиты */}
        <p className="section-label" style={{ marginTop: 20 }}>Утилиты</p>
        <SectionCard>
          <ProtectionModule
            icon={<Trash2 size={20} />}
            title="Чистый чат"
            description="Удаляет системные уведомления о входе и выходе участников"
            enabled={s.clean_chat_enabled}
            onChange={(v) => toggle('clean_chat_enabled', v)}
            isLast
          />
        </SectionCard>

        {/* СЕКЦИЯ: Опасная зона */}
        <p className="section-label" style={{ marginTop: 20, color: 'rgba(255,69,58,0.55)' }}>
          Опасная зона
        </p>
        <div
          className="card"
          style={{ overflow: 'hidden', padding: '14px 16px' }}
        >
          <Button
            variant="danger"
            style={{ width: '100%' }}
            onClick={() => setShowDeleteModal(true)}
          >
            <Trash size={16} />
            Удалить чат из защиты
          </Button>
        </div>
      </div>

      {/* Confirm delete modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Удалить чат?"
      >
        <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.55)', marginBottom: 20, lineHeight: 1.55 }}>
          Бот перестанет защищать «{chat.title}». Все настройки будут сброшены. Это действие необратимо.
        </p>
        <div style={{ display: 'flex', gap: 10 }}>
          <Button variant="ghost" style={{ flex: 1 }} onClick={() => setShowDeleteModal(false)}>
            Отмена
          </Button>
          <Button variant="danger" style={{ flex: 1 }} loading={deleting} onClick={handleDelete}>
            Удалить
          </Button>
        </div>
      </Modal>
    </div>
  )
}
