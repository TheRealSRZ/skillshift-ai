import { useState } from 'react'
import type { AnalyzeResponse, Match, Skill, MarketSignalsResponse } from '../types'
import { CareerMarketSignal } from '../components/MarketSignals'

type SdgInfo = { sdg: number; title: string }

const SHOW_MISSING = 2

function RoleCard({ role, isTop, isTarget, nameOf, sdgs, onSelect, onOpenRoadmap, marketSignals, marketLoading, marketError }: { role: Match; marketSignals: MarketSignalsResponse | null; marketLoading: boolean; marketError: string; isTop: boolean; isTarget: boolean; nameOf: (id: string) => string; sdgs: SdgInfo[]; onSelect: () => void; onOpenRoadmap: () => void }) {
  const [expanded, setExpanded] = useState(false)
  const [marketOpen, setMarketOpen] = useState(false)
  const [marketHover, setMarketHover] = useState(false)
  const showMarket = marketOpen || marketHover
  const missing = expanded ? role.missing_skills : role.missing_skills.slice(0, SHOW_MISSING)
  const hidden = role.missing_skills.length - SHOW_MISSING
  const roleSdgs = role.sdgs ?? []

  return (
    <article className={isTarget ? 'role-card target' : isTop ? 'role-card top' : 'role-card'} onClick={e => { if (!(e.target as HTMLElement).closest('button')) onSelect() }}>
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

      <div className={`market-fold${showMarket ? ' open' : ''}${marketOpen ? ' pinned' : ''}`} onMouseEnter={() => setMarketHover(true)} onMouseLeave={() => setMarketHover(false)}>
        <button type="button" className="market-fold-head" onClick={() => setMarketOpen(!marketOpen)} aria-expanded={showMarket} aria-pressed={marketOpen} title={marketOpen ? 'Unpin' : 'Pin open'}>
          <span>Malaysia job-market context</span>
          <span className="market-fold-icons">
            <span className="market-fold-pin" aria-hidden="true">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="17" x2="12" y2="22" /><path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V6h1a2 2 0 0 0 0-4H8a2 2 0 0 0 0 4h1v4.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24Z" /></svg>
            </span>
            <span className="market-fold-arrow" aria-hidden="true">⌄</span>
          </span>
        </button>
        <div className="market-fold-body">
          <div className="market-fold-inner">
            <CareerMarketSignal careerId={role.role_id} snapshot={marketSignals} loading={marketLoading} error={marketError} />
          </div>
        </div>
      </div>
    </article>
  )
}

export default function CareersPage({ results, skills, sdgs, selectedRoleId, onSelectRole, onOpenRoadmap, marketSignals, marketLoading, marketError, onRefreshMarket }: { results: AnalyzeResponse | null; marketSignals: MarketSignalsResponse | null; marketLoading: boolean; marketError: string; onRefreshMarket: () => void; skills: Skill[]; sdgs: SdgInfo[]; selectedRoleId: string; onSelectRole: (roleId: string) => void; onOpenRoadmap: () => void }) {
  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id

  return (
    <section>
      <h2 className="intro-title">
        <span className="intro-w">Career</span>{' '}
        <span className="intro-w">matches</span>{' '}
        <span className="intro-chip" aria-hidden="true">✦</span>{' '}
        <span className="intro-w">and</span>{' '}
        <b className="intro-w"><span className="intro-hl">skill gaps</span></b>
      </h2>
      <button type="button" className="market-refresh" onClick={onRefreshMarket} disabled={marketLoading}>
        {marketLoading ? 'Loading market data…' : 'Refresh DOSM evidence'}
      </button>
      <div className="intro-pills">
        <span className="intro-pill">Select the career you want to pursue.</span>
        <span className="intro-pill">The highest score is only a suggestion.</span>
        <span className="intro-pill lime">Career-readiness scores and DOSM job-market observations measure different things.</span>
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