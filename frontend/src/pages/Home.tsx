import React, { useState } from 'react'
import { Plus, Shield } from 'lucide-react'
import { useStore } from '../store'
import { useApi } from '../hooks/useApi'
import { getChats, addChat } from '../api/client'
import { ChatCard } from '../components/ChatCard'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { showToast } from '../components/ui/Toast'

export function Home() {
  const { chats, setChats, addChat: storeAddChat } = useStore()
  const [showAddModal, setShowAddModal] = useState(false)
  const [tgId, setTgId] = useState('')
  const [chatTitle, setChatTitle] = useState('')
  const [adding, setAdding] = useState(false)
  const [fieldError, setFieldError] = useState('')

  const { loading, refetch } = useApi(
    () =>
      getChats().then((data: typeof chats) => {
        setChats(data)
        return data
      }),
    []
  )

  const handleAdd = async () => {
    setFieldError('')
    const id = parseInt(tgId.trim(), 10)
    if (!tgId.trim() || isNaN(id)) {
      setFieldError('Введите корректный ID чата')
      return
    }
    if (!chatTitle.trim()) {
      setFieldError('Введите название чата')
      return
    }
    setAdding(true)
    try {
      const chat = await addChat({ tg_id: id, title: chatTitle.trim() })
      storeAddChat(chat)
      setShowAddModal(false)
      setTgId('')
      setChatTitle('')
      showToast('Чат добавлен', 'success')
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setFieldError(err?.response?.data?.detail ?? 'Ошибка добавления')
    } finally {
      setAdding(false)
    }
  }

  return (
    <div className="page fade-in" style={{ paddingTop: 20 }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }}>Чаты</h1>
      </div>

      {/* List */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton" style={{ height: 72, borderRadius: 16 }} />
          ))}
        </div>
      ) : chats.length === 0 ? (
        // Empty state
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '55vh',
            gap: 16,
            textAlign: 'center',
          }}
        >
          <Shield size={64} color="rgba(255,255,255,0.10)" />
          <div>
            <p style={{ fontSize: 17, fontWeight: 600, marginBottom: 6 }}>Нет защищённых чатов</p>
            <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.40)', lineHeight: 1.5 }}>
              Добавьте первый чат, чтобы начать защиту
            </p>
          </div>
          <Button onClick={() => setShowAddModal(true)}>Добавить чат</Button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {chats.map((chat) => (
              <ChatCard key={chat.id} chat={chat} />
            ))}
          </div>
          <Button
            variant="ghost"
            onClick={() => setShowAddModal(true)}
            style={{ width: '100%', marginTop: 8 }}
          >
            <Plus size={16} />
            Добавить ещё чат
          </Button>
        </div>
      )}

      {/* Add chat modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => { setShowAddModal(false); setFieldError('') }}
        title="Добавить чат"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Input
            label="ID чата"
            placeholder="-1001234567890"
            value={tgId}
            onChange={(e) => setTgId(e.target.value)}
            hint="Отрицательный числовой ID группы или супергруппы"
            type="number"
          />
          <Input
            label="Название"
            placeholder="Мой чат"
            value={chatTitle}
            onChange={(e) => setChatTitle(e.target.value)}
            error={fieldError}
          />
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.30)', lineHeight: 1.5 }}>
            Сначала добавьте бота в чат и назначьте ему права администратора, затем вставьте ID чата сюда.
          </p>
          <Button
            loading={adding}
            onClick={handleAdd}
            style={{ width: '100%', marginTop: 4 }}
          >
            Добавить
          </Button>
        </div>
      </Modal>
    </div>
  )
}
