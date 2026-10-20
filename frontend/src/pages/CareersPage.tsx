import type { AnalyzeResponse, Skill } from '../types'

export default function CareersPage({ results, skills }: { results: AnalyzeResponse | null; skills: Skill[] }) {
  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id
  const show = (ids: string[]) => ids.map(nameOf).join(', ') || 'None'

  return (
    <section>
      <h2>Career Matches & Skill Gaps</h2>
      {results?.matches.length ? (
        <div className="grid">
          {results.matches.map(r => (
            <article className="card" key={r.role_id}>
              <h3>{r.title}</h3>
              <strong>{r.readiness_score}%</strong>
              <p>Matched: {show(r.matched_skills)}</p>
              <p>Missing: {show(r.missing_skills)}</p>
              <small>Skill compatibility only; not hiring probability</small>
            </article>
          ))}
        </div>
      ) : (
        <p>Analyze a profile first.</p>
      )}
    </section>
  )
}