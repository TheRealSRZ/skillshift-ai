import { useState } from 'react'
import type { AnalyzeResponse, Match, Skill, MarketSignalsResponse } from '../types'
import { CareerMarketSignal } from '../components/MarketSignals'

type SdgInfo = { sdg: number; title: string }

const SHOW_MISSING = 2

function RoleCard({ role, isTop, isTarget, nameOf, sdgs, onSelect, onOpenRoadmap, marketSignals, marketLoading, marketError }: { role: Match; marketSignals: MarketSignalsResponse | null; marketLoading: boolean; marketError: string; isTop: boolean; isTarget: boolean; nameOf: (id: string) => string; sdgs: SdgInfo[]; onSelect: () => void; onOpenRoadmap: () => void }) {
  const [expanded, setExpanded] = useState(false)
  const missing = expanded ? role.missing_skills : role.missing_skills.slice(0, SHOW_MISSING)
  const hidden = role.missing_skills.length - SHOW_MISSING
  const roleSdgs = role.sdgs ?? []

  return (
    <article className={isTarget ? 'role-card target' : isTop ? 'role-card top' : 'role-card'}>
      <div className="role-head">
        <h3>{role.title}</h3>
        <div className="role-badges">
          {isTop && <span className="top-badge">Top match</span>}
          {isTarget && <span className="target-badge">Your target</span>}
        </div>
      </div>

      <div className="score-row">
        <strong className="score-val">{role.readiness_score}%</strong>
        <div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, role.readiness_score)}%` }} /></div>
      </div>

      <div className="role-actions">
        <button type="button" className={isTarget ? 'target-selected-btn' : 'role-select-btn'} onClick={onSelect} aria-pressed={isTarget}>
          {isTarget ? '✓ Selected target' : 'Choose this career'}
        </button>
        {isTarget && <button type="button" className="link-btn" onClick={onOpenRoadmap}>View roadmap →</button>}
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
      <CareerMarketSignal careerId={role.role_id} snapshot={marketSignals} loading={marketLoading} error={marketError} />
    </article>
  )
}

export default function CareersPage({ results, skills, sdgs, selectedRoleId, onSelectRole, onOpenRoadmap, marketSignals, marketLoading, marketError, onRefreshMarket }: { results: AnalyzeResponse | null; marketSignals: MarketSignalsResponse | null; marketLoading: boolean; marketError: string; onRefreshMarket: () => void; skills: Skill[]; sdgs: SdgInfo[]; selectedRoleId: string; onSelectRole: (roleId: string) => void; onOpenRoadmap: () => void }) {
  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id

  return (
    <section>
      <h2>Career matches and skill gaps</h2>
      <p className="muted section-lead">Select the career you want to pursue. The highest score is only a suggestion.</p>
      <div className="market-careers-toolbar">
        <span>Career-readiness scores and DOSM job-market observations measure different things.</span>
        <button type="button" className="market-refresh" onClick={onRefreshMarket} disabled={marketLoading}>
          {marketLoading ? 'Loading market data…' : 'Refresh DOSM evidence'}
        </button>
      </div>
      {marketError && <div className="market-api-error" role="alert">
        Market evidence is temporarily unavailable. Career matching remains usable.
        <button type="button" onClick={onRefreshMarket}>Retry market evidence</button>
      </div>}
      {results?.matches.length ? (
        <>
          <div className="role-grid">
            {results.matches.map((r, i) => (
              <RoleCard key={r.role_id} role={r} isTop={i === 0 && r.readiness_score > 0} isTarget={r.role_id === selectedRoleId} nameOf={nameOf} sdgs={sdgs} onSelect={() => onSelectRole(r.role_id)} onOpenRoadmap={onOpenRoadmap} marketSignals={marketSignals} marketLoading={marketLoading} marketError={marketError} />
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