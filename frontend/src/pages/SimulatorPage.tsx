import type { AnalyzeResponse } from '../types'
export default function SimulatorPage({results}:{results:{moderate:AnalyzeResponse;rapid:AnalyzeResponse}|null}){
  return <section><h2>Future Scenario Simulator</h2><p>Hypothetical adoption scenarios, not forecasts.</p>
    {results?<div className="grid">{(['moderate','rapid'] as const).map(s=><article className="card" key={s}><h3>{s==='moderate'?'Moderate':'Rapid'} AI Adoption</h3>{results[s].matches.map(r=><p key={r.role_id}>{r.title}: <strong>{r.readiness_score}%</strong></p>)}</article>)}</div>:<p>Analyze a profile to compare both scenarios.</p>}
  </section>
}
