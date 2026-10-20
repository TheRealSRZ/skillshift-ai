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

export default function App() {
  const [user, setUser] = useState<DemoUser | null>(() => {
    try {
      const raw = sessionStorage.getItem('demoUser')
      return raw ? JSON.parse(raw) : null
    } catch { return null }
  })
  const [theme, setTheme] = useState<Theme>(initialTheme)
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
  const [booting, setBooting] = useState(true)
  const [analysedAt, setAnalysedAt] = useState<Date | null>(null)
  // Monotonic request IDs stop an old response replacing results after user edits.
  const analysisSeq = useRef(0)
  const roadmapSeq = useRef(0)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('skillshift-theme', theme) } catch { /* optional preference */ }
  }, [theme])

  const loadData = () => {
    setBooting(true)
    setError('')
    void Promise.all([api.catalog(), api.trends(), api.sdgs()])
      .then(([c, t, s]) => { setSkills(c.skills); setCareers(c.careers); setTrend(t); setSdgs(s.mappings) })
      .catch(e => setError(String(e)))
      .finally(() => setBooting(false))
  }

  useEffect(() => { loadData() }, [])

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

  const signIn = (u: DemoUser) => {
    setUser(u)
    try { sessionStorage.setItem('demoUser', JSON.stringify(u)) } catch { /* storage unavailable */ }
  }

  const signOut = () => {
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

  if (!user) return <LoginPage onSignIn={signIn} />

  return <Layout active={tab} onSelect={setTab} userName={user.name} theme={theme} onToggleTheme={() => setTheme(t => t === 'light' ? 'dark' : 'light')}>
    {error && <ErrorBanner message={error} onRetry={skills.length === 0 ? loadData : undefined} onDismiss={() => setError('')} />}
    {tab === 'Dashboard' && <DashboardPage name={user.name} matches={matches} scenarios={scenarios} roadmap={roadmap} skills={skills} sdgs={sdgs} loading={loading} onNavigate={setTab} onAnalyze={() => void analyze()} analysedAt={analysedAt} selectedMatch={selectedMatch} targetRoleId={targetRoleId} roadmapLoading={roadmapLoading} />}
    {tab === 'Profile' && <ProfilePage skills={skills} careers={careers} profile={profile} onChange={changeProfile} targetRoleId={targetRoleId} onSelectTarget={selectTarget} onAnalyze={() => void analyze()} loading={loading} booting={booting} />}
    {tab === 'Trends' && <TrendsPage trend={trend} skills={skills} booting={booting} />}
    {tab === 'Careers' && <CareersPage results={matches} skills={skills} sdgs={sdgs} selectedRoleId={targetRoleId} onSelectRole={selectTarget} onOpenRoadmap={() => setTab('Roadmap')} />}
    {tab === 'Simulator' && <SimulatorPage results={scenarios} />}
    {tab === 'Roadmap' && <RoadmapPage roadmap={roadmap} skills={skills} careers={careers} results={matches} targetRoleId={targetRoleId} onSelectRole={selectTarget} onGenerate={() => void generateRoadmap()} loading={roadmapLoading} error={roadmapError} onNavigate={setTab} />}
    {tab === 'SDG Impact' && <SDGPage mappings={sdgs} topMatch={selectedMatch ?? matches?.matches[0] ?? null} booting={booting} />}
    {tab === 'Account' && <AccountPage name={user.name} email={user.email} onSignOut={signOut} />}
    <p className="muted data-footnote">Demo catalog: {skills.length} skills · {careers.length} careers. Readiness is not hiring probability.</p>
  </Layout>
}
