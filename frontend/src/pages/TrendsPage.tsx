import { useState } from 'react'
import { CalendarCheck, CalendarDays, ChevronDown, ChevronUp, MapPin, Tag } from 'lucide-react'
import { MarketSignalsOverview } from '../components/MarketSignals'
import type { Skill, TrendData, MarketSignalsResponse } from '../types'

const LIMIT = 6

export default function TrendsPage({ trend, skills, booting, marketSignals, marketLoading, marketError, onRefreshMarket }: {
  trend: TrendData | null
  skills: Skill[]
  booting: boolean
  marketSignals: MarketSignalsResponse | null
  marketLoading: boolean
  marketError: string
  onRefreshMarket: () => void
}) {
  const [showAll, setShowAll] = useState(false)
  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id
  const data = Object.entries(trend?.multipliers ?? {})
    .map(([id, value]) => ({ id, name: nameOf(id), value }))
    .sort((a, b) => b.value - a.value)
  const max = data.length ? Math.max(...data.map(d => d.value)) : 0
  const visible = showAll ? data : data.slice(0, LIMIT)

  return <section className="trend-evidence-page">
    {/* The sourced market evidence and its availability do not depend on synthetic trends. */}
    <MarketSignalsOverview snapshot={marketSignals} loading={marketLoading} error={marketError} onRetry={onRefreshMarket} />

    <section className="scenario-radar" aria-labelledby="scenario-radar-heading">
      <div className="trend-head">
        <div>
          <p className="market-eyebrow">TEAM-DEFINED MODEL · NOT DOSM DEMAND</p>
          <h2 id="scenario-radar-heading">Scenario simulation (synthetic)</h2>
          <p className="muted">Skill multipliers below are hypothetical team assumptions, not measured Malaysian job demand.</p>
        </div>
      </div>
      {booting && <div role="status">{[0, 1, 2].map(i => <div className="skeleton-row" key={i} />)}</div>}
      {!booting && !trend && <p className="muted">Synthetic scenario data is unavailable. The sourced occupation evidence above remains independent.</p>}
      {!booting && trend && <>
        <p className="trend-src">
          <span><Tag size={14} aria-hidden="true" />{trend.snapshot_id}</span>
          <span><CalendarDays size={14} aria-hidden="true" />Scenario observed {trend.observed_date}</span>
          <span><CalendarCheck size={14} aria-hidden="true" />Snapshot retrieved {trend.retrieved_date}</span>
          <span><MapPin size={14} aria-hidden="true" />{trend.region}</span>
        </p>
        {visible.map((d, i) => <div className="trend-row" key={d.id} title={`${d.name}: ${d.value}`}>
          <span>{d.name}</span>
          <div className="trend-track"><div className="trend-fill" style={{ width: `${max > 0 ? (d.value / max) * 100 : 0}%`, animationDelay: `${i * 0.05}s` }} /></div>
          <span className="trend-val">{d.value}</span>
        </div>)}
        {data.length > LIMIT && <div className="trend-more">
          <button type="button" onClick={() => setShowAll(!showAll)}>
            {showAll ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
            {showAll ? `Show top ${LIMIT}` : `Show all ${data.length}`}
          </button>
        </div>}
      </>}
    </section>
  </section>
}
