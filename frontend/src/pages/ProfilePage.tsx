import { ArrowRight, Check, Loader2  } from 'lucide-react'
import type { Career, Profile, Skill } from '../types'

type Props = {
  skills: Skill[]
  careers: Career[]
  targetRoleId: string
  onSelectTarget: (roleId: string) => void
  profile: Profile
  onChange: (profile: Profile) => void
  onAnalyze: () => void
  loading: boolean
  booting: boolean
}

export default function ProfilePage({ skills, careers, targetRoleId, onSelectTarget, profile, onChange, onAnalyze, loading, booting }: Props) {
  const toggle = (id: string, on: boolean) =>
    onChange({ ...profile, skills: on ? [...profile.skills, id] : profile.skills.filter(s => s !== id) })

  return (
    <section>
      <h2>Build your skills profile</h2>
      <p className="muted">Choose skills for a synthetic user. Do not enter real CVs or personal details.</p>

      <div className="form-block">
        <label htmlFor="education" className="form-label">Education / background</label>
        <input
          id="education"
          className="text-field"
          value={profile.education}
          onChange={e => onChange({ ...profile, education: e.target.value })}
        />
      </div>

      <div className="form-block">
        <label htmlFor="target-career" className="form-label">Target career</label>
        <select id="target-career" className="text-field" value={targetRoleId} onChange={e => onSelectTarget(e.target.value)} disabled={booting}>
          <option value="">Choose a career (optional for matching)</option>
          {careers.map(role => <option key={role.id} value={role.id}>{role.title}</option>)}
        </select>
        <p className="muted field-hint">You can compare every career first and choose a target later.</p>
      </div>

      <div className="form-block">
        <div className="form-label-row">
          <span className="form-label">Your skills</span>
          {!booting && <span className="count-pill">{profile.skills.length} of {skills.length} selected</span>}
        </div>
        <div className="skill-grid">
          {booting && Array.from({ length: 8 }).map((_, i) => <span className="skill-skeleton" key={i} style={{ width: 80 + (i % 4) * 25 }} />)}
          {skills.map(s => {
            const on = profile.skills.includes(s.id)
            return (
              <label key={s.id} className={on ? 'skill-chip on' : 'skill-chip'}>
                <input type="checkbox" checked={on} onChange={e => toggle(s.id, e.target.checked)} />
                {on && <Check size={14} aria-hidden="true" />}
                {s.name}
              </label>
            )
          })}
        </div>
      </div>

      <div className="form-actions">
        <span className="muted">{profile.skills.length === 0 ? 'Pick a few skills to get started.' : 'Ready when you are.'}</span>
        <button type="button" className="primary" onClick={onAnalyze} disabled={loading}>
          {loading && <Loader2 size={16} className="spin" aria-hidden="true" />}
          {loading ? 'Analysing…' : 'Analyse my skills'}
          {!loading && <ArrowRight size={16} aria-hidden="true" />}
        </button>
      </div>
    </section>
  )
}