import type { ReactNode } from 'react'
import { ArrowRight, BrainCircuit, CheckCircle2, Cloud, Code2, DatabaseZap, LockKeyhole, Sparkles, WandSparkles } from 'lucide-react'
import type { Scenario } from '../types'

export const careerIcon=(id:string)=>{
  if(id.includes('data'))return DatabaseZap
  if(id.includes('cloud'))return Cloud
  if(id.includes('security'))return LockKeyhole
  return Code2
}
export const careerTone=(id:string)=>id.includes('data')?'mint':id.includes('security')?'violet':id.includes('cloud')?'blue':'amber'
export function ScenarioSwitch({value,onChange}:{value:Scenario;onChange:(value:Scenario)=>void}){
  return <div className="scenario-switch" role="group" aria-label="AI adoption scenario">
    <button className={value==='moderate'?'scenario-active':''} aria-pressed={value==='moderate'} onClick={()=>onChange('moderate')} type="button"><BrainCircuit size={15}/> Moderate</button>
    <button className={value==='rapid'?'scenario-active':''} aria-pressed={value==='rapid'} onClick={()=>onChange('rapid')} type="button"><Sparkles size={15}/> Rapid AI</button>
  </div>
}
export function ProgressBar({value,tone='mint'}:{value:number;tone?:string}){
  return <div className="progress-track" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}><div className={`progress-fill tone-${tone}`} style={{width:`${Math.max(0,Math.min(100,value))}%`}}/></div>
}
export function SectionTitle({eyebrow,title,side}:{eyebrow:string;title:string;side?:ReactNode}){
  return <div className="section-heading"><div><p className="section-kicker">{eyebrow}</p><h2>{title}</h2></div>{side}</div>
}
export function EmptyPanel({title,description,onAction,action}:{title:string;description:string;onAction?:()=>void;action?:string}){
  return <div className="empty-panel"><div className="empty-art"><WandSparkles size={31}/></div><h3>{title}</h3><p>{description}</p>{onAction&&<button className="btn btn-primary" type="button" onClick={onAction}>{action??'Get started'} <ArrowRight size={17}/></button>}</div>
}
export function StatusIcon({ready}:{ready:boolean}){return ready?<CheckCircle2 size={15}/>:<Sparkles size={15}/>}
