import { useState } from 'react'
import { Check, Route } from 'lucide-react'
import type { Match } from '../types'

type Mapping = { sdg: number; title: string; rationale: string }

const PRIMARY_SDG = 4
const PRIMARY_GIF = '/sdg/E_GIF_04.gif'

function SdgIcon({ n, size, src }: { n: number; size: number; src?: string }) {
  const [failed, setFailed] = useState(false)
  if (failed) return <span className="sdg-badge" style={{ width: size, height: size }}>{n}</span>
  return (
    <img
      className="sdg-icon"
      src={src ?? `/sdg/E_WEB_${String(n).padStart(2, '0')}.png`}
      alt={`SDG ${n}`}
      width={size}
      height={size}
      onError={() => setFailed(true)}
    />
  )
}

export default function SDGPage({ mappings, topMatch, booting }: { mappings: Mapping[]; topMatch: Match | null; booting: boolean }) {
  const roleSdgs = topMatch?.sdgs ?? []
  const titleOf = (n: number) => mappings.find(m => m.sdg === n)?.title
  const primaryTitle = titleOf(PRIMARY_SDG)

  return (
    <section>
      <div className="sdg-hero">
        <SdgIcon n={PRIMARY_SDG} size={64} src={PRIMARY_GIF} />
        <div>
          <p className="kicker">Primary target</p>
          <p className="big">SDG {PRIMARY_SDG}{primaryTitle ? `: ${primaryTitle}` : ''}</p>
          <p className="small">Contributions shown are proposed, not measured impacts.</p>
        </div>
      </div>

      <p className="sdg-label">Your top match connects to</p>
      {topMatch ? (
        <div className="sdg-path">
          <Route size={18} aria-hidden="true" />
          <span><strong>{topMatch.title}</strong> is linked to</span>
          {roleSdgs.length === 0 && <strong>no SDGs yet</strong>}
          {roleSdgs.map(n => (
            <span className="sdg-pill" key={n}>
              <SdgIcon n={n} size={24} />
              {titleOf(n) ?? `SDG ${n}`}
            </span>
          ))}
        </div>
      ) : (
        <p className="muted">Analyse a profile to see how your top role links to the SDGs.</p>
      )}

      <p className="sdg-label">All goals in the data</p>
      <div className="sdg-grid">
        {booting && [0, 1, 2].map(i => <div className="sdg-skeleton" key={i} />)}
        {mappings.map(s => {
          const linked = roleSdgs.includes(s.sdg)
          return (
            <article className={linked ? 'sdg-card on fade-in' : 'sdg-card fade-in'} key={s.sdg}>
              <div className="sdg-card-top">
                <SdgIcon n={s.sdg} size={56} />
                <div>
                  <p className="sdg-num">SDG {s.sdg}</p>
                  <p className="sdg-name">{s.title}</p>
                </div>
              </div>
              <p className="sdg-why">{s.rationale}</p>
              <div className="sdg-tags">
                {s.sdg === PRIMARY_SDG && <span className="sdg-tag primary">Primary target</span>}
                {linked && <span className="sdg-tag linked"><Check size={13} aria-hidden="true" />Linked to your path</span>}
                {!linked && topMatch && <span className="sdg-tag not">Not linked to your top match</span>}
              </div>
            </article>
          )
        })}
      </div>

      <p className="sdg-foot">
        SDG icons: © United Nations, from <a href="https://www.un.org/sustainabledevelopment/" target="_blank" rel="noopener noreferrer">un.org/sustainabledevelopment</a>.
      </p>
    </section>
  )
}