import { useEffect, useState } from 'react'
import Layout, { type Tab } from './components/Layout'
import ProfilePage from './pages/ProfilePage'
import TrendsPage from './pages/TrendsPage'
import CareersPage from './pages/CareersPage'
import SimulatorPage from './pages/SimulatorPage'
import RoadmapPage from './pages/RoadmapPage'
import SDGPage from './pages/SDGPage'
import { api } from './api/client'
import type { AnalyzeResponse, Career, Profile, RoadmapResponse, Skill, TrendData } from './types'

const demoProfile: Profile = { education:'Synthetic IT undergraduate', skills:['skill_python','skill_sql'], interests:['data'] }
export default function App(){
  const [tab,setTab]=useState<Tab>('Profile')
  const [skills,setSkills]=useState<Skill[]>([])
  const [careers,setCareers]=useState<Career[]>([])
  const [trend,setTrend]=useState<TrendData|null>(null)
  const [sdgs,setSdgs]=useState<{sdg:number;title:string;rationale:string}[]>([])
  const [profile,setProfile]=useState<Profile>(demoProfile)
  const [matches,setMatches]=useState<AnalyzeResponse|null>(null)
  const [scenarios,setScenarios]=useState<{moderate:AnalyzeResponse;rapid:AnalyzeResponse}|null>(null)
  const [roadmap,setRoadmap]=useState<RoadmapResponse|null>(null)
  const [error,setError]=useState('')
  const [loading,setLoading]=useState(false)
  useEffect(()=>{ void Promise.all([api.catalog(),api.trends(),api.sdgs()]).then(([c,t,s])=>{setSkills(c.skills);setCareers(c.careers);setTrend(t);setSdgs(s.mappings)}).catch(e=>setError(String(e))) },[])
  const analyze=async()=>{
    setLoading(true);setError('')
    try {
      const [result,comparison] = await Promise.all([api.analyze(profile,'moderate'),api.scenarios(profile)])
      setMatches(result);setScenarios(comparison)
      const selected = result.matches[0]
      if (selected) setRoadmap(await api.roadmap(selected.role_id,selected.missing_skills,'moderate'))
      setTab('Careers')
    } catch(e) { setError(String(e)) } finally {setLoading(false)}
  }
  return <Layout active={tab} onSelect={setTab}>
    {error&&<p role="alert" className="error">{error}. Make sure FastAPI is running on port 8000.</p>}
    {tab==='Profile'&&<ProfilePage skills={skills} profile={profile} onChange={setProfile} onAnalyze={()=>void analyze()} loading={loading}/>}
    {tab==='Trends'&&<TrendsPage trend={trend} skills={skills}/>}
    {tab==='Careers'&&<CareersPage results={matches} skills={skills}/>}
    {tab==='Simulator'&&<SimulatorPage results={scenarios}/>}
    {tab==='Roadmap'&&<RoadmapPage roadmap={roadmap} skills={skills} careers={careers}/>}
    {tab==='SDG Impact'&&<SDGPage mappings={sdgs}/>}
    <p className="muted">Loaded {skills.length} synthetic skills / {careers.length} synthetic roles. Replace before judging.</p>
  </Layout>
}
