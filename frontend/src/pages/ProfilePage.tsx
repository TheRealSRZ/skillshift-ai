import { ArrowRight, Check, CircleHelp, CloudUpload, GraduationCap, Loader2, Search, ShieldCheck, Sparkles, Target } from 'lucide-react'
import { useMemo, useState } from 'react'
import UserAvatar from '../components/UserAvatar'
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
  userName: string
  avatarUrl?: string | null
  authenticated: boolean
  onSave: () => void
  saving: boolean
}

export default function ProfilePage({ skills, careers, targetRoleId, onSelectTarget, profile, onChange, onAnalyze, loading, booting, userName, avatarUrl, authenticated, onSave, saving }: Props) {
  const [query, setQuery] = useState('')
  const visibleSkills = useMemo(() => skills.filter(skill => skill.name.toLowerCase().includes(query.trim().toLowerCase())), [skills, query])
  const targetCareer = careers.find(role => role.id === targetRoleId)
  const toggle = (id: string, on: boolean) =>
    onChange({ ...profile, skills: on ? [...profile.skills, id] : profile.skills.filter(skill => skill !== id) })

  return <section className="profile-workspace">
    <div className="profile-hero">
      <div className="profile-hero-user">
        <UserAvatar name={userName} imageUrl={avatarUrl} size="large" />
        <div><span className="page-eyebrow">CAREER READINESS PROFILE</span><h2>Make your next move, {userName.split(' ')[0]}</h2>
          <p>Tell us about your background and skills. We'll map your strengths to career paths.</p></div>
      </div>
      <span className="profile-state"><ShieldCheck size={16} aria-hidden="true" />{authenticated ? 'Private profile' : 'Guest demo'}</span>
    </div>

    <div className="profile-summary" aria-label="Profile completeness">
      <div><GraduationCap size={18} aria-hidden="true" /><span>Background</span><strong>{profile.education.trim() ? 'Added' : 'Not set'}</strong></div>
      <div><Sparkles size={18} aria-hidden="true" /><span>Skills selected</span><strong>{profile.skills.length} of {skills.length}</strong></div>
      <div><Target size={18} aria-hidden="true" /><span>Target career</span><strong>{targetCareer?.title || 'Exploring'}</strong></div>
    </div>

    <div className="profile-section card">
      <div className="profile-section-title"><span className="profile-section-icon"><GraduationCap size={21} aria-hidden="true" /></span><div><h3>Education & background</h3><p className="muted">A short description helps you keep track of where you're starting from.</p></div></div>
      <label htmlFor="education" className="form-label">Your current background</label>
      <input id="education" className="text-field" maxLength={200} placeholder="e.g. Diploma in Computer Science"
        value={profile.education} onChange={event => onChange({ ...profile, education: event.target.value })}/>
    </div>

    <div className="profile-section card">
      <div className="profile-section-title"><span className="profile-section-icon"><Target size={21} aria-hidden="true" /></span><div><h3>Target career</h3><p className="muted">Pick a direction now or compare matches first. You can switch later.</p></div></div>
      <label htmlFor="target-career" className="form-label">Career you're interested in</label>
      <select id="target-career" className="text-field" value={targetRoleId} onChange={event => onSelectTarget(event.target.value)} disabled={booting}>
        <option value="">Explore all careers first</option>
        {careers.map(role => <option key={role.id} value={role.id}>{role.title}</option>)}
      </select>
      <p className="muted field-hint"><CircleHelp size={14} aria-hidden="true" /> Your target only changes which roadmap you generate; you can still compare every career.</p>
    </div>

    <div className="profile-section card">
      <div className="profile-section-title"><span className="profile-section-icon"><Sparkles size={21} aria-hidden="true" /></span><div><h3>Skills you already have</h3><p className="muted">Select your current skills. Your choices directly affect readiness scores.</p></div></div>
      <div className="profile-skill-tools">
        <div className="profile-search"><Search size={17} aria-hidden="true" /><input aria-label="Search skills" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search skills…" /></div>
        <span className="count-pill">{profile.skills.length} selected</span>
      </div>
      <div className="skill-grid" aria-label="Skills checklist">
        {booting && Array.from({ length: 8 }).map((_, index) => <span className="skill-skeleton" key={index} style={{ width: 80 + (index % 4) * 25 }} />)}
        {visibleSkills.map(skill => {
          const on = profile.skills.includes(skill.id)
          return <label key={skill.id} className={on ? 'skill-chip on' : 'skill-chip'}>
            <input type="checkbox" checked={on} onChange={event => toggle(skill.id, event.target.checked)} />
            {on && <Check size={14} aria-hidden="true" />}
            {skill.name}
          </label>
        })}
      </div>
      {!booting && visibleSkills.length === 0 && <p className="account-empty">No skills match “{query}”. Try a different search.</p>}
      {profile.skills.length > 0 && <button type="button" className="link-btn profile-clear" onClick={() => onChange({ ...profile, skills: [] })}>Clear selected skills</button>}
    </div>

    <div className="profile-bottom-bar">
      <div><strong>{profile.skills.length ? 'Ready to explore careers?' : 'Start by selecting some skills'}</strong>
        <p className="muted">{authenticated ? 'Save your profile to keep these choices across visits.' : 'Guest progress is temporary. Sign in to save it.'}</p>
      </div>
      <div className="profile-bottom-actions">
        {authenticated && <button type="button" className="profile-save" onClick={onSave} disabled={saving || loading}>
          {saving ? <Loader2 className="spin" size={17} aria-hidden="true" /> : <CloudUpload size={17} aria-hidden="true" />}{saving ? 'Saving…' : 'Save progress'}</button>}
        <button type="button" className="primary" onClick={onAnalyze} disabled={loading || booting}>
          {loading ? <Loader2 size={17} className="spin" aria-hidden="true" /> : <Sparkles size={17} aria-hidden="true" />}
          {loading ? 'Analysing…' : 'Analyse my skills'}
          {!loading && <ArrowRight size={17} aria-hidden="true" />}
        </button>
      </div>
    </div>
  </section>
}
