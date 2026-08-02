import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useStore } from '../store'
import { useApi, useMutation } from '../hooks/useApi'
import {
  getAdminStats, getAdminUsers, grantPlan,
  createPromo, listPromos,
  createKeys, listKeys,
  getForceSub, updateForceSub,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { Toggle } from '../components/ui/Toggle'
import { showToast } from '../components/ui/Toast'

type AdminTab = 'stats' | 'users' | 'promo' | 'keys' | 'settings'

const TABS: { id: AdminTab; label: string }[] = [
  { id: 'stats',    label: 'Статистика' },
  { id: 'users',    label: 'Пользователи' },
  { id: 'promo',    label: 'Промокоды' },
  { id: 'keys',     label: 'Ключи' },
  { id: 'settings', label: 'Настройки' },
]

const PLANS = ['lite', 'pro', 'corporate']
const PLAN_LABELS: Record<string, string> = { none: 'Нет', lite: 'Лайт', pro: 'Про', corporate: 'Корп' }

// ─── Stats Tab ────────────────────────────────────────────────────────────────
function StatsTab() {
  const { data, loading } = useApi(getAdminStats, [])

  if (loading) return <div className="skeleton" style={{ height: 200 }} />
  if (!data) return null

  const StatCard = ({ label, value }: { label: string; value: string | number }) => (
    <div className="card" style={{ padding: '16px', textAlign: 'center' }}>
      <p style={{ fontSize: 26, fontWeight: 700, marginBottom: 4 }}>{value}</p>
      <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.40)' }}>{label}</p>
    </div>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <StatCard label="Пользователей" value={data.total_users} />
        <StatCard label="Чатов" value={data.total_chats} />
        <StatCard label="В ЧС" value={data.blacklist_count} />
        <StatCard
          label="Активных подписок"
          value={Object.values(data.active_subscriptions as Record<string, number>).reduce((a: number, b: number) => a + b, 0)}
        />
      </div>
      {Object.entries(data.active_subscriptions as Record<string, number>).length > 0 && (
        <div className="card" style={{ padding: '14px 16px' }}>
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.40)', marginBottom: 10 }}>
            Разбивка по тарифам
          </p>
          {Object.entries(data.active_subscriptions as Record<string, number>).map(([plan, count]) => (
            <div key={plan} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <Badge plan={plan}>{PLAN_LABELS[plan] ?? plan}</Badge>
              <span style={{ fontSize: 14, fontWeight: 600 }}>{count}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Users Tab ────────────────────────────────────────────────────────────────
function UsersTab() {
  const [search, setSearch] = useState('')
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [grantForm, setGrantForm] = useState({ plan: 'lite', days: '30' })
  const [granting, setGranting] = useState(false)

  const { data, loading, refetch } = useApi(
    () => getAdminUsers(1, search),
    [search]
  )

  const handleGrant = async (tgId: number) => {
    setGranting(true)
    try {
      await grantPlan(tgId, grantForm.plan, parseInt(grantForm.days, 10))
      showToast('Тариф выдан', 'success')
      setExpandedId(null)
      refetch()
    } catch {
      showToast('Ошибка', 'error')
    } finally {
      setGranting(false)
    }
  }

  const users = (data as { items: unknown[] } | null)?.items ?? []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <Input
        placeholder="Поиск по имени или @username..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      {loading ? (
        <div className="skeleton" style={{ height: 200 }} />
      ) : (
        <div className="card" style={{ overflow: 'hidden' }}>
          {(users as Array<{ tg_id: number; first_name: string; username?: string; plan: string; subscription_end?: string }>).map((u, i, arr) => (
            <div key={u.tg_id}>
              <button
                onClick={() => setExpandedId(expandedId === u.tg_id ? null : u.tg_id)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  borderBottom: i < arr.length - 1 || expandedId === u.tg_id ? '1px solid rgba(255,255,255,0.06)' : 'none',
                }}
              >
                <div style={{ textAlign: 'left' }}>
                  <p style={{ fontSize: 14, fontWeight: 500, color: '#FFFFFF' }}>{u.first_name}</p>
                  <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)' }}>
                    {u.username ? `@${u.username}` : `ID: ${u.tg_id}`}
                  </p>
                </div>
                <Badge plan={u.plan}>{PLAN_LABELS[u.plan] ?? u.plan}</Badge>
              </button>

              {expandedId === u.tg_id && (
                <div style={{ padding: '12px 16px', background: 'rgba(255,255,255,0.02)', borderBottom: i < arr.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none' }}>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                    <select
                      value={grantForm.plan}
                      onChange={(e) => setGrantForm((f) => ({ ...f, plan: e.target.value }))}
                      style={{
                        flex: 1, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.10)',
                        borderRadius: 10, padding: '8px 12px', color: '#FFFFFF', fontSize: 14, outline: 'none',
                      }}
                    >
                      {PLANS.map((p) => <option key={p} value={p} style={{ background: '#1C1C1E' }}>{PLAN_LABELS[p]}</option>)}
                    </select>
                    <input
                      type="number"
                      value={grantForm.days}
                      onChange={(e) => setGrantForm((f) => ({ ...f, days: e.target.value }))}
                      placeholder="Дней"
                      style={{
                        width: 80, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.10)',
                        borderRadius: 10, padding: '8px 12px', color: '#FFFFFF', fontSize: 14, outline: 'none',
                      }}
                    />
                  </div>
                  <Button
                    size="sm"
                    loading={granting}
                    onClick={() => handleGrant(u.tg_id)}
                    style={{ width: '100%' }}
                  >
                    Выдать тариф
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Promo Tab ────────────────────────────────────────────────────────────────
function PromoTab() {
  const [form, setForm] = useState({ code: '', free_days: '', discount_pct: '', uses_left: '-1' })
  const [creating, setCreating] = useState(false)
  const { data, loading, refetch } = useApi(listPromos, [])

  const handleCreate = async () => {
    if (!form.code.trim()) { showToast('Введите код', 'error'); return }
    setCreating(true)
    try {
      await createPromo({
        code: form.code.toUpperCase(),
        free_days: parseInt(form.free_days || '0', 10),
        discount_pct: parseInt(form.discount_pct || '0', 10),
        uses_left: parseInt(form.uses_left || '-1', 10),
      })
      showToast('Промокод создан', 'success')
      setForm({ code: '', free_days: '', discount_pct: '', uses_left: '-1' })
      refetch()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      showToast(err?.response?.data?.detail ?? 'Ошибка', 'error')
    } finally {
      setCreating(false)
    }
  }

  const promos = (data as Array<{ id: number; code: string; free_days: number; discount_pct: number; uses_left: number }> | null) ?? []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className="card" style={{ padding: 16 }}>
        <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Создать промокод</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Input label="Код" placeholder="WARDEUM2024" value={form.code} onChange={(e) => setForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
            <Input label="Дней" placeholder="7" type="number" value={form.free_days} onChange={(e) => setForm((f) => ({ ...f, free_days: e.target.value }))} />
            <Input label="Скидка %" placeholder="0" type="number" value={form.discount_pct} onChange={(e) => setForm((f) => ({ ...f, discount_pct: e.target.value }))} />
            <Input label="Лимит" placeholder="-1" type="number" value={form.uses_left} onChange={(e) => setForm((f) => ({ ...f, uses_left: e.target.value }))} />
          </div>
          <Button loading={creating} onClick={handleCreate} style={{ width: '100%' }}>Создать</Button>
        </div>
      </div>

      {loading ? <div className="skeleton" style={{ height: 100 }} /> : promos.length > 0 && (
        <div className="card" style={{ overflow: 'hidden' }}>
          {promos.map((p, i) => (
            <div key={p.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '11px 16px', borderBottom: i < promos.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none' }}>
              <div>
                <p style={{ fontSize: 13, fontWeight: 600, fontFamily: 'monospace' }}>{p.code}</p>
                <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginTop: 2 }}>+{p.free_days}д · {p.discount_pct}% · лимит: {p.uses_left === -1 ? '∞' : p.uses_left}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Keys Tab ─────────────────────────────────────────────────────────────────
function KeysTab() {
  const [form, setForm] = useState({ plan: 'lite', duration_days: '30', count: '1' })
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState<string[]>([])
  const { data, loading, refetch } = useApi(listKeys, [])

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const result = await createKeys({
        plan: form.plan,
        duration_days: parseInt(form.duration_days, 10),
        count: parseInt(form.count, 10),
      }) as { keys: string[] }
      setGenerated(result.keys)
      showToast(`Создано ${result.keys.length} ключей`, 'success')
      refetch()
    } catch {
      showToast('Ошибка генерации', 'error')
    } finally {
      setGenerating(false)
    }
  }

  const keys = (data as Array<{ key: string; plan: string; duration_days: number; used: boolean }> | null) ?? []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className="card" style={{ padding: 16 }}>
        <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Генерировать ключи</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <label style={{ fontSize: 12, color: 'rgba(255,255,255,0.40)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Тариф</label>
              <select
                value={form.plan}
                onChange={(e) => setForm((f) => ({ ...f, plan: e.target.value }))}
                style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.10)', borderRadius: 10, padding: '11px 10px', color: '#FFFFFF', fontSize: 14, outline: 'none' }}
              >
                {PLANS.map((p) => <option key={p} value={p} style={{ background: '#1C1C1E' }}>{PLAN_LABELS[p]}</option>)}
              </select>
            </div>
            <Input label="Дней" placeholder="30" type="number" value={form.duration_days} onChange={(e) => setForm((f) => ({ ...f, duration_days: e.target.value }))} />
            <Input label="Кол-во" placeholder="1" type="number" value={form.count} onChange={(e) => setForm((f) => ({ ...f, count: e.target.value }))} />
          </div>
          <Button loading={generating} onClick={handleGenerate} style={{ width: '100%' }}>Сгенерировать</Button>
        </div>

        {generated.length > 0 && (
          <div style={{ marginTop: 14, background: 'rgba(255,255,255,0.04)', borderRadius: 10, padding: 12 }}>
            {generated.map((k) => (
              <p key={k} style={{ fontFamily: 'monospace', fontSize: 13, letterSpacing: '0.05em', padding: '3px 0', color: 'rgba(255,255,255,0.85)' }}>{k}</p>
            ))}
            <button
              onClick={() => navigator.clipboard.writeText(generated.join('\n')).then(() => showToast('Скопированы все ключи'))}
              style={{ marginTop: 8, background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, color: 'rgba(255,255,255,0.45)' }}
            >
              Скопировать все
            </button>
          </div>
        )}
      </div>

      {!loading && keys.length > 0 && (
        <div className="card" style={{ overflow: 'hidden' }}>
          {keys.slice(0, 20).map((k, i) => (
            <div key={k.key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', borderBottom: i < Math.min(keys.length, 20) - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none', opacity: k.used ? 0.4 : 1 }}>
              <p style={{ fontFamily: 'monospace', fontSize: 12, letterSpacing: '0.04em' }}>{k.key}</p>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Badge plan={k.plan} />
                {k.used && <Badge variant="danger" style={{ fontSize: 10 }}>Использован</Badge>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Settings Tab ─────────────────────────────────────────────────────────────
function SettingsTab() {
  const [forceSub, setForceSub] = useState(false)
  const [channelId, setChannelId] = useState('')
  const [saving, setSaving] = useState(false)

  useApi(
    () =>
      getForceSub().then((d: { enabled: boolean; channel_id?: number | null }) => {
        setForceSub(d.enabled)
        setChannelId(d.channel_id ? String(d.channel_id) : '')
        return d
      }),
    []
  )

  const save = async () => {
    setSaving(true)
    try {
      await updateForceSub({
        enabled: forceSub,
        channel_id: channelId ? parseInt(channelId, 10) : null,
      })
      showToast('Сохранено', 'success')
    } catch {
      showToast('Ошибка сохранения', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div className="card" style={{ padding: '16px 18px' }}>
        <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 16 }}>Обязательная подписка</p>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div>
            <p style={{ fontSize: 15, fontWeight: 500 }}>Включить</p>
            <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.40)', marginTop: 2 }}>Пользователи должны подписаться на канал</p>
          </div>
          <Toggle checked={forceSub} onChange={setForceSub} />
        </div>
        {forceSub && (
          <Input
            label="ID канала"
            placeholder="2590000962 (без -100 в начале)"
            value={channelId}
            onChange={(e) => setChannelId(e.target.value)}
            hint="Введите числовую часть ID канала без префикса -100"
          />
        )}
        <Button loading={saving} onClick={save} style={{ width: '100%', marginTop: 16 }}>
          Сохранить
        </Button>
      </div>
    </div>
  )
}

// ─── Main Admin page ──────────────────────────────────────────────────────────
export function Admin() {
  const { user } = useStore()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<AdminTab>('stats')

  if (!user?.is_admin) {
    navigate('/', { replace: true })
    return null
  }

  return (
    <div className="page fade-in" style={{ paddingTop: 20 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 20 }}>
        Администрирование
      </h1>

      {/* Tab bar */}
      <div
        style={{
          display: 'flex',
          gap: 0,
          background: 'rgba(255,255,255,0.05)',
          borderRadius: 12,
          padding: 4,
          marginBottom: 20,
          overflowX: 'auto',
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              flex: '1 0 auto',
              padding: '7px 10px',
              borderRadius: 9,
              border: 'none',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 500,
              whiteSpace: 'nowrap',
              background: activeTab === tab.id ? '#FFFFFF' : 'transparent',
              color: activeTab === tab.id ? '#0A0A0A' : 'rgba(255,255,255,0.45)',
              transition: 'background 0.2s, color 0.2s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'stats'    && <StatsTab />}
      {activeTab === 'users'    && <UsersTab />}
      {activeTab === 'promo'    && <PromoTab />}
      {activeTab === 'keys'     && <KeysTab />}
      {activeTab === 'settings' && <SettingsTab />}
    </div>
  )
}
