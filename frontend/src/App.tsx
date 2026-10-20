import { useEffect, useState } from 'react'
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

const demoProfile: Profile = { education: 'Synthetic IT undergraduate', skills: ['skill_python', 'skill_sql'], interests: ['data'] }

export default function App() {
  const [user, setUser] = useState<DemoUser | null>(() => {
    try {
      const raw = sessionStorage.getItem('demoUser')
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })
  const [tab, setTab] = useState<Tab>('Dashboard')
  const [skills, setSkills] = useState<Skill[]>([])
  const [careers, setCareers] = useState<Career[]>([])
  const [trend, setTrend] = useState<TrendData | null>(null)
  const [sdgs, setSdgs] = useState<{ sdg: number; title: string; rationale: string }[]>([])
  const [profile, setProfile] = useState<Profile>(demoProfile)
  const [matches, setMatches] = useState<AnalyzeResponse | null>(null)
  const [scenarios, setScenarios] = useState<{ moderate: AnalyzeResponse; rapid: AnalyzeResponse } | null>(null)
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [booting, setBooting] = useState(true)
  const [analysedAt, setAnalysedAt] = useState<Date | null>(null)

  const loadData = () => {
    setBooting(true)
    setError('')
    void Promise.all([api.catalog(), api.trends(), api.sdgs()])
      .then(([c, t, s]) => { setSkills(c.skills); setCareers(c.careers); setTrend(t); setSdgs(s.mappings) })
      .catch(e => setError(String(e)))
      .finally(() => setBooting(false))
  }

  useEffect(() => { loadData() }, [])

  const analyze = async () => {
    setLoading(true); setError('')
    try {
      const [result, comparison] = await Promise.all([api.analyze(profile, 'moderate'), api.scenarios(profile)])
      setMatches(result); setScenarios(comparison); setAnalysedAt(new Date())
      const selected = result.matches[0]
      if (selected) setRoadmap(await api.roadmap(selected.role_id, selected.missing_skills, 'moderate'))
      setTab('Dashboard')
    } catch (e) { setError(String(e)) } finally { setLoading(false) }
  }

  const signIn = (u: DemoUser) => {
    setUser(u)
    try { sessionStorage.setItem('demoUser', JSON.stringify(u)) } catch { /* storage unavailable */ }
  }

  const signOut = () => {
    setUser(null); setTab('Dashboard'); setMatches(null); setScenarios(null); setRoadmap(null)
    try { sessionStorage.removeItem('demoUser') } catch { /* storage unavailable */ }
  }

  if (!user) return <LoginPage onSignIn={signIn} />

  return <Layout active={tab} onSelect={setTab} userName={user.name}>
    {error && <ErrorBanner message={error} onRetry={skills.length === 0 ? loadData : undefined} onDismiss={() => setError('')} />}
    {tab === 'Dashboard' && <DashboardPage name={user.name} matches={matches} scenarios={scenarios} roadmap={roadmap} skills={skills} sdgs={sdgs} loading={loading} onNavigate={setTab} onAnalyze={() => void analyze()} analysedAt={analysedAt} />}
    {tab === 'Profile' && <ProfilePage skills={skills} profile={profile} onChange={setProfile} onAnalyze={() => void analyze()} loading={loading} booting={booting} />}
    {tab === 'Trends' && <TrendsPage trend={trend} skills={skills} booting={booting} />}
    {tab === 'Careers' && <CareersPage results={matches} skills={skills} sdgs={sdgs} />}
    {tab === 'Simulator' && <SimulatorPage results={scenarios} />}
    {tab === 'Roadmap' && <RoadmapPage roadmap={roadmap} skills={skills} careers={careers} />}
    {tab === 'SDG Impact' && <SDGPage mappings={sdgs} topMatch={matches?.matches[0] ?? null} booting={booting} />}
    {tab === 'Account' && <AccountPage name={user.name} email={user.email} onSignOut={signOut} />}
    <p className="muted">Loaded {skills.length} synthetic skills / {careers.length} synthetic roles. Replace before judging.</p>
  </Layout>
}