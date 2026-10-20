import type { ReactNode } from 'react'
import { BarChart3, Briefcase, Globe, LayoutDashboard, Moon, Route, SlidersHorizontal, Sun, User } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import UserAvatar from './UserAvatar'

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

export default function Layout({ active, onSelect, userName, avatarUrl, theme, onToggleTheme, children }: { active: Tab; onSelect: (tab: Tab) => void; userName: string; avatarUrl?: string | null; theme: 'light' | 'dark'; onToggleTheme: () => void; children: ReactNode }) {
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
            <UserAvatar name={userName} imageUrl={avatarUrl} size="small" />
            <span className="sidebar-account-label">Account</span>
          </button>
        </div>
      </aside>
      <div className="content">
        <header className="topbar">
          <h1>{active}</h1>
          <div className="topbar-actions">
            <span className="badge" title="Trend scenario weights are synthetic, even if you are signed in">Demo data</span>
            <button type="button" className="theme-toggle" onClick={onToggleTheme} aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`} title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
              {theme === 'light' ? <Moon size={17} aria-hidden="true" /> : <Sun size={17} aria-hidden="true" />}
              <span>{theme === 'light' ? 'Dark' : 'Light'} mode</span>
            </button>
            <button type="button" className="topbar-user" title={`Account: ${userName}`} onClick={() => onSelect('Account')} aria-label={`Open account for ${userName}`}>
              <UserAvatar name={userName} imageUrl={avatarUrl} size="small" />
              <span>{userName}</span>
            </button>
          </div>
        </header>
        <main>{children}</main>
        <footer>SYNTHETIC SCENARIO WEIGHTS — Scores measure skill compatibility, not employment probability. Occupation evidence is separate.</footer>
      </div>
    </div>
  )
}
