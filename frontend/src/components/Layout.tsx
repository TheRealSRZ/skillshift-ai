import type { ReactNode } from 'react'
const tabs = ['Profile', 'Trends', 'Careers', 'Simulator', 'Roadmap', 'SDG Impact'] as const
export type Tab = typeof tabs[number]
export default function Layout({active,onSelect,children}:{active:Tab;onSelect:(tab:Tab)=>void;children:ReactNode}){
  return <div className="shell"><header><h1>SkillShift AI</h1><p>Future skills · Education · Career readiness</p></header>
    <nav aria-label="Application sections">{tabs.map(t=><button type="button" key={t} className={t===active?'selected':''} onClick={()=>onSelect(t)}>{t}</button>)}</nav>
    <main>{children}</main><footer>SYNTHETIC DEMO DATA — Not validated Malaysian market trends. Scores are not employment probabilities.</footer>
  </div>
}
