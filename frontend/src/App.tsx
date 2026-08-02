import React, { useEffect } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { ToastProvider } from './components/ui/Toast'
import { ForceSubModal } from './components/ForceSubModal'
import { Home } from './pages/Home'
import { ChatSettings } from './pages/ChatSettings'
import { Subscription } from './pages/Subscription'
import { Blacklist } from './pages/Blacklist'
import { Profile } from './pages/Profile'
import { Admin } from './pages/Admin'
import { useTelegram } from './hooks/useTelegram'
import { useStore } from './store'
import { getMe } from './api/client'

export default function App() {
  useTelegram()
  const location = useLocation()
  const { setUser, setInitialized, isInitialized } = useStore()

  // Hide navbar inside chat settings (full-page view)
  const hideNavbar = location.pathname.startsWith('/chat/')

  useEffect(() => {
    getMe()
      .then((user: ReturnType<typeof useStore.getState>['user']) => {
        setUser(user)
        setInitialized(true)
      })
      .catch(() => setInitialized(true))
  }, [])

  if (!isInitialized) {
    return (
      <div
        style={{
          height: '100dvh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#0A0A0A',
        }}
      >
        <svg
          width="26"
          height="26"
          viewBox="0 0 24 24"
          fill="none"
          stroke="rgba(255,255,255,0.35)"
          strokeWidth="2"
          style={{ animation: 'spin 0.9s linear infinite' }}
        >
          <style>{`@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>
          <circle cx="12" cy="12" r="9" strokeDasharray="28" strokeDashoffset="8" strokeLinecap="round" />
        </svg>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100dvh', background: '#0A0A0A' }}>
      <ToastProvider />
      <ForceSubModal />
      <Routes>
        <Route path="/"              element={<Home />} />
        <Route path="/chat/:id"      element={<ChatSettings />} />
        <Route path="/subscription"  element={<Subscription />} />
        <Route path="/blacklist"     element={<Blacklist />} />
        <Route path="/profile"       element={<Profile />} />
        <Route path="/admin"         element={<Admin />} />
      </Routes>
      {!hideNavbar && <Navbar />}
    </div>
  )
}
