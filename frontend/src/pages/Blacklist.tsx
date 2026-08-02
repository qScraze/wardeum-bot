import React, { useState } from 'react'
import { ShieldOff, Trash2 } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import { getBlacklist, removeFromBlacklist } from '../api/client'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Modal } from '../components/ui/Modal'
import { showToast } from '../components/ui/Toast'

interface BlacklistEntry {
  id: number
  tg_id: number
  username?: string
  first_name?: string
  reason: string
  banned_by: number
  is_global: boolean
  created_at: string
}

function Initials({ name }: { name?: string }) {
  const letters = (name ?? '?').slice(0, 2).toUpperCase()
  const hue = (name ?? '').split('').reduce((a, c) => a + c.charCodeAt(0), 0) % 360
  return (
    <div
      style={{
        width: 40,
        height: 40,
        borderRadius: '50%',
        background: `hsl(${hue},20%,24%)`,
        border: '1px solid rgba(255,255,255,0.08)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 13,
        fontWeight: 600,
        color: `hsl(${hue},50%,70%)`,
        flexShrink: 0,
      }}
    >
      {letters}
    </div>
  )
}

export function Blacklist() {
  const [page, setPage] = useState(1)
  const [items, setItems] = useState<BlacklistEntry[]>([])
  const [total, setTotal] = useState(0)
  const [selected, setSelected] = useState<BlacklistEntry | null>(null)
  const [unbanning, setUnbanning] = useState(false)

  const { loading, refetch } = useApi(
    () =>
      getBlacklist(1, 50).then((data: { items: BlacklistEntry[]; total: number }) => {
        setItems(data.items)
        setTotal(data.total)
        return data
      }),
    []
  )

  const handleUnban = async () => {
    if (!selected) return
    setUnbanning(true)
    try {
      await removeFromBlacklist(selected.tg_id)
      setItems((prev) => prev.filter((e) => e.tg_id !== selected.tg_id))
      setTotal((t) => t - 1)
      showToast('Пользователь разбанен', 'success')
      setSelected(null)
    } catch {
      showToast('Ошибка — глобальные записи может удалить только администратор', 'error')
    } finally {
      setUnbanning(false)
    }
  }

  const formatDate = (d: string) =>
    new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' })

  return (
    <div className="page fade-in" style={{ paddingTop: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }}>Чёрный список</h1>
        {total > 0 && (
          <span
            style={{
              background: 'rgba(255,255,255,0.08)',
              border: '1px solid rgba(255,255,255,0.10)',
              borderRadius: 20,
              padding: '2px 8px',
              fontSize: 12,
              color: 'rgba(255,255,255,0.50)',
            }}
          >
            {total}
          </span>
        )}
      </div>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton" style={{ height: 66, borderRadius: 14 }} />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '50vh',
            gap: 14,
          }}
        >
          <ShieldOff size={52} color="rgba(255,255,255,0.10)" />
          <p style={{ fontSize: 15, fontWeight: 500, color: 'rgba(255,255,255,0.35)' }}>
            Список пуст
          </p>
        </div>
      ) : (
        <div className="card" style={{ overflow: 'hidden' }}>
          {items.map((entry, i) => (
            <div
              key={entry.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 16px',
                borderBottom: i < items.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none',
              }}
            >
              <Initials name={entry.first_name ?? entry.username} />

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                  <span style={{ fontSize: 14, fontWeight: 600, color: '#FFFFFF' }}>
                    {entry.first_name ?? entry.username ?? `ID: ${entry.tg_id}`}
                  </span>
                  {entry.is_global && <Badge variant="global">Глобальный</Badge>}
                </div>
                <p
                  style={{
                    fontSize: 12,
                    color: 'rgba(255,255,255,0.38)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {entry.reason} · {formatDate(entry.created_at)}
                </p>
              </div>

              {!entry.is_global && (
                <button
                  onClick={() => setSelected(entry)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'rgba(255,69,58,0.6)',
                    display: 'flex',
                    padding: 6,
                    borderRadius: 8,
                  }}
                >
                  <Trash2 size={16} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Confirm unban modal */}
      <Modal
        isOpen={!!selected}
        onClose={() => setSelected(null)}
        title="Разбанить пользователя?"
      >
        {selected && (
          <>
            <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.55)', marginBottom: 20, lineHeight: 1.55 }}>
              Пользователь «{selected.first_name ?? selected.username ?? selected.tg_id}» будет разбанен
              в ваших чатах. Причина бана: {selected.reason}.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <Button variant="ghost" style={{ flex: 1 }} onClick={() => setSelected(null)}>
                Отмена
              </Button>
              <Button style={{ flex: 1 }} loading={unbanning} onClick={handleUnban}>
                Разбанить
              </Button>
            </div>
          </>
        )}
      </Modal>
    </div>
  )
}
