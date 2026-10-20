import { useState } from 'react'
import type { AnalyzeResponse, Match, Skill } from '../types'

type SdgInfo = { sdg: number; title: string }

const SHOW_MISSING = 2

function RoleCard({ role, isTop, nameOf, sdgs }: { role: Match; isTop: boolean; nameOf: (id: string) => string; sdgs: SdgInfo[] }) {
  const [expanded, setExpanded] = useState(false)
  const missing = expanded ? role.missing_skills : role.missing_skills.slice(0, SHOW_MISSING)
  const hidden = role.missing_skills.length - SHOW_MISSING
  const roleSdgs = role.sdgs ?? []

  return (
    <article className={isTop ? 'role-card top' : 'role-card'}>
      <div className="role-head">
        <h3>{role.title}</h3>
        {isTop && <span className="top-badge">Top match</span>}
      </div>

      <div className="score-row">
        <strong className="score-val">{role.readiness_score}%</strong>
        <div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, role.readiness_score)}%` }} /></div>
      </div>

      <p className="chip-label">You have</p>
      <div className="chips">
        {role.matched_skills.length === 0 && <span className="chip none">None yet</span>}
        {role.matched_skills.map(id => <span className="chip have" key={id}>{nameOf(id)}</span>)}
      </div>

      <p className="chip-label">To learn</p>
      <div className="chips">
        {role.missing_skills.length === 0 && <span className="chip none">Nothing missing</span>}
        {missing.map(id => <span className="chip miss" key={id}>{nameOf(id)}</span>)}
        {hidden > 0 && (
          <button type="button" className="chip more" onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Show less' : `+${hidden} more`}
          </button>
        )}
      </div>

      <p className="chip-label">Linked SDGs</p>
      <div className="chips">
        {roleSdgs.length === 0 && <span className="chip none">None</span>}
        {roleSdgs.map(n => <span className="chip tag" key={n} title={sdgs.find(g => g.sdg === n)?.title}>SDG {n}</span>)}
      </div>
    </article>
  )
}

export default function CareersPage({ results, skills, sdgs }: { results: AnalyzeResponse | null; skills: Skill[]; sdgs: SdgInfo[] }) {
  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id

  return (
    <section>
      <h2>Career matches and skill gaps</h2>
      {results?.matches.length ? (
        <>
          <div className="role-grid">
            {results.matches.map((r, i) => (
              <RoleCard key={r.role_id} role={r} isTop={i === 0 && r.readiness_score > 0} nameOf={nameOf} sdgs={sdgs} />
            ))}
          </div>
          <p className="page-foot">Skill compatibility only; not hiring probability.</p>
        </>
      ) : (
        <p className="muted">Analyse a profile first.</p>
      )}
    </section>
  )
}