import { createClient } from '@supabase/supabase-js'

const url = (import.meta.env.VITE_SUPABASE_URL ?? '').trim()
const key = (import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? '').trim()

// Guest demo still works when credentials are not configured.
export const supabase = url && key ? createClient(url, key, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, flowType: 'pkce' },
}) : null

export const appleAvailable = import.meta.env.VITE_ENABLE_APPLE_AUTH === 'true'
