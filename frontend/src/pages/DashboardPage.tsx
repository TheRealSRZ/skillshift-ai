import { useEffect, useState, type ReactNode } from 'react'
import type { Tab } from '../components/Layout'
import type { AnalyzeResponse, Match, RoadmapResponse, Skill } from '../types'

type Sdg = { sdg: number; title: string; rationale: string }
type Scenarios = { moderate: AnalyzeResponse; rapid: AnalyzeResponse }

type Props = {
  name: string
  matches: AnalyzeResponse | null
  scenarios: Scenarios | null
  roadmap: RoadmapResponse | null
  skills: Skill[]
  sdgs: Sdg[]
  loading: boolean
  analysedAt: Date | null
  onNavigate: (tab: Tab) => void
  onAnalyze: () => void
  selectedMatch: Match | null
  targetRoleId: string
  roadmapLoading: boolean
}

const pct = (score: number) => Math.round((score <= 1 ? score * 100 : score) * 10) / 10

function Widget({ title, to, onNavigate, children }: { title: string; to: Tab; onNavigate: (tab: Tab) => void; children: ReactNode }) {
  return (
    <div className="widget">
      <div className="widget-head">
        <h3>{title}</h3>
        <button type="button" className="link-btn" onClick={() => onNavigate(to)}>View all</button>
      </div>
      {children}
    </div>
  )
}

export default function DashboardPage({analysedAt, name, matches, scenarios, roadmap, skills, sdgs, loading, onNavigate, onAnalyze, selectedMatch, targetRoleId, roadmapLoading }: Props) {
  const top = matches?.matches[0]
  const focus = selectedMatch ?? top
  const [justUpdated, setJustUpdated] = useState(false)

  useEffect(() => {
    if (!analysedAt || Date.now() - analysedAt.getTime() > 3000) return
    setJustUpdated(true)
    const timer = setTimeout(() => setJustUpdated(false), 3000)
    return () => clearTimeout(timer)
  }, [analysedAt])

  if (!matches || !top) {
    return (
      <section className="hero-card">
        <h2>Start here: build your profile</h2>
        <p>Pick the skills you already have. SkillShift AI will match you to future roles, show what's missing, and suggest what to learn next.</p>
        <button type="button" className="primary" onClick={() => onNavigate('Profile')}>Build your profile</button>
      </section>
    )
  }

  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id
  const hours = roadmap ? roadmap.steps.reduce((sum, s) => sum + (s.estimated_hours ?? 0), 0) : 0
  const steps = roadmap?.steps.slice(0, 3) ?? []

  return (
    <section>
      <div className="dash-head">
        <div>
          <h2>Hi, {name}</h2>
          <p className="muted">Here's your latest analysis{analysedAt ? `, updated ${analysedAt.toLocaleTimeString()}` : ''}.</p>
        </div>
        <div className="dash-actions">
          {justUpdated && <span className="updated-pill" role="status">✓ Analysis updated</span>}
          <button type="button" onClick={() => onNavigate('Profile')}>Edit profile</button>
          <button type="button" className="primary" onClick={onAnalyze}>{loading ? 'Analysing…' : 'Re-analyse'}</button>
        </div>
      </div>

      <div key={`k${analysedAt?.getTime()}`} className={loading ? 'kpi-grid fade-in dim' : 'kpi-grid fade-in'}>
        <div className="kpi"><span>Top match</span><strong>{top.title}</strong><small>{pct(top.readiness_score)}% skill fit</small></div>
        <div className="kpi"><span>Skills you have</span><strong>{focus?.matched_skills.length ?? 0}</strong><small>for {focus?.title ?? top.title}</small></div>
        <div className="kpi"><span>Skills to learn</span><strong>{focus?.missing_skills.length ?? 0}</strong><small>for {focus?.title ?? top.title}</small></div>
        <div className="kpi"><span>Selected target</span><strong>{selectedMatch ? selectedMatch.title : 'Not set'}</strong><small>{selectedMatch ? `${selectedMatch.readiness_score}% readiness` : 'Choose one on Careers'}</small></div>
      </div>

      <div key={`w${analysedAt?.getTime()}`} className={loading ? 'widget-grid fade-in dim' : 'widget-grid fade-in'}>
        <Widget title="Career matches" to="Careers" onNavigate={onNavigate}>
          {matches.matches.map(m => (
            <div className="bar-row" key={m.role_id}>
              <span>{m.title}</span>
              <div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, pct(m.readiness_score))}%` }} /></div>
              <span className="bar-val">{pct(m.readiness_score)}%</span>
            </div>
          ))}
        </Widget>

        <Widget title={`Skills for ${focus?.title ?? top.title}`} to="Careers" onNavigate={onNavigate}>
          <p className="chip-label">You have</p>
          <div className="chips">
            {focus?.matched_skills.length === 0 && <span className="muted">None yet</span>}
            {focus?.matched_skills.map(id => <span className="chip have" key={id}>{nameOf(id)}</span>)}
          </div>
          <p className="chip-label">To learn</p>
          <div className="chips">
            {focus?.missing_skills.length === 0 && <span className="muted">Nothing missing</span>}
            {focus?.missing_skills.map(id => <span className="chip miss" key={id}>{nameOf(id)}</span>)}
          </div>
        </Widget>

        <Widget title="Moderate vs rapid" to="Simulator" onNavigate={onNavigate}>
          {scenarios ? (
            <div className="duo">
              <div><span className="muted">Moderate</span><strong>{scenarios.moderate.matches[0]?.title}</strong><small>{scenarios.moderate.matches[0] ? `${pct(scenarios.moderate.matches[0].readiness_score)}%` : ''}</small></div>
              <div><span className="muted">Rapid</span><strong>{scenarios.rapid.matches[0]?.title}</strong><small>{scenarios.rapid.matches[0] ? `${pct(scenarios.rapid.matches[0].readiness_score)}%` : ''}</small></div>
            </div>
          ) : <p className="muted">No scenarios yet.</p>}
        </Widget>

        <Widget title="Roadmap" to="Roadmap" onNavigate={onNavigate}>
          {!targetRoleId && <p className="muted">Select a target career on Careers or Roadmap.</p>}
          {targetRoleId && roadmapLoading && <p className="muted">Generating your roadmap…</p>}
          {targetRoleId && !roadmapLoading && steps.length === 0 && <p className="muted">No roadmap generated yet. Open Roadmap to request one.</p>}
          {roadmap && <p className="muted">{hours > 0 ? `${Math.round(hours * 10) / 10} h · ` : ''}{roadmap.generation_mode === 'runpod_validated' ? 'AI-assisted' : 'Verified fallback'}</p>}
          <ol className="mini-steps">
            {steps.map(s => (
              <li key={s.step}>
                <span className="step-num">{s.step}</span>
                <span className="step-title">{s.title}</span>
                {s.estimated_hours ? <span className="step-time">{Math.round(s.estimated_hours * 10) / 10} h</span> : null}
              </li>
            ))}
          </ol>
        </Widget>

        <Widget title={`SDGs for ${focus?.title ?? top.title}`} to="SDG Impact" onNavigate={onNavigate}>
          <div className="chips">
            {focus?.sdgs.map(n => <span className="chip sdg" key={n} title={sdgs.find(s => s.sdg === n)?.title}>SDG {n}</span>)}
          </div>
        </Widget>
      </div>
    </section>
  )
}