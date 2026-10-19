import type { Profile, Skill } from '../types'
export default function ProfilePage({skills,profile,onChange,onAnalyze,loading}:{skills:Skill[];profile:Profile;onChange:(profile:Profile)=>void;onAnalyze:()=>void;loading:boolean}){
  return <section><h2>My Skills Profile</h2><p>Choose skills for a synthetic user. Do not enter real CVs or personal details.</p>
    <label>Education / Background <input value={profile.education} onChange={e=>onChange({...profile,education:e.target.value})}/></label>
    <div className="skills">{skills.map(s=><label key={s.id} className="skill"><input type="checkbox" checked={profile.skills.includes(s.id)} onChange={e=>onChange({...profile,skills:e.target.checked?[...profile.skills,s.id]:profile.skills.filter(id=>id!==s.id)})}/>{s.name}</label>)}</div>
    <button className="primary" onClick={onAnalyze} disabled={loading}>{loading?'Analyzing…':'Analyze Career Readiness'}</button>
  </section>
}
