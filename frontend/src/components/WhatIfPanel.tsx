import { useEffect, useRef, useState } from 'react'
import { ArrowRight, RotateCcw, Sparkles } from 'lucide-react'
import { api } from '../api/client'
import type { Match, Profile, Skill, WhatIfResponse } from '../types'

type Props = { role: Match; profile: Profile; skills: Skill[] }

export default function WhatIfPanel({ role, profile, skills }: Props) {
  const [selected, setSelected] = useState<string[]>([])
  const [result, setResult] = useState<WhatIfResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const seq = useRef(0)
  const nameOf = (id: string) => skills.find(skill => skill.id === id)?.name ?? id

  // Switching careers or rerunning analysis must never show results from an old profile.
  useEffect(() => {
    seq.current += 1
    setSelected([]); setResult(null); setError(''); setLoading(false)
    return () => { seq.current += 1 }
  }, [role.role_id, profile])
  const toggle = (id: string) => {
    setSelected(prev => prev.includes(id) ? prev.filter(item => item !== id) : prev.length < 5 ? [...prev, id] : prev)
    setResult(null)
    setError('')
    seq.current += 1
    setLoading(false)
  }
  const preview = async () => {
    if (!selected.length || loading) return
    const ticket = ++seq.current
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const response = await api.whatIf(profile, role.role_id, selected)
      // Don't let stale results overwrite a new selection/role.
      if (ticket === seq.current) { setResult(response); setLoading(false) }
    } catch {
      if (ticket === seq.current) { setError('Unable to calculate the preview. Please retry.'); setLoading(false) }
    }
  }
  return (
    <section className="what-if-panel" aria-labelledby="what-if-title">
      <div className="what-if-header">
        <div>
          <h3 id="what-if-title"><Sparkles size={18} aria-hidden="true" /> Explore your next skill</h3>
          <p className="muted">What if you learned one or more missing skills for <strong>{role.title}</strong>?</p>
        </div>
        <span className="what-if-tag">No AI credits needed</span>
      </div>
      {role.missing_skills.length ? <>
        <p className="muted what-if-label">Choose up to five skills to simulate:</p>
        <div className="what-if-choices" role="group" aria-label="Skills to simulate">
          {role.missing_skills.map(id => <button key={id} type="button" aria-pressed={selected.includes(id)}
            className={selected.includes(id) ? 'what-if-choice selected' : 'what-if-choice'}
            disabled={!selected.includes(id) && selected.length >= 5}
            onClick={() => toggle(id)}>{selected.includes(id) ? '✓ ' : '+ '}{nameOf(id)}</button>)}
        </div>
        <div className="what-if-actions">
          <button className="primary-btn" type="button" disabled={!selected.length || loading} onClick={() => void preview()}>
            {loading ? 'Calculating…' : 'Preview readiness'} <ArrowRight size={15} aria-hidden="true" />
          </button>
          <button className="what-if-reset" type="button" disabled={!selected.length && !result} onClick={() => {setSelected([]);setResult(null);setError('');seq.current += 1;setLoading(false)}}>
            <RotateCcw size={14} aria-hidden="true"/> Reset
          </button>
        </div>
        {error && <p role="alert" className="what-if-error">{error}</p>}
        {result && !loading && <div className="what-if-result" role="status" aria-live="polite">
          <span>Current: <strong>{result.original_readiness}%</strong></span>
          <ArrowRight size={19} aria-hidden="true" />
          <span>Hypothetical: <strong>{result.hypothetical_readiness}%</strong></span>
          <span className="what-if-delta">+{result.delta_points} points</span>
        </div>}
        {result && <p className="muted what-if-note">{result.note}</p>}
      </> : <p className="muted">You already have all the listed skills for this career.</p>}
    </section>
  )
}
