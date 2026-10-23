import { ArrowDownRight, ArrowUpRight, ExternalLink, Info, RefreshCcw } from 'lucide-react'
import type { MarketSignal, MarketSignalsResponse } from '../types'

const formatCount = (value: number) => new Intl.NumberFormat('en-MY').format(value)
const formatChange = (value: number) => `${value > 0 ? '+' : ''}${value.toFixed(2)}%`

function EvidenceSources({ urls }: { urls: string[] }) {
  const safeUrls = urls.filter(url => /^https:\/\//i.test(url))
  if (safeUrls.length === 0) return null
  return <span className="market-source-links">
    {safeUrls.map((url, index) => (
      <a key={url} href={url} target="_blank" rel="noopener noreferrer" title={`Open original DOSM source ${index + 1}`}>
        DOSM {index + 1} <ExternalLink size={12} aria-hidden="true" />
      </a>
    ))}
  </span>
}

function Availability({ signal }: { signal: MarketSignal }) {
  if (signal.data_status === 'insufficient_data') {
    return <div className="market-unavailable">
      <span className="market-status market-status--unavailable">Insufficient comparable data</span>
      <p>{signal.availability_note}</p>
      <p className="muted">This does not mean zero demand, zero growth or no job opportunities.</p>
    </div>
  }
  return <div className="market-observation">
    <div className="market-change-line">
      {signal.percent_change < 0 ? <ArrowDownRight size={19} aria-hidden="true" /> : signal.percent_change > 0 ? <ArrowUpRight size={19} aria-hidden="true" /> : <Info size={18} aria-hidden="true" />}
      <strong>{formatChange(signal.percent_change)}</strong>
      <span className="market-status">Observed {signal.previous_period} → {signal.latest_period}</span>
    </div>
    <div className="market-counts">
      <span><small>{signal.previous_period}</small><strong>{formatCount(signal.previous_job_offerings)}</strong></span>
      <span aria-hidden="true">→</span>
      <span><small>{signal.latest_period}</small><strong>{formatCount(signal.latest_job_offerings)}</strong></span>
    </div>
    <EvidenceSources urls={signal.source_urls} />
  </div>
}

/** Per-career evidence; never presented as readiness, automation risk or a demand forecast. */
export function CareerMarketSignal({ careerId, snapshot, loading, error }: {
  careerId: string
  snapshot: MarketSignalsResponse | null
  loading: boolean
  error: string
}) {
  const signal = snapshot?.career_signals.find(item => item.career_id === careerId)
  return <div className="market-inline">
    <div className="market-card">
      <div className="market-inline-head">
        <strong>Malaysia job-market context</strong>
        <span className="market-source-tag">DOSM · occupation-level</span>
      </div>
      {loading ? <p className="muted" role="status">Loading occupation evidence…</p>
        : error ? <p className="muted">Market evidence is temporarily unavailable. Skill-readiness scores are unaffected.</p>
        : !signal ? <p className="muted">No curated DOSM occupation comparison for this demo career.</p>
        : <Availability signal={signal} />}
    </div>
    <p className="market-fineprint">Online job offerings, not unique vacancies, a forecast, AI impact or hiring probability. Does not change readiness.</p>
  </div>
}

export function MarketSignalsOverview({ snapshot, loading, error, onRetry }: {
  snapshot: MarketSignalsResponse | null
  loading: boolean
  error: string
  onRetry: () => void
}) {
  return <div className="market-overview" aria-labelledby="market-signals-title">
    <div className="market-overview-head">
      <div>
        <p className="market-eyebrow">OFFICIAL SOURCE CONTEXT · MALAYSIA</p>
        <h2 id="market-signals-title" className="intro-title"><span className="intro-w">Career-specific</span>{' '}<b className="intro-w"><span className="intro-hl">job-offering</span></b>{' '}<span className="intro-w">comparisons</span></h2>
        <p className="muted">DOSM occupation-level observations, {snapshot ? snapshot.periods.join(' vs ') : 'most recent saved periods'}. Not skill-demand estimates.</p>
      </div>
      <button className="market-refresh" type="button" onClick={onRetry} disabled={loading} aria-label="Refresh latest saved market evidence">
        <RefreshCcw size={15} className={loading ? 'market-spin' : ''} aria-hidden="true" />
        {loading ? 'Refreshing…' : 'Refresh evidence'}
      </button>
    </div>
    {error && <div className="market-api-error" role="alert">
      Market observations could not be loaded. You can still use career analysis and learning roadmaps.
      <button type="button" onClick={onRetry}>Retry</button>
    </div>}
    {!error && loading && !snapshot && <p className="muted market-loading" role="status">Loading verified DOSM market observations…</p>}
    {!error && !loading && !snapshot && <p className="muted">No market snapshot has been loaded.</p>}
    {!error && snapshot && <>
      <div className="market-summary-strip">
        <span><strong>{snapshot.observed_count}</strong> careers with observed comparisons</span>
        <span><strong>{snapshot.insufficient_data_count}</strong> with insufficient data</span>
        <span>Snapshot: <strong>{snapshot.snapshot_id}</strong></span>
      </div>
      <div className="market-career-grid">
        {snapshot.career_signals.map(signal => <article key={signal.career_id} className="market-career-item">
          <h3>{signal.career_title}</h3>
          <Availability signal={signal} />
        </article>)}
      </div>
      <div className="market-context-note">
        <Info size={17} aria-hidden="true" />
        <p>Changes describe reported online job offerings across two quarters. They are not unique vacancies, an employment forecast, evidence of AI-caused displacement, or probabilities of getting hired. No market signal is used as a skill multiplier.</p>
      </div>
      <details className="market-method">
        <summary>Data limitations and methodology</summary>
        <p>{snapshot.method}. Snapshot generated {snapshot.generated_date}; data periods {snapshot.periods.join(' → ')}.</p>
        <ul>{snapshot.limitations.map(item => <li key={item}>{item}</li>)}</ul>
      </details>
    </>}
  </div>
}
