import { useState, type FormEvent } from 'react'
import { ArrowRight, BarChart3, BriefcaseBusiness, CheckCircle2, Eye, EyeOff, Globe2, LockKeyhole, Mail, Route, Sparkles } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { appleAvailable } from '../lib/supabase'
import { useToast } from '../notifications/ToastProvider'

type DemoUser = { name: string; email: string }
const personas = [
  { name: 'Demo student', email: 'student@skillshift.test', initials: 'DS', blurb: 'Explore as a student' },
  { name: 'Demo career switcher', email: 'switcher@skillshift.test', initials: 'DC', blurb: 'Explore a career change' },
]
const features = [
  { icon: BriefcaseBusiness, text: 'Career readiness by skill' },
  { icon: BarChart3, text: 'Scenario and trend evidence' },
  { icon: Route, text: 'Verified learning pathways' },
  { icon: Globe2, text: 'Sustainable Development Goals' },
]

function GoogleMark() {
  return <svg width="19" height="19" viewBox="0 0 48 48" aria-hidden="true">
    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6C44.4 38.03 46.98 31.86 46.98 24.55z"/>
    <path fill="#FBBC05" d="M10.53 28.59A14.4 14.4 0 0 1 9.75 24c0-1.59.27-3.13.76-4.59l-7.98-6.2A23.9 23.9 0 0 0 0 24c0 3.87.93 7.52 2.56 10.78l7.97-6.19z"/>
    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.9-5.8l-7.73-6C30.03 37.6 27.26 38.5 24 38.5c-6.26 0-11.57-4.22-13.47-9.91l-7.97 6.19C6.51 42.62 14.62 48 24 48z"/>
  </svg>
}

export default function LoginPage({ onSignIn }: { onSignIn: (user: DemoUser) => void }) {
  const auth = useAuth()
  const { notify } = useToast()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  function showError(message: string) { setError(message); notify('error', message) }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true); setError(''); setSuccess('')
    try {
      if (mode === 'register') {
        const confirmationRequired = await auth.register(email.trim(), password)
        const message = confirmationRequired
          ? 'Check your inbox for a confirmation link, then return to sign in.'
          : 'Your account has been created. Welcome to SkillShift AI!'
        setSuccess(message); notify('success', message)
      } else {
        await auth.login(email.trim(), password)
        notify('success', 'Signed in successfully. Welcome back!')
      }
    } catch (reason) {
      showError(reason instanceof Error ? reason.message : 'Sign-in failed. Please try again.')
    } finally { setBusy(false) }
  }

  async function provider(name: 'google' | 'apple') {
    setBusy(true); setError(''); setSuccess('')
    try { await auth.signInWithProvider(name) }
    catch (reason) { showError(reason instanceof Error ? reason.message : 'Provider sign-in failed.') }
    finally { setBusy(false) }
  }

  async function forgotPassword() {
    if (!email.trim()) { showError('Enter your email address above before requesting a password reset.'); return }
    setBusy(true); setError(''); setSuccess('')
    try {
      await auth.resetPassword(email.trim())
      const message = 'If this email has an account, we will send password-reset instructions.'
      setSuccess(message); notify('success', message)
    } catch { showError('Unable to send a reset link. Please try again.') }
    finally { setBusy(false) }
  }

  const isRegister = mode === 'register'

  return <div className="login-split">
    <aside className="login-brand" aria-label="About SkillShift AI">
      <div className="login-brand-inner">
        <div className="brand-mark"><Sparkles size={24} aria-hidden="true" /> SkillShift <span>AI</span></div>
        <div className="login-brand-copy">
          <span className="login-eyebrow">FIND YOUR NEXT OPPORTUNITY</span>
          <h1>Your skills.<br /><span>Your next chapter.</span></h1>
          <p>Discover careers that match what you know, understand your skill gaps, and build a pathway forward.</p>
        </div>
        <ul className="login-feature-list">{features.map(({ icon: Icon, text }) =>
          <li key={text}><span className="login-feature-icon"><Icon size={18} aria-hidden="true" /></span>{text}</li>)}</ul>
        <div className="login-brand-foot"><CheckCircle2 size={16} aria-hidden="true" /> Built for future-ready careers</div>
      </div>
    </aside>

    <main className="login-panel">
      <div className="login-box">
        <div className="login-mobile-logo"><Sparkles size={19} aria-hidden="true" /> SkillShift AI</div>
        {auth.enabled ? <>
          <div className="login-heading">
            <span className="login-kicker">{isRegister ? 'JOIN SKILLSHIFT' : 'WELCOME BACK'}</span>
            <h2>{isRegister ? 'Create your account' : 'Sign in to SkillShift'}</h2>
            <p className="login-sub">{isRegister ? 'Save your career discoveries and pick up right where you left off.' : 'Your career journey continues here.'}</p>
          </div>

          <form onSubmit={(event) => void submit(event)} className="auth-form">
            <label htmlFor="auth-email" className="form-label">Email address</label>
            <div className="auth-input-wrap"><Mail size={18} aria-hidden="true" />
              <input id="auth-email" className="text-field" type="email" autoComplete="email" placeholder="you@example.com"
                value={email} onChange={event => setEmail(event.target.value)} required disabled={busy} />
            </div>
            <label htmlFor="auth-password" className="form-label">Password</label>
            <div className="auth-input-wrap"><LockKeyhole size={18} aria-hidden="true" />
              <input id="auth-password" className="text-field" type={showPassword ? 'text' : 'password'}
                autoComplete={isRegister ? 'new-password' : 'current-password'}
                minLength={isRegister ? 8 : undefined} placeholder={isRegister ? 'At least 8 characters' : 'Enter your password'}
                value={password} onChange={event => setPassword(event.target.value)} required disabled={busy} />
              <button type="button" className="auth-password-toggle" aria-label={showPassword ? 'Hide password' : 'Show password'}
                onClick={() => setShowPassword(value => !value)} disabled={busy}>
                {showPassword ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
              </button>
            </div>
            {isRegister && <p className="auth-hint">Use at least eight characters for your password.</p>}
            <button type="submit" className="primary auth-submit" disabled={busy}>
              {busy ? 'Please wait…' : isRegister ? 'Create account' : 'Sign in'}
              {!busy && <ArrowRight size={18} aria-hidden="true" />}
            </button>
          </form>
          {error && <p className="auth-feedback auth-feedback--error" role="alert">{error}</p>}
          {success && <p className="auth-feedback auth-feedback--success" role="status">{success}</p>}
          <div className="auth-inline">
            <button type="button" className="link-btn" onClick={() => {
              setMode(value => value === 'login' ? 'register' : 'login'); setError(''); setSuccess(''); setPassword('')
            }}>{isRegister ? 'Already have an account? Sign in' : 'New here? Create an account'}</button>
            {!isRegister && <button type="button" className="link-btn" disabled={busy} onClick={() => void forgotPassword()}>Forgot password?</button>}
          </div>
          <div className="auth-divider"><span>or continue with</span></div>
          <div className="auth-social">
            <button type="button" disabled={busy} onClick={() => void provider('google')}><GoogleMark /> Continue with Google</button>
            {appleAvailable && <button type="button" disabled={busy} onClick={() => void provider('apple')}>Continue with Apple</button>}
          </div>
        </> : <div className="login-heading">
          <span className="login-kicker">WELCOME</span>
          <h2>Explore SkillShift AI</h2>
          <p className="login-sub">Accounts are not configured. You can explore with a guest demo.</p>
        </div>}

        <div className="guest-section">
          <div className="auth-divider"><span>Or explore without an account</span></div>
          <div className="persona-grid">{personas.map(persona =>
            <button className="persona" type="button" key={persona.email} onClick={() => onSignIn({ name: persona.name, email: persona.email })}>
              <span className="avatar large">{persona.initials}</span>
              <span className="persona-text"><strong>{persona.name}</strong><small>{persona.blurb}</small></span>
              <ArrowRight size={17} aria-hidden="true" />
            </button>)}</div>
          <p className="login-note"><LockKeyhole size={13} aria-hidden="true" /> Demo profiles are synthetic. Sign in to save your progress.</p>
        </div>
      </div>
    </main>
  </div>
}
