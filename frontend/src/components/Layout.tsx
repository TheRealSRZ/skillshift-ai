import type { ReactNode } from 'react'
import { BarChart3, Briefcase, Globe, LayoutDashboard, Route, SlidersHorizontal, User } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

const tabs = ['Dashboard', 'Profile', 'Trends', 'Careers', 'Simulator', 'Roadmap', 'SDG Impact'] as const
export type Tab = typeof tabs[number] | 'Account'

const icons: Record<typeof tabs[number], LucideIcon> = {
  Dashboard: LayoutDashboard,
  Profile: User,
  Trends: BarChart3,
  Careers: Briefcase,
  Simulator: SlidersHorizontal,
  Roadmap: Route,
  'SDG Impact': Globe,
}

const initials = (name: string) => name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()

export default function Layout({ active, onSelect, userName, children }: { active: Tab; onSelect: (tab: Tab) => void; userName: string; children: ReactNode }) {
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
        <div className="sidebar-bottom">
          <button type="button" className={active === 'Account' ? 'nav-item selected' : 'nav-item'} onClick={() => onSelect('Account')}>
            <span className="avatar">{initials(userName)}</span>
            Account
          </button>
        </div>
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