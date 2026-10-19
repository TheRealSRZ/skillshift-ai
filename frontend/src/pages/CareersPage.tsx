import type { AnalyzeResponse } from '../types'
export default function CareersPage({results}:{results:AnalyzeResponse|null}){
  return <section><h2>Career Matches & Skill Gaps</h2>{results?.matches.length?<div className="grid">{results.matches.map(r=><article className="card" key={r.role_id}><h3>{r.title}</h3><strong>{r.readiness_score}%</strong><p>Matched: {r.matched_skills.join(', ')||'None'}</p><p>Missing: {r.missing_skills.join(', ')||'None'}</p><small>Skill compatibility only; not hiring probability</small></article>)}</div>:<p>Analyze a profile first.</p>}</section>
}
