import type { ReactNode } from 'react'
import { BarChart3, Briefcase, Globe, Route, SlidersHorizontal, User } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

const tabs = ['Profile', 'Trends', 'Careers', 'Simulator', 'Roadmap', 'SDG Impact'] as const
export type Tab = typeof tabs[number]

const icons: Record<Tab, LucideIcon> = {
  Profile: User,
  Trends: BarChart3,
  Careers: Briefcase,
  Simulator: SlidersHorizontal,
  Roadmap: Route,
  'SDG Impact': Globe,
}

export default function Layout({ active, onSelect, children }: { active: Tab; onSelect: (tab: Tab) => void; children: ReactNode }) {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">SkillShift AI</div>
        <nav aria-label="Application sections">
          {tabs.map(t => {
            const Icon = icons[t]
            return (
              <button type="button" key={t} className={t === active ? 'nav-item selected' : 'nav-item'} onClick={() => onSelect(t)}>
                <Icon size={18} aria-hidden="true" />
                {t}
              </button>
            )
          })}
        </nav>
      </aside>
      <div className="content">
        <header className="topbar">
          <h1>{active}</h1>
          <span className="badge">Synthetic demo data</span>
        </header>
        <main>{children}</main>
        <footer>SYNTHETIC DEMO DATA — Not validated Malaysian market trends. Scores are not employment probabilities.</footer>
      </div>
    </div>
  )
}