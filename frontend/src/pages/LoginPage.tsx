import { useEffect, useRef, useState, type CSSProperties, type FormEvent, type MouseEvent as ReactMouseEvent } from 'react'
import { ArrowRight, BarChart3, BriefcaseBusiness, Eye, EyeOff, Globe2, LockKeyhole, Mail, Route, Sparkles } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { appleAvailable } from '../lib/supabase'
import { useToast } from '../notifications/ToastProvider'
import type { Career } from '../types'

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

const INTRO_KEY = 'skillshift-intro-seen'
const BRAND_WORD = 'SkillShift AI'
// Intro stages: 0 green screen, 1 logo, 2 content opens, 3 content fades in, 4 career bar, 5 slide left, 6 login shown.
const STAGE_CLASSES = ['lg-pop', 'lg-open', 'lg-go', 'lg-match-on', 'lg-split', 'lg-show']
const STAGE_TIMES: [number, number][] = [[700, 1], [2100, 2], [2700, 3], [3900, 4], [9300, 5], [9800, 6]]

function wantsReducedMotion(): boolean {
  try {
    const saved = localStorage.getItem('skillshift-reduce-motion')
    if (saved === 'on') return true
    if (saved === 'off') return false
  } catch { /* storage may be unavailable */ }
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function introAlreadySeen(): boolean {
  try { return sessionStorage.getItem(INTRO_KEY) === '1' } catch { return false }
}

const delay = (seconds: number) => ({ '--d': `${seconds}s` }) as CSSProperties

function GoogleMark() {
  return <svg width="19" height="19" viewBox="0 0 48 48" aria-hidden="true">
    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6C44.4 38.03 46.98 31.86 46.98 24.55z"/>
    <path fill="#FBBC05" d="M10.53 28.59A14.4 14.4 0 0 1 9.75 24c0-1.59.27-3.13.76-4.59l-7.98-6.2A23.9 23.9 0 0 0 0 24c0 3.87.93 7.52 2.56 10.78l7.97-6.19z"/>
    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.9-5.8l-7.73-6C30.03 37.6 27.26 38.5 24 38.5c-6.26 0-11.57-4.22-13.47-9.91l-7.97 6.19C6.51 42.62 14.62 48 24 48z"/>
  </svg>
}

export default function LoginPage({ onSignIn, careers = [] }: { onSignIn: (user: DemoUser) => void; careers?: Career[] }) {
  const auth = useAuth()
  const { notify } = useToast()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Intro animation: plays once per browser session, never with reduce motion.
  const [reduced] = useState(wantsReducedMotion)
  const [phase, setPhase] = useState(() => (reduced || introAlreadySeen() ? 6 : 0))
  const timers = useRef<number[]>([])
  const [tick, setTick] = useState(0)
  const pointer = useRef({ x: -400, y: -400, want: 0, boost: 0 })
  const drop1 = useRef<HTMLSpanElement>(null)
  const drop2 = useRef<HTMLSpanElement>(null)
  const drop3 = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (phase >= 6) return
    timers.current = STAGE_TIMES.map(([ms, next]) => window.setTimeout(() => setPhase(next), ms))
    return () => timers.current.forEach(id => window.clearTimeout(id))
  }, [])

  useEffect(() => {
    if (phase >= 6) { try { sessionStorage.setItem(INTRO_KEY, '1') } catch { /* optional */ } }
  }, [phase])

  function skipIntro() {
    timers.current.forEach(id => window.clearTimeout(id))
    setPhase(6)
  }

  // The career bar steps through every career in the catalog, one per tick.
  const matchOn = phase >= 4
  useEffect(() => {
    if (!matchOn || careers.length === 0 || reduced) return
    const id = window.setInterval(() => setTick(t => t + 1), 900)
    return () => window.clearInterval(id)
  }, [matchOn, careers.length, reduced])

  // Lime liquid drops that trail the mouse over the green panel.
  useEffect(() => {
    if (reduced) return
    const drops = [
      { el: drop1.current, r: 85, k: 0.12, x: -400, y: -400, s: 0 },
      { el: drop2.current, r: 60, k: 0.075, x: -400, y: -400, s: 0 },
      { el: drop3.current, r: 40, k: 0.05, x: -400, y: -400, s: 0 },
    ]
    let frame = 0
    const loop = () => {
      const p = pointer.current
      p.boost *= 0.93
      for (const d of drops) {
        if (!d.el) continue
        d.x += (p.x - d.r - d.x) * d.k
        d.y += (p.y - d.r - d.y) * d.k
        d.s += (p.want * (1 + p.boost * 0.9) - d.s) * 0.14
        d.el.style.transform = `translate(${d.x.toFixed(1)}px, ${d.y.toFixed(1)}px) scale(${d.s.toFixed(3)})`
      }
      frame = requestAnimationFrame(loop)
    }
    frame = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(frame)
  }, [reduced])

  function onBrandMove(event: ReactMouseEvent<HTMLElement>) {
    const box = event.currentTarget.getBoundingClientRect()
    pointer.current.x = event.clientX - box.left
    pointer.current.y = event.clientY - box.top
    pointer.current.want = 1
  }

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
  const pageClass = ['lg-page', ...STAGE_CLASSES.slice(0, phase)].join(' ')
  const total = careers.length
  const current = total > 0 ? tick % total : 0
  const careerName = total > 0 ? careers[current].title : ''
  const letters = BRAND_WORD.split('').map((ch, i) =>
    <span key={i} className={i >= 11 ? 'lg-ch lg-ai' : 'lg-ch'} style={{ '--n': i } as CSSProperties}>{ch === ' ' ? '\u00a0' : ch}</span>)

  return <div className={pageClass}>
    <svg className="lg-defs" width="0" height="0" aria-hidden="true"><defs>
      <filter id="lg-goo"><feGaussianBlur in="SourceGraphic" stdDeviation="14" result="blur" />
        <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9" /></filter>
    </defs></svg>

    {phase < 6 && <button type="button" className="lg-skip" onClick={skipIntro}>Skip intro <ArrowRight size={15} aria-hidden="true" /></button>}

    <aside className="lg-brand" aria-label="About SkillShift AI"
      onMouseMove={onBrandMove}
      onMouseLeave={() => { pointer.current.want = 0 }}
      onMouseDown={() => { pointer.current.boost = 1 }}>
      <div className="lg-lava" aria-hidden="true">
        <div className="lg-layer lg-layer-a"><span className="lg-blob lg-b1" /><span className="lg-blob lg-b3" /><span className="lg-blob lg-b5" /></div>
        <div className="lg-layer lg-layer-b">
          <span className="lg-blob lg-b2" /><span className="lg-blob lg-b4" /><span className="lg-blob lg-b6" />
          {!reduced && <>
            <span className="lg-blob lg-drop" ref={drop1} style={{ width: 170, height: 170 }} />
            <span className="lg-blob lg-drop" ref={drop2} style={{ width: 120, height: 120 }} />
            <span className="lg-blob lg-drop" ref={drop3} style={{ width: 80, height: 80 }} />
          </>}
        </div>
      </div>

      <div className="lg-inner">
        <div className="lg-logo"><Sparkles size={30} aria-hidden="true" /><span className="lg-word">{letters}</span></div>
        <div className="lg-content">
          <span className="lg-eyebrow lg-in" style={delay(0)}>FIND YOUR NEXT OPPORTUNITY</span>
          <h1 className="lg-title"><span className="lg-in" style={delay(0.15)}>Your skills.</span><span className="lg-in lg-lime" style={delay(0.4)}>Your next chapter.</span></h1>
          <p className="lg-sub lg-in" style={delay(0.65)}>Discover careers that match what you know, understand your skill gaps, and build a pathway forward.</p>
          <ul className="lg-features">{features.map(({ icon: Icon, text }, i) =>
          <li key={text} className="lg-in" style={delay(0.9 + i * 0.25)}><Icon size={18} aria-hidden="true" />{text}</li>)}</ul>
          {!reduced && total > 0 && <div className="lg-match" aria-hidden="true">
            <div className="lg-match-top"><strong key={careerName} className="lg-name">{careerName}</strong><b>{current + 1} of {total}</b></div>
            <div className="lg-mbar"><div className="lg-mfill" style={{ width: `${((current + 1) / total) * 100}%` }} /></div>
            <div className="lg-mtag">Careers you can analyse</div>
          </div>}
        </div>
      </div>
    </aside>

    <main className="login-panel lg-side">
      <div className="lg-stack">
        <div className="lg-card">
          <div className="login-box">
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
        </div>
      </div>
    </main>
  </div>
}