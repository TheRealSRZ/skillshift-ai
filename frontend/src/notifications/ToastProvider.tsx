import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react'

type Tone = 'success' | 'error' | 'info'
type Toast = { id: number; tone: Tone; message: string }
type ToastContextValue = { notify: (tone: Tone, message: string) => void }
const ToastContext = createContext<ToastContextValue | null>(null)
let sequence = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([])
  const notify = useCallback((tone: Tone, message: string) => {
    const toast = { id: ++sequence, tone, message }
    // Bound the stack, so repeated errors do not fill the whole screen.
    setItems(old => [...old.slice(-2), toast])
  }, [])
  const dismiss = useCallback((id: number) => setItems(old => old.filter(item => item.id !== id)), [])
  const context = useMemo(() => ({ notify }), [notify])

  return <ToastContext.Provider value={context}>
    {children}
    <div className="toast-stack" aria-label="Notifications">
      {items.map(item => <ToastItem key={item.id} item={item} onDismiss={dismiss} />)}
    </div>
  </ToastContext.Provider>
}

function ToastItem({ item, onDismiss }: { item: Toast; onDismiss: (id: number) => void }) {
  useEffect(() => {
    const timeout = window.setTimeout(() => onDismiss(item.id), item.tone === 'error' ? 8500 : 5000)
    return () => window.clearTimeout(timeout)
  }, [item.id, item.tone, onDismiss])
  const Icon = item.tone === 'success' ? CheckCircle2 : item.tone === 'error' ? AlertCircle : Info
  return <div className={`toast toast--${item.tone}`} role={item.tone === 'error' ? 'alert' : 'status'}>
    <Icon size={22} aria-hidden="true" />
    <div className="toast-text"><strong>{item.tone === 'success' ? 'Success' : item.tone === 'error' ? 'Action needed' : 'Notice'}</strong><p>{item.message}</p></div>
    <button type="button" aria-label="Dismiss notification" onClick={() => onDismiss(item.id)}><X size={18} aria-hidden="true" /></button>
  </div>
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used inside ToastProvider')
  return context
}
