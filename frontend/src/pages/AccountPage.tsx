import { useEffect, useState } from 'react'
import { ArrowRight, BookMarked, CheckCircle2, ChevronRight, ClipboardList, CloudUpload, Database, Download, KeyRound, LockKeyhole, LogOut, Mail, ShieldCheck, Trash2, UserRound, X } from 'lucide-react'
import type { AnalyzeResponse, Career, Profile, RoadmapResponse } from '../types'
import { useAuth } from '../auth/AuthContext'
import { supabase } from '../lib/supabase'
import { useToast } from '../notifications/ToastProvider'
import UserAvatar from '../components/UserAvatar'
import {
  deleteAnalysis, deleteRoadmap, listAnalyses, listRoadmaps,
  loadProfile, saveAnalysis, saveProfile, saveRoadmap,
  type AnalysisRecord, type RoadmapRecord,
} from '../lib/accountData'

type Props = {
  name: string
  email: string
  avatarUrl?: string | null
  onSignOut: () => void
  profile: Profile
  targetRoleId: string
  careers: Career[]
  theme: 'light' | 'dark'
  matches: AnalyzeResponse | null
  roadmap: RoadmapResponse | null
  onRestoreProfile: (profile: Profile, role: string) => void
}

const dateLabel = (value: string) => new Date(value).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })

export default function AccountPage({
  name, email, avatarUrl, onSignOut, profile, targetRoleId, careers, theme,
  matches, roadmap, onRestoreProfile,
}: Props) {
  const auth = useAuth()
  const { notify } = useToast()
  const userId = auth.user?.id
  const provider = auth.user?.app_metadata?.provider
  const [displayName, setDisplayName] = useState(name)
  const [password, setPassword] = useState('')
  const [newEmail, setNewEmail] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleteInput, setDeleteInput] = useState('')
  const [analyses, setAnalyses] = useState<AnalysisRecord[]>([])
  const [roadmaps, setRoadmaps] = useState<RoadmapRecord[]>([])

  useEffect(() => { setDisplayName(name) }, [name])
  useEffect(() => {
    if (!userId) return
    let active = true
    void Promise.all([listAnalyses(userId), listRoadmaps(userId)])
      .then(([a, r]) => { if (active) { setAnalyses(a); setRoadmaps(r) } })
      .catch(() => {
        if (active) {
          const message = 'Saved history is unavailable. Confirm that the Supabase database migration has run.'
          setError(message); notify('error', message)
        }
      })
    return () => { active = false }
  }, [userId, notify])

  async function action(successMessage: string, callback: () => Promise<void>) {
    setBusy(true); setError(''); setStatus('')
    try {
      await callback()
      setStatus(successMessage)
      notify('success', successMessage)
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : 'Unable to complete that action.'
      setError(message)
      notify('error', message)
    } finally { setBusy(false) }
  }

  const refresh = async (id: string) => {
    const [a, r] = await Promise.all([listAnalyses(id), listRoadmaps(id)])
    setAnalyses(a); setRoadmaps(r)
  }
  const roleLabel = (id: string) => careers.find(role => role.id === id)?.title || id || 'Not chosen'

  if (!userId) return <section className="account-panel">
    <div className="account-intro"><span className="page-eyebrow">GUEST SESSION</span><h2>Explore without an account</h2><p className="muted">Your changes are kept only for this demo session.</p></div>
    <div className="card account-card account-hero">
      <div className="account-head"><UserAvatar name={name} size="large" /><div><h3>{name}</h3><p className="muted">Guest mode</p></div></div>
      <p>Create an account to securely save your education, selected skills, target career and learning roadmaps.</p>
      <button type="button" className="primary" onClick={onSignOut}>Go to sign in <ArrowRight size={17} aria-hidden="true" /></button>
    </div>
  </section>

  return <section className="account-panel">
    <div className="account-intro">
      <span className="page-eyebrow">YOUR WORKSPACE</span>
      <h2>Account & progress</h2>
      <p className="muted">Everything about your career journey, saved in one place.</p>
    </div>

    {error && <div className="account-message account-message--error" role="alert"><span>{error}</span><button type="button" aria-label="Dismiss error" onClick={() => setError('')}><X size={16} /></button></div>}
    {status && <div className="account-message account-message--success" role="status"><CheckCircle2 size={19} aria-hidden="true" /><span>{status}</span><button type="button" aria-label="Dismiss confirmation" onClick={() => setStatus('')}><X size={16} /></button></div>}

    <div className="account-hero card">
      <div className="account-hero-top">
        <div className="account-head">
          <UserAvatar name={name} imageUrl={avatarUrl} size="large" />
          <div className="account-identity"><h3>{name}</h3><p className="muted">{email}</p><span className="account-provider"><CheckCircle2 size={13} aria-hidden="true" /> Signed in {provider === 'google' ? 'with Google' : 'securely'}</span></div>
        </div>
        <span className="account-private"><ShieldCheck size={16} aria-hidden="true" /> Private account</span>
      </div>
      <div className="account-stats" aria-label="Saved progress summary">
        <div><strong>{profile.skills.length}</strong><span>Skills selected</span></div>
        <div><strong>{analyses.length}</strong><span>Saved analyses</span></div>
        <div><strong>{roadmaps.length}</strong><span>Saved roadmaps</span></div>
      </div>
    </div>

    <div className="account-grid">
      <div className="card account-card">
        <div className="account-section-heading"><UserRound size={20} aria-hidden="true" /><div><h3>Personal details</h3><p className="muted">Update how you appear in SkillShift.</p></div></div>
        <label className="form-label" htmlFor="account-name">Display name</label>
        <input className="text-field" id="account-name" maxLength={100} autoComplete="nickname"
          value={displayName} onChange={event => setDisplayName(event.target.value)} />
        <label className="form-label" htmlFor="account-email">Email address</label>
        <input className="text-field" id="account-email" value={email} disabled readOnly />
        <p className="muted field-hint">Your avatar is supplied by Google when available. Otherwise, your initials are displayed.</p>
        <div className="account-actions">
          <button type="button" className="primary" disabled={busy || !displayName.trim()} onClick={() => void action(
            'Profile saved. Your education, skills and target career are now stored securely.',
            async () => { await saveProfile(userId, displayName.trim(), profile, targetRoleId, theme); await auth.updateDisplayName(displayName.trim()) },
          )}><CloudUpload size={17} aria-hidden="true" /> {busy ? 'Please wait…' : 'Save my profile'}</button>
          <button type="button" disabled={busy} onClick={() => void action(
            'Saved profile restored. Your latest preferences are now active.',
            async () => {
              const saved = await loadProfile(userId)
              if (!saved) throw new Error('No saved profile found. Save your profile first.')
              onRestoreProfile({ education: saved.education, skills: saved.skills, interests: saved.interests }, saved.target_role)
              setDisplayName(saved.display_name)
            },
          )}><Download size={17} aria-hidden="true" /> Restore</button>
        </div>
      </div>

      <div className="card account-card">
        <div className="account-section-heading"><ClipboardList size={20} aria-hidden="true" /><div><h3>Career preferences</h3><p className="muted">Your current profile at a glance.</p></div></div>
        <div className="account-preference"><span>Education</span><strong>{profile.education || 'Not added'}</strong></div>
        <div className="account-preference"><span>Target career</span><strong>{roleLabel(targetRoleId)}</strong></div>
        <div className="account-preference"><span>Selected skills</span><strong>{profile.skills.length} skills</strong></div>
        <div className="account-preference"><span>Theme</span><strong>{theme === 'dark' ? 'Dark' : 'Light'}</strong></div>
        <div className="account-tip"><ShieldCheck size={18} aria-hidden="true" /><span>Only your signed-in account can read your saved profile when database policies are correctly configured.</span></div>
      </div>
    </div>

    <div className="card account-card account-wide">
      <div className="account-section-heading"><Database size={20} aria-hidden="true" /><div><h3>Saved career progress</h3><p className="muted">Keep your latest analysis and roadmap for future visits.</p></div></div>
      <div className="account-actions">
        <button type="button" disabled={busy || !matches} onClick={() => void action('Career analysis saved.', async () => {
          if (matches) { await saveAnalysis(userId, profile, targetRoleId, matches); await refresh(userId) }
        })}><ClipboardList size={17} aria-hidden="true" /> Save current analysis</button>
        <button type="button" disabled={busy || !roadmap} onClick={() => void action('Learning roadmap saved.', async () => {
          if (roadmap) { await saveRoadmap(userId, roadmap); await refresh(userId) }
        })}><BookMarked size={17} aria-hidden="true" /> Save current roadmap</button>
      </div>
      <div className="account-history-grid">
        <div className="account-history"><h4>Recent analyses <span className="count-pill">{analyses.length}</span></h4>
          {analyses.length === 0 && <p className="account-empty">No saved analyses yet. Run an analysis, then save it here.</p>}
          {analyses.map(item => <div className="account-row" key={item.id}>
            <div><strong>{roleLabel(item.target_role)}</strong><span>{item.scenario} scenario · {dateLabel(item.saved_at)}</span></div>
            <button className="account-delete-row" disabled={busy} type="button" aria-label={`Delete analysis saved ${dateLabel(item.saved_at)}`} onClick={() => void action('Analysis deleted.', async () => { await deleteAnalysis(userId, item.id); await refresh(userId) })}><Trash2 size={17} aria-hidden="true" /></button>
          </div>)}
        </div>
        <div className="account-history"><h4>Recent roadmaps <span className="count-pill">{roadmaps.length}</span></h4>
          {roadmaps.length === 0 && <p className="account-empty">No saved roadmaps yet. Generate a pathway, then save it here.</p>}
          {roadmaps.map(item => <div className="account-row" key={item.id}>
            <div><strong>{roleLabel(item.target_role)}</strong><span>{item.scenario} scenario · {dateLabel(item.saved_at)}</span></div>
            <button className="account-delete-row" disabled={busy} type="button" aria-label={`Delete roadmap saved ${dateLabel(item.saved_at)}`} onClick={() => void action('Roadmap deleted.', async () => { await deleteRoadmap(userId, item.id); await refresh(userId) })}><Trash2 size={17} aria-hidden="true" /></button>
          </div>)}
        </div>
      </div>
    </div>

    <div className="account-grid">
      <div className="card account-card">
        <div className="account-section-heading"><KeyRound size={20} aria-hidden="true" /><div><h3>Sign-in & security</h3><p className="muted">Manage credentials and recovery.</p></div></div>
        {auth.recovery && <div className="account-message account-message--success" role="status">Password recovery confirmed. Set a new password below.</div>}
        <label className="form-label" htmlFor="new-password">New password</label>
        <div className="account-password-wrap"><input className="text-field" id="new-password" type={showPassword ? 'text' : 'password'} autoComplete="new-password"
          minLength={8} value={password} onChange={event => setPassword(event.target.value)} placeholder="At least 8 characters" />
          <button type="button" onClick={() => setShowPassword(value => !value)} aria-label={showPassword ? 'Hide new password' : 'Show new password'}>{showPassword ? 'Hide' : 'Show'}</button>
        </div>
        <div className="account-actions">
          <button type="button" disabled={busy || password.length < 8} onClick={() => void action('Password updated successfully.', async () => { await auth.updatePassword(password); setPassword('') })}><LockKeyhole size={16} aria-hidden="true" /> Update password</button>
          <button type="button" disabled={busy} onClick={() => void action('Password reset instructions requested. Check your inbox.', async () => { await auth.resetPassword(email) })}><Mail size={16} aria-hidden="true" /> Send reset link</button>
        </div>
        <label className="form-label" htmlFor="new-email">Change email address</label>
        <input className="text-field" id="new-email" type="email" autoComplete="email" value={newEmail} onChange={event => setNewEmail(event.target.value)} placeholder="new@email.com" />
        <div className="account-actions"><button type="button" disabled={busy || !newEmail.includes('@')} onClick={() => void action('Email change requested. Check your inboxes to confirm.', async () => {
          const { error: changeError } = await supabase!.auth.updateUser({ email: newEmail.trim() })
          if (changeError) throw changeError
          setNewEmail('')
        })}>Request email change <ChevronRight size={16} aria-hidden="true" /></button></div>
      </div>

      <div className="card account-card">
        <div className="account-section-heading"><ShieldCheck size={20} aria-hidden="true" /><div><h3>Privacy & account</h3><p className="muted">You control your account and its data.</p></div></div>
        <p className="muted">Your saved data is scoped to your authenticated account with Supabase Row Level Security.</p>
        <button className="account-signout" type="button" disabled={busy} onClick={onSignOut}><LogOut size={17} aria-hidden="true" /> Sign out <ArrowRight size={16} aria-hidden="true" /></button>
        <div className="account-danger-zone">
          <h4>Danger zone</h4>
          <p className="muted">Deleting your account permanently removes its saved profiles, analyses and roadmaps.</p>
          {!confirmDelete ? <button type="button" className="auth-danger" onClick={() => setConfirmDelete(true)}><Trash2 size={16} aria-hidden="true" /> Delete my account</button> :
            <div className="account-confirm-delete">
              <label htmlFor="confirm-delete">Type <strong>DELETE</strong> to confirm</label>
              <input id="confirm-delete" className="text-field" autoComplete="off" value={deleteInput} onChange={event => setDeleteInput(event.target.value)} />
              <div className="account-actions"><button type="button" onClick={() => { setConfirmDelete(false); setDeleteInput('') }}>Cancel</button>
                <button type="button" className="auth-danger" disabled={busy || deleteInput !== 'DELETE'} onClick={() => void action('Account deleted.', async () => {
                  const { data } = await supabase!.auth.getSession()
                  const token = data.session?.access_token
                  if (!token) throw new Error('Please sign in again before deleting your account.')
                  const response = await fetch('/api/account/me', { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } })
                  if (!response.ok) {
                    if (response.status === 503) throw new Error('Account deletion is not enabled by the administrator.')
                    throw new Error('Account deletion failed. Please try again.')
                  }
                  await supabase!.auth.signOut({ scope: 'local' })
                  window.location.assign('/')
                })}>Delete permanently</button></div>
            </div>}
        </div>
      </div>
    </div>
  </section>
}
