import type { Match } from '../types'

type Mapping = { sdg: number; title: string; rationale: string }

export default function SDGPage({ mappings, topMatch }: { mappings: Mapping[]; topMatch: Match | null }) {
  const roleSdgs = topMatch?.sdgs ?? []

  return (
    <section>
      <h2>SDG Impact</h2>
      <p>Primary target: SDG 4 Quality Education. Contributions shown are proposed, not measured impacts.</p>
      {topMatch ? (
        <p>
          Your top matched role, <strong>{topMatch.title}</strong>, links to:{' '}
          <strong>{roleSdgs.length ? roleSdgs.map(n => `SDG ${n}`).join(', ') : 'no SDGs yet'}</strong>
        </p>
      ) : (
        <p>Analyze a profile to see how your top role links to the SDGs.</p>
      )}
      <div className="grid">
        {mappings.map(s => {
          const linked = roleSdgs.includes(s.sdg)
          return (
            <article className="card" key={s.sdg}>
              <h3>SDG {s.sdg} — {s.title}</h3>
              {linked && <p><strong>✓ Linked to your path</strong></p>}
              <p>{s.rationale}</p>
            </article>
          )
        })}
      </div>
    </section>
  )
}