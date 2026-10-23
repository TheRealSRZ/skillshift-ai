import { useEffect, useState } from 'react'
import { ArrowDownRight, ArrowUpRight, Check, Gauge, Info, Star, Zap } from 'lucide-react'
import type { AnalyzeResponse } from '../types'

type Results = { moderate: AnalyzeResponse; rapid: AnalyzeResponse }

const round1 = (n: number) => Math.round(n * 10) / 10

export default function SimulatorPage({ results }: { results: Results | null }) {
  const [showVerdict, setShowVerdict] = useState(true)

  useEffect(() => {
    setShowVerdict(true)
    const timer = setTimeout(() => setShowVerdict(false), 5000)
    return () => clearTimeout(timer)
  }, [results])

  const topM = results?.moderate.matches[0]
  const topR = results?.rapid.matches[0]

  if (!results || !topM || !topR) {
    return (
      <section>
        <h2>Future scenario simulator</h2>
        <p className="muted">Analyse a profile to compare both scenarios.</p>
      </section>
    )
  }

  const same = topM.role_id === topR.role_id
  const gapDiff = round1(topR.readiness_score - topM.readiness_score)
  const gapText = !same ? 'different top roles' : gapDiff === 0 ? 'no change' : `${Math.abs(gapDiff)} ${gapDiff < 0 ? 'lower' : 'higher'}`

  const rapidScore = (id: string) => results.rapid.matches.find(m => m.role_id === id)?.readiness_score
  const rows = results.moderate.matches.map(m => ({ id: m.role_id, title: m.title, mod: m.readiness_score, rap: rapidScore(m.role_id) }))
  const disclaimers = Array.from(new Set([results.moderate.scenario_disclaimer, results.rapid.scenario_disclaimer].filter(Boolean)))

  return (
    <section>
      <div className="sim-top">
        <div>
          <h2 className="intro-title">
            <span className="intro-w">Does</span>{' '}
            <span className="intro-w">your</span>{' '}
            <span className="intro-w">best</span>{' '}
            <span className="intro-w">match</span>{' '}
            <span className="intro-chip" aria-hidden="true">✦</span>{' '}
            <b className="intro-w"><span className="intro-hl">hold up?</span></b>
          </h2>
          <div className="intro-pills">
            <span className="intro-pill">Moderate and Rapid are hypothetical AI adoption scenarios, not forecasts. Rapid is compared with Moderate.</span>
          </div>
        </div>
        {!showVerdict && (
          <span className={same ? 'verdict-pill' : 'verdict-pill warn'}>
            {same ? <Check size={14} aria-hidden="true" /> : <Info size={14} aria-hidden="true" />}
            {same ? 'Top match unchanged' : 'Top match changes'}
          </span>
        )}
      </div>

      <div className={`verdict ${same ? 'ok' : 'warn'}${showVerdict ? '' : ' hide'}`} role="status" aria-hidden={!showVerdict}>
        {same ? <Check size={20} aria-hidden="true" /> : <Info size={20} aria-hidden="true" />}
        <span>
          {same
            ? <><strong>Top match unchanged.</strong> {topM.title} is your best fit in both scenarios.</>
            : <><strong>Top match changes under Rapid.</strong> {topM.title} becomes {topR.title}.</>}
        </span>
      </div>

      <div className="sim-tiles">
        <div className="sim-tile m">
          <span className="sim-ic m"><Gauge size={20} aria-hidden="true" /></span>
          <div>
            <p className="sim-tl">Moderate AI adoption</p>
            <p className="sim-tv m">{topM.readiness_score}%</p>
            <p className="sim-ts">{topM.title}</p>
          </div>
        </div>
        <div className="sim-gap">{gapText}</div>
        <div className="sim-tile r">
          <span className="sim-ic r"><Zap size={20} aria-hidden="true" /></span>
          <div>
            <p className="sim-tl">Rapid AI adoption</p>
            <p className="sim-tv r">{topR.readiness_score}%</p>
            <p className="sim-ts">{topR.title}</p>
          </div>
        </div>
      </div>

      <div className="sim-card">
        <div className="sim-card-head">
          <h3>All roles, side by side</h3>
          <div className="sim-legend"><span className="a">Moderate</span><span className="b">Rapid</span></div>
        </div>
        <p className="sim-hint">The tag shows how much a score changed under Rapid.</p>

        {rows.map((row, i) => {
          const delay = `${i * 0.1}s`
          const delta = row.rap === undefined ? null : round1(row.rap - row.mod)
          return (
            <div className="sim-row" key={row.id}>
              <span className="sim-name">
                <span className="sim-name-line">
                  {row.title}
                  {row.id === topM.role_id && row.mod > 0 && <Star size={15} aria-label="Top match" />}
                </span>
                <small>{row.mod}%{row.rap !== undefined ? ` → ${row.rap}%` : ''}</small>
              </span>
              <div className="sim-bars">
                <div className="sim-track"><div className="sim-f1" style={{ width: `${Math.min(100, row.mod)}%`, animationDelay: delay }} /></div>
                <div className="sim-track">
                  {row.rap !== undefined && <div className="sim-f2" style={{ width: `${Math.min(100, row.rap)}%`, animationDelay: delay }} />}
                </div>
              </div>
              <span className="sim-delta">
                {delta === null ? <span className="sim-nc">n/a</span>
                  : delta === 0 ? <span className="sim-nc">no change</span>
                  : <span className={delta < 0 ? 'sim-tag down' : 'sim-tag up'}>
                      {delta < 0 ? <ArrowDownRight size={13} aria-hidden="true" /> : <ArrowUpRight size={13} aria-hidden="true" />}
                      {Math.abs(delta)}
                    </span>}
              </span>
            </div>
          )
        })}

        {disclaimers.length > 0 && (
          <div className="sim-dis">
            <Info size={15} aria-hidden="true" />
            <span>{disclaimers.join(' ')}</span>
          </div>
        )}
      </div>
    </section>
  )
}