import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Session, User } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'

type AuthState = {
  user: User | null
  session: Session | null
  loading: boolean
  enabled: boolean
  recovery: boolean
  updatePassword: (password: string) => Promise<void>
  updateDisplayName: (name: string) => Promise<void>
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<boolean>
  signInWithProvider: (provider: 'google' | 'apple') => Promise<void>
  resetPassword: (email: string) => Promise<void>
  signOut: () => Promise<void>
}
const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(Boolean(supabase))
  const [recovery, setRecovery] = useState(false)

  useEffect(() => {
    if (!supabase) return
    let alive = true
    // Session data is for UI rendering; DB ownership is enforced by RLS.
    void supabase.auth.getSession().then(({ data, error }) => {
      if (!alive) return
      if (error) setSession(null)
      else setSession(data.session)
      setLoading(false)
    }).catch(() => { if (alive) { setSession(null); setLoading(false) } })
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, nextSession) => {
      if (event === 'PASSWORD_RECOVERY') setRecovery(true)
      if (alive) { setSession(nextSession); setLoading(false) }
    })
    return () => { alive = false; subscription.unsubscribe() }
  }, [])

  const auth = useMemo<AuthState>(() => ({
    user: session?.user ?? null,
    session,
    loading,
    enabled: Boolean(supabase),
    recovery,
    updatePassword: async (password) => {
      if (!supabase) throw new Error('Accounts are not configured')
      const { error } = await supabase.auth.updateUser({ password })
      if (error) throw error
      setRecovery(false)
    },
    updateDisplayName: async (name) => {
      if (!supabase) throw new Error('Accounts are not configured')
      const { error } = await supabase.auth.updateUser({ data: { display_name: name.trim().slice(0, 100) } })
      if (error) throw error
    },
    login: async (email, password) => {
      if (!supabase) throw new Error('Accounts are not configured')
      const { error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) throw error
    },
    register: async (email, password) => {
      if (!supabase) throw new Error('Accounts are not configured')
      const { data, error } = await supabase.auth.signUp({
        email, password, options: { emailRedirectTo: window.location.origin },
      })
      if (error) throw error
      return data.session === null // Email confirmation is usually required.
    },
    signInWithProvider: async (provider) => {
      if (!supabase) throw new Error('Accounts are not configured')
      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: { redirectTo: window.location.origin },
      })
      if (error) throw error
    },
    resetPassword: async (email) => {
      if (!supabase) throw new Error('Accounts are not configured')
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/?recovery=1`,
      })
      if (error) throw error
    },
    signOut: async () => {
      if (!supabase) return
      const { error } = await supabase.auth.signOut()
      if (error) throw error
    },
  }), [session, loading, recovery])

  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
