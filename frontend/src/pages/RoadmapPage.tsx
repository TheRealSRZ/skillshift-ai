import { Check, ExternalLink, Info, Loader2, Sparkles, ShieldCheck } from 'lucide-react'
import type { Tab } from '../components/Layout'
import type { AnalyzeResponse, Career, RoadmapResponse, Skill } from '../types'

type Props = {
  roadmap: RoadmapResponse | null
  skills: Skill[]
  careers: Career[]
  results: AnalyzeResponse | null
  targetRoleId: string
  onSelectRole: (id: string) => void
  onGenerate: () => void
  onPersonalize: () => void
  aiAuthenticated: boolean
  onSignIn: () => void
  loading: boolean
  aiLoading: boolean
  aiError: string
  error: string
  onNavigate: (tab: Tab) => void
}

export default function RoadmapPage({ roadmap, skills, careers, results, targetRoleId, onSelectRole, onGenerate, onPersonalize, aiAuthenticated, onSignIn, loading, aiLoading, aiError, error, onNavigate }: Props) {
  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id
  const cleanText = (text: string) => text.replace(/skill_[a-z0-9_]+/g, id => nameOf(id))
  const selected = results?.matches.find(m => m.role_id === targetRoleId)
  const roleTitle = careers.find(c => c.id === targetRoleId)?.title ?? targetRoleId
  const totalHours = roadmap
    ? Math.round(roadmap.steps.reduce((sum, s) => sum + (s.estimated_hours ?? 0), 0) * 100) / 100
    : 0

  return (
    <section>
      <h2 className="intro-title">
        <span className="intro-w">Learning</span>{' '}
        <span className="intro-chip" aria-hidden="true">✦</span>{' '}
        <b className="intro-w"><span className="intro-hl">roadmap</span></b>
      </h2>
      <div className="intro-pills">
        <span className="intro-pill">Build a learning plan for the career you've chosen.</span>
      </div>
      <div className="roadmap-controls">
        <div className="roadmap-field">
          <label htmlFor="roadmap-career" className="form-label">Target career</label>
          <select id="roadmap-career" className="text-field" value={targetRoleId} onChange={e => onSelectRole(e.target.value)}>
            <option value="">Choose your target career</option>
            {careers.map(role => <option value={role.id} key={role.id}>{role.title}</option>)}
          </select>
        </div>
        <button className="primary" type="button" onClick={onGenerate} disabled={!selected || selected.missing_skills.length === 0 || loading || aiLoading}>
          {loading && <Loader2 className="spin" size={16} aria-hidden="true" />}
          {loading ? 'Preparing approved courses…' : roadmap ? 'Refresh approved roadmap' : 'Generate approved roadmap'}
        </button>
      </div>

      {!results && <div className="empty-state"><p>Analyse your skills first so we can identify the right learning gaps.</p><button type="button" onClick={() => onNavigate('Profile')}>Go to profile</button></div>}
      {results && !targetRoleId && <div className="empty-state">Choose a target career above to see your missing skills and generate a learning plan.</div>}
      {results && targetRoleId && !selected && <div className="empty-state">This career is not in your latest analysis. Analyse your profile again.</div>}

      {selected && <div className="target-summary">
        <div><span className="muted">Selected career</span><strong>{roleTitle}</strong></div>
        <div><span className="muted">Skill readiness</span><strong>{selected.readiness_score}%</strong></div>
        <div><span className="muted">Missing skills</span><strong>{selected.missing_skills.length}</strong></div>
      </div>}
      {selected && selected.missing_skills.length > 0 && <div className="roadmap-gaps"><span className="form-label">Skills to develop</span><div className="chips">{selected.missing_skills.map(id => <span key={id} className="chip miss">{nameOf(id)}</span>)}</div></div>}
      {selected && selected.missing_skills.length === 0 && <div className="note-banner ok"><Check size={18} aria-hidden="true" /><span>You've matched every required skill for this career. No gap-based courses are needed.</span></div>}
      {error && <div className="error roadmap-error" role="alert">Roadmap request failed: {error}. Your career scores are still available. You can try again.</div>}
      {loading && <div className="roadmap-loading" role="status" aria-live="polite"><Loader2 className="spin" size={20} aria-hidden="true" /><div><strong>Preparing approved courses</strong><p className="muted">This first step uses the verified catalog without waiting for AI.</p></div></div>}

      {!loading && selected && selected.missing_skills.length > 0 && !roadmap && !error && <div className="empty-state">Select “Generate approved roadmap” for an immediate verified learning plan. You can optionally refine it with AI afterwards.</div>}
      {roadmap && (
        <>
          <div className="note-banner roadmap-mode">
            <ShieldCheck size={18} aria-hidden="true" />
            <span><strong>{roadmap.generation_mode === 'runpod_validated' ? 'AI-assisted roadmap · validated' : 'Approved-course roadmap · ready now'}</strong> — {roadmap.note}</span>
          </div>
          <div className="roadmap-ai-stage">
            <div className="roadmap-ai-copy">
              <span className="roadmap-stage-label"><Sparkles size={16} aria-hidden="true" /> Optional step 2</span>
              <h3>Personalize with AI</h3>
              <p className="muted">Ask RunPod to select or reorder approved courses. Your current roadmap stays visible while AI works, even if the worker is starting or the request times out.</p>
              {!aiAuthenticated && <p className="muted">AI personalization requires a signed-in account to protect limited GPU credits. Guest roadmaps remain free.</p>}
            </div>
            {!aiAuthenticated && <button type="button" className="roadmap-ai-button" onClick={onSignIn}>Sign in for AI</button>}
            <button className="roadmap-ai-button" type="button" onClick={onPersonalize} disabled={!aiAuthenticated || loading || aiLoading || !selected || roadmap.steps.length === 0}>
              {aiLoading ? <Loader2 size={17} className="spin" aria-hidden="true" /> : <Sparkles size={17} aria-hidden="true" />}
              {aiLoading ? 'AI is personalizing…' : roadmap.generation_mode === 'runpod_validated' ? 'Personalize again' : 'Personalize with AI'}
            </button>
          </div>
          {aiLoading && <div className="roadmap-ai-status" role="status" aria-live="polite"><Loader2 className="spin" size={17} aria-hidden="true" /> RunPod is processing your request. You can use the approved courses below in the meantime.</div>}
          {aiError && <div className="note-banner roadmap-ai-warning" role="alert"><Info size={18} aria-hidden="true" /><span>{aiError} You can try again later.</span></div>}
          {roadmap.steps.length > 0 ? (
            <>
              <div className="kpi-grid three">
                <div className="kpi"><span>Target career</span><strong>{roleTitle}</strong></div>
                <div className="kpi"><span>Estimated time</span><strong>{totalHours} h</strong></div>
                <div className="kpi"><span>Courses</span><strong>{roadmap.steps.length}</strong></div>
              </div>
              <ol className="path">
                {roadmap.steps.map(step => (
                  <li key={step.course_id}>
                    <span className="step-num">{step.step}</span>
                    <div className="path-card">
                      <a className="path-title" href={step.url} target="_blank" rel="noopener noreferrer">{step.title}<ExternalLink size={14} aria-hidden="true" /></a>
                      <p className="path-reason">{cleanText(step.reason)}</p>
                      <span className="step-time">{step.estimated_hours != null ? `${step.estimated_hours} h` : 'Time not listed'}</span>
                    </div>
                  </li>
                ))}
              </ol>
            </>
          ) : <div className="empty-state">No approved courses were returned for these gaps. Check the uncovered skills below.</div>}
          {roadmap.uncovered_skills.length === 0 ? (
            <div className="note-banner ok"><Check size={18} aria-hidden="true" /><span>All the identified skill gaps have approved course coverage.</span></div>
          ) : (
            <div className="roadmap-gaps"><span className="form-label">Skills not covered by the catalog yet</span><div className="chips">{roadmap.uncovered_skills.map(id => <span className="chip miss" key={id}>{nameOf(id)}</span>)}</div></div>
          )}
        </>
      )}
    </section>
  )
}
