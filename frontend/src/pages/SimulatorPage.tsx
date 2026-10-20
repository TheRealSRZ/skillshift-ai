import type { AnalyzeResponse } from '../types'

type Results = { moderate: AnalyzeResponse; rapid: AnalyzeResponse }

export default function SimulatorPage({ results }: { results: Results | null }) {
  const moderateScore = (roleId: string) =>
    results?.moderate.matches.find(m => m.role_id === roleId)?.readiness_score

  const changeText = (roleId: string, score: number) => {
    const base = moderateScore(roleId)
    if (base === undefined) return ''
    const diff = Math.round((score - base) * 10) / 10
    if (diff === 0) return 'no change vs Moderate'
    return `${Math.abs(diff)} ${diff < 0 ? 'lower' : 'higher'} than Moderate`
  }

  return (
    <section>
      <h2>Future Scenario Simulator</h2>
      <p>Hypothetical adoption scenarios, not forecasts.</p>
      {results ? (
        <div className="grid">
          {(['moderate', 'rapid'] as const).map(s => (
            <article className="card" key={s}>
              <h3>{s === 'moderate' ? 'Moderate' : 'Rapid'} AI Adoption</h3>
              {results[s].matches.map(r => {
                const note = s === 'rapid' ? changeText(r.role_id, r.readiness_score) : ''
                return (
                  <p key={r.role_id}>
                    {r.title}: <strong>{r.readiness_score}%</strong>
                    {note && <small> ({note})</small>}
                  </p>
                )
              })}
            </article>
          ))}
        </div>
      ) : (
        <p>Analyze a profile to compare both scenarios.</p>
      )}
    </section>
  )
}