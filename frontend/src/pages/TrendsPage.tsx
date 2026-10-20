import { useState } from 'react'
import { CalendarCheck, CalendarDays, ChevronDown, ChevronUp, MapPin, Tag } from 'lucide-react'
import type { Skill, TrendData } from '../types'

const LIMIT = 6

export default function TrendsPage({ trend, skills }: { trend: TrendData | null; skills: Skill[] }) {
  const [showAll, setShowAll] = useState(false)
  const nameOf = (id: string) => skills.find(s => s.id === id)?.name ?? id

  if (!trend) {
    return (
      <section>
        <h2>Future skills radar</h2>
        <p className="muted">Trend data unavailable.</p>
      </section>
    )
  }

  const data = Object.entries(trend.multipliers)
    .map(([id, value]) => ({ id, name: nameOf(id), value }))
    .sort((a, b) => b.value - a.value)
  const max = data.length ? Math.max(...data.map(d => d.value)) : 0
  const visible = showAll ? data : data.slice(0, LIMIT)

  return (
    <section>
      <div className="trend-head">
        <div>
          <h2>Future skills radar</h2>
          <p className="muted">{trend.label}</p>
        </div>
      </div>

      <p className="trend-src">
        <span><Tag size={14} aria-hidden="true" />{trend.snapshot_id}</span>
        <span><CalendarDays size={14} aria-hidden="true" />Observed {trend.observed_date}</span>
        <span><CalendarCheck size={14} aria-hidden="true" />Retrieved {trend.retrieved_date}</span>
        <span><MapPin size={14} aria-hidden="true" />{trend.region}</span>
      </p>

      {visible.map((d, i) => (
        <div className="trend-row" key={d.id} title={`${d.name}: ${d.value}`}>
          <span>{d.name}</span>
          <div className="trend-track">
            <div className="trend-fill" style={{ width: `${max > 0 ? (d.value / max) * 100 : 0}%`, animationDelay: `${i * 0.05}s` }} />
          </div>
          <span className="trend-val">{d.value}</span>
        </div>
      ))}

      {data.length > LIMIT && (
        <div className="trend-more">
          <button type="button" onClick={() => setShowAll(!showAll)}>
            {showAll ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
            {showAll ? `Show top ${LIMIT}` : `Show all ${data.length}`}
          </button>
        </div>
      )}
    </section>
  )
}