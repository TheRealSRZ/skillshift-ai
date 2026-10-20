import { Check, ExternalLink, Info } from 'lucide-react'
import type { Career, RoadmapResponse, Skill } from '../types'

export default function RoadmapPage({ roadmap, skills, careers }: { roadmap: RoadmapResponse | null; skills: Skill[]; careers: Career[] }) {
  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id
  const cleanText = (text: string) => text.replace(/skill_[a-z0-9_]+/g, id => nameOf(id))
  const roleTitle = careers.find(c => c.id === roadmap?.target_role)?.title ?? roadmap?.target_role

  const totalHours = roadmap
    ? Math.round(roadmap.steps.reduce((sum, s) => sum + (s.estimated_hours ?? 0), 0) * 100) / 100
    : 0

  return (
    <section>
      <h2>Your reskilling pathway</h2>
      {roadmap ? (
        <>
          <div className="note-banner">
            <Info size={18} aria-hidden="true" />
            <span>{roadmap.note}</span>
          </div>

          {roadmap.steps.length ? (
            <>
              <div className="kpi-grid three">
                <div className="kpi"><span>Target role</span><strong>{roleTitle}</strong></div>
                <div className="kpi"><span>Total estimated time</span><strong>{totalHours} h</strong></div>
                <div className="kpi"><span>Courses</span><strong>{roadmap.steps.length}</strong></div>
              </div>

              <ol className="path">
                {roadmap.steps.map(step => (
                  <li key={step.course_id}>
                    <span className="step-num">{step.step}</span>
                    <div className="path-card">
                      <a className="path-title" href={step.url} target="_blank" rel="noopener noreferrer">
                        {step.title}
                        <ExternalLink size={14} aria-hidden="true" />
                      </a>
                      <p className="path-reason">{cleanText(step.reason)}</p>
                      <span className="step-time">{step.estimated_hours != null ? `${step.estimated_hours} h` : 'Time not listed'}</span>
                    </div>
                  </li>
                ))}
              </ol>
            </>
          ) : (
            <p className="muted">No verified courses are available in the starter catalog. Member 4 must validate real resources.</p>
          )}

          {roadmap.uncovered_skills.length === 0 ? (
            <div className="note-banner ok">
              <Check size={18} aria-hidden="true" />
              <span>All your missing skills are covered by this pathway.</span>
            </div>
          ) : (
            <>
              <p className="chip-label" style={{ marginTop: 20 }}>Not covered yet</p>
              <div className="chips">
                {roadmap.uncovered_skills.map(id => <span className="chip miss" key={id}>{nameOf(id)}</span>)}
              </div>
            </>
          )}
        </>
      ) : (
        <p className="muted">Analyse a profile first to get your pathway.</p>
      )}
    </section>
  )
}