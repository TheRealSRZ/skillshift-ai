import { useEffect, useRef, useState } from 'react'
import Layout, { type Tab } from './components/Layout'
import ProfilePage from './pages/ProfilePage'
import TrendsPage from './pages/TrendsPage'
import CareersPage from './pages/CareersPage'
import SimulatorPage from './pages/SimulatorPage'
import RoadmapPage from './pages/RoadmapPage'
import SDGPage from './pages/SDGPage'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import AccountPage from './pages/AccountPage'
import { useAuth } from './auth/AuthContext'
import { loadProfile, saveProfile } from './lib/accountData'
import { useToast } from './notifications/ToastProvider'
import { api } from './api/client'
import ErrorBanner from './components/ErrorBanner'
import type { AnalyzeResponse, Career, Profile, RoadmapResponse, Skill, TrendData } from './types'

type DemoUser = { name: string; email: string }
type Theme = 'light' | 'dark'
const demoProfile: Profile = { education: 'Synthetic IT undergraduate', skills: ['skill_python', 'skill_sql'], interests: ['data'] }

function initialTheme(): Theme {
  try {
    const saved = localStorage.getItem('skillshift-theme')
    if (saved === 'light' || saved === 'dark') return saved
  } catch { /* localStorage may be unavailable */ }
  return 'light'
}

function initialMotion(): boolean {
  try {
    const saved = localStorage.getItem('skillshift-reduce-motion')
    if (saved === 'on' || saved === 'off') return saved === 'on'
  } catch { /* localStorage may be unavailable */ }
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export default function App() {
  const auth = useAuth()
  const { notify } = useToast()
  const authUser = auth.user
  const [user, setUser] = useState<DemoUser | null>(() => {
    try {
      const raw = sessionStorage.getItem('demoUser')
      return raw ? JSON.parse(raw) : null
    } catch { return null }
  })
  const [theme, setTheme] = useState<Theme>(initialTheme)
  const [reduceMotion, setReduceMotion] = useState<boolean>(initialMotion)
  const [tab, setTab] = useState<Tab>('Dashboard')
  const [skills, setSkills] = useState<Skill[]>([])
  const [careers, setCareers] = useState<Career[]>([])
  const [trend, setTrend] = useState<TrendData | null>(null)
  const [sdgs, setSdgs] = useState<{ sdg: number; title: string; rationale: string }[]>([])
  const [profile, setProfile] = useState<Profile>(demoProfile)
  // A career is explicitly chosen by the user, never silently replaced by the top match.
  const [targetRoleId, setTargetRoleId] = useState('')
  const [matches, setMatches] = useState<AnalyzeResponse | null>(null)
  const [scenarios, setScenarios] = useState<{ moderate: AnalyzeResponse; rapid: AnalyzeResponse } | null>(null)
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null)
  const [roadmapError, setRoadmapError] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [roadmapLoading, setRoadmapLoading] = useState(false)
  const [profileSaving, setProfileSaving] = useState(false)
  const [booting, setBooting] = useState(true)
  const [analysedAt, setAnalysedAt] = useState<Date | null>(null)
  // Monotonic request IDs stop an old response replacing results after user edits.
  const analysisSeq = useRef(0)
  const roadmapSeq = useRef(0)
  const identitySeq = useRef(0)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('skillshift-theme', theme) } catch { /* optional preference */ }
  }, [theme])

    useEffect(() => {
    document.documentElement.dataset.motion = reduceMotion ? 'reduced' : 'full'
  }, [reduceMotion])

  const changeMotion = (value: boolean) => {
    setReduceMotion(value)
    try { localStorage.setItem('skillshift-reduce-motion', value ? 'on' : 'off') } catch { /* optional preference */ }
  }

  const loadData = () => {
    setBooting(true)
    setError('')
    void Promise.all([api.catalog(), api.trends(), api.sdgs()])
      .then(([c, t, s]) => { setSkills(c.skills); setCareers(c.careers); setTrend(t); setSdgs(s.mappings) })
      .catch(e => setError(String(e)))
      .finally(() => setBooting(false))
  }

  useEffect(() => { loadData() }, [])

  // User identities never share in-memory profile/analysis/roadmap state.
  useEffect(() => {
    const sequence = ++identitySeq.current
    analysisSeq.current += 1
    roadmapSeq.current += 1
    setProfile(authUser ? { education: '', skills: [], interests: [] } : demoProfile)
    setTargetRoleId('')
    setMatches(null)
    setScenarios(null)
    setRoadmap(null)
    setRoadmapError('')
    setError('')
    setLoading(false)
    setRoadmapLoading(false)
    setAnalysedAt(null)
    setTab(auth.recovery ? 'Account' : 'Dashboard')

    if (authUser) {
      setUser(null)
      try { sessionStorage.removeItem('demoUser') } catch { /* optional storage */ }
      void loadProfile(authUser.id).then(saved => {
        if (sequence !== identitySeq.current || !saved) return
        setProfile({ education: saved.education, skills: saved.skills, interests: saved.interests })
        setTargetRoleId(saved.target_role)
        if (saved.theme === 'light' || saved.theme === 'dark') setTheme(saved.theme)
      }).catch(() => {
        if (sequence === identitySeq.current) setError('Unable to load saved profile. Check Supabase migrations.')
      })
    }
  }, [authUser?.id, user?.email])

  useEffect(() => {
    if (auth.recovery && authUser) setTab('Account')
  }, [auth.recovery, authUser?.id])

  const restoreProfile = (saved: Profile, role: string) => {
    changeProfile(saved)
    setTargetRoleId(role)
    setTab('Profile')
  }

  const changeProfile = (next: Profile) => {
    analysisSeq.current += 1
    roadmapSeq.current += 1
    setProfile(next)
    setMatches(null)
    setScenarios(null)
    setRoadmap(null)
    setRoadmapError('')
    setError('')
    setLoading(false)
    setRoadmapLoading(false)
    setAnalysedAt(null)
  }

  const selectTarget = (id: string) => {
    if (id === targetRoleId) return
    roadmapSeq.current += 1
    setTargetRoleId(id)
    setRoadmap(null)
    setRoadmapError('')
    setRoadmapLoading(false)
  }

  const analyze = async () => {
    const token = ++analysisSeq.current
    roadmapSeq.current += 1
    setLoading(true)
    setError('')
    setMatches(null)
    setScenarios(null)
    setRoadmap(null)
    setRoadmapError('')
    setRoadmapLoading(false)
    try {
      // Career scores appear immediately; scenarios and RunPod cannot block analysis.
      const result = await api.analyze(profile, 'moderate')
      if (token !== analysisSeq.current) return
      setMatches(result)
      setAnalysedAt(new Date())
      setTab('Dashboard')
      void api.scenarios(profile)
        .then(comparison => { if (token === analysisSeq.current) setScenarios(comparison) })
        .catch(() => { /* analysis still usable without comparison; user can retry */ })
    } catch (e) {
      if (token === analysisSeq.current) setError(String(e))
    } finally {
      if (token === analysisSeq.current) setLoading(false)
    }
  }

  const generateRoadmap = async () => {
    const role = matches?.matches.find(item => item.role_id === targetRoleId)
    if (!role) {
      setRoadmapError('Choose a target career and analyse your profile first.')
      setTab('Roadmap')
      return
    }
    if (role.missing_skills.length === 0) {
      setRoadmap(null)
      setRoadmapError('')
      setTab('Roadmap')
      return // No AI request when all required skills are present.
    }
    const token = ++roadmapSeq.current
    setRoadmap(null)
    setRoadmapError('')
    setRoadmapLoading(true)
    setTab('Roadmap')
    try {
      const response = await api.roadmap(role.role_id, role.missing_skills, 'moderate')
      if (token === roadmapSeq.current) setRoadmap(response)
    } catch (e) {
      if (token === roadmapSeq.current) setRoadmapError(String(e))
    } finally {
      if (token === roadmapSeq.current) setRoadmapLoading(false)
    }
  }

  const saveCurrentProfile = async () => {
    if (!authUser) { notify('info', 'Sign in to save your career profile.'); return }
    setProfileSaving(true)
    try {
      const displayName = String(authUser.user_metadata?.display_name || authUser.user_metadata?.full_name || authUser.email?.split('@')[0] || 'Student')
      await saveProfile(authUser.id, displayName, profile, targetRoleId, theme)
      notify('success', 'Career profile saved! Your skills and target role will be ready next time.')
    } catch (reason) {
      notify('error', reason instanceof Error ? reason.message : 'Unable to save your profile.')
    } finally { setProfileSaving(false) }
  }

  const signIn = (u: DemoUser) => {
    setUser(u)
    try { sessionStorage.setItem('demoUser', JSON.stringify(u)) } catch { /* storage unavailable */ }
  }

  const signOut = async () => {
    if (authUser) {
      try { await auth.signOut() }
      catch { setError('Sign-out failed. Please try again.'); return }
    }
    identitySeq.current += 1
    analysisSeq.current += 1
    roadmapSeq.current += 1
    setUser(null)
    setTab('Dashboard')
    setProfile(demoProfile)
    setTargetRoleId('')
    setMatches(null)
    setScenarios(null)
    setRoadmap(null)
    setRoadmapError('')
    setLoading(false)
    setRoadmapLoading(false)
    try { sessionStorage.removeItem('demoUser') } catch { /* storage unavailable */ }
  }

  const selectedMatch = matches?.matches.find(m => m.role_id === targetRoleId) ?? null
  const userName = authUser
    ? String(authUser.user_metadata?.display_name || authUser.user_metadata?.full_name || authUser.email?.split('@')[0] || 'Student')
    : user?.name
  const userEmail = authUser?.email || user?.email || ''
  const avatarUrl = authUser ? String(authUser.user_metadata?.avatar_url || authUser.user_metadata?.picture || '') : null

  if (auth.loading && !user) return <div className="auth-loading" role="status">Restoring your session…</div>
  if (!userName) return <LoginPage onSignIn={signIn} />

  return <Layout active={tab} onSelect={setTab} userName={userName} avatarUrl={avatarUrl} theme={theme} onToggleTheme={() => setTheme(t => t === 'light' ? 'dark' : 'light')}>
    {error && <ErrorBanner message={error} onRetry={skills.length === 0 ? loadData : undefined} onDismiss={() => setError('')} />}
    <div className="page-fade" key={tab}>
    {tab === 'Dashboard' && <DashboardPage name={userName} matches={matches} scenarios={scenarios} roadmap={roadmap} skills={skills} sdgs={sdgs} loading={loading} onNavigate={setTab} onAnalyze={() => void analyze()} analysedAt={analysedAt} selectedMatch={selectedMatch} targetRoleId={targetRoleId} roadmapLoading={roadmapLoading} />}
    {tab === 'Profile' && <ProfilePage skills={skills} careers={careers} profile={profile} onChange={changeProfile} targetRoleId={targetRoleId} onSelectTarget={selectTarget} onAnalyze={() => void analyze()} loading={loading} booting={booting} userName={userName} avatarUrl={avatarUrl} authenticated={Boolean(authUser)} onSave={() => void saveCurrentProfile()} saving={profileSaving} />}
    {tab === 'Trends' && <TrendsPage trend={trend} skills={skills} booting={booting} />}
    {tab === 'Careers' && <CareersPage results={matches} skills={skills} sdgs={sdgs} selectedRoleId={targetRoleId} onSelectRole={selectTarget} onOpenRoadmap={() => setTab('Roadmap')} />}
    {tab === 'Simulator' && <SimulatorPage results={scenarios} />}
    {tab === 'Roadmap' && <RoadmapPage roadmap={roadmap} skills={skills} careers={careers} results={matches} targetRoleId={targetRoleId} onSelectRole={selectTarget} onGenerate={() => void generateRoadmap()} loading={roadmapLoading} error={roadmapError} onNavigate={setTab} />}
    {tab === 'SDG Impact' && <SDGPage mappings={sdgs} topMatch={selectedMatch ?? matches?.matches[0] ?? null} booting={booting} />}
    {tab === 'Account' && <AccountPage name={userName} email={userEmail} avatarUrl={avatarUrl} onSignOut={() => void signOut()} profile={profile} targetRoleId={targetRoleId} careers={careers} theme={theme} matches={matches} roadmap={roadmap} onRestoreProfile={restoreProfile} reduceMotion={reduceMotion} onReduceMotion={changeMotion} />} 
    </div>  
    <p className="muted data-footnote">Demo catalog: {skills.length} skills · {careers.length} careers. Readiness is not hiring probability.</p>
  </Layout>
}
