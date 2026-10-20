import type { AnalyzeResponse, Skill } from '../types'

type SdgInfo = { sdg: number; title: string }

export default function CareersPage({ results, skills, sdgs }: { results: AnalyzeResponse | null; skills: Skill[]; sdgs: SdgInfo[] }) {
  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id
  const show = (ids: string[]) => ids.map(nameOf).join(', ') || 'None'
  const sdgLabel = (n: number) => {
    const title = sdgs.find(g => g.sdg === n)?.title
    return title ? `SDG ${n} (${title})` : `SDG ${n}`
  }

  return (
    <section>
      <h2>Career Matches & Skill Gaps</h2>
      {results?.matches.length ? (
        <div className="grid">
          {results.matches.map(r => {
            const roleSdgs = r.sdgs ?? []
            return (
              <article className="card" key={r.role_id}>
                <h3>{r.title}</h3>
                <strong>{r.readiness_score}%</strong>
                <p>Matched: {show(r.matched_skills)}</p>
                <p>Missing: {show(r.missing_skills)}</p>
                <p>Linked SDGs: {roleSdgs.length ? roleSdgs.map(sdgLabel).join(', ') : 'None'}</p>
                <small>Skill compatibility only; not hiring probability</small>
              </article>
            )
          })}
        </div>
      ) : (
        <p>Analyze a profile first.</p>
      )}
    </section>
  )
}