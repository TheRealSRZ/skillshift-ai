import { BarChart3, Briefcase, Globe, Route } from 'lucide-react'

type DemoUser = { name: string; email: string }

const personas = [
  { name: 'Demo student', email: 'student@skillshift.test', blurb: 'Final-year IT student, exploring first roles' },
  { name: 'Demo career switcher', email: 'switcher@skillshift.test', blurb: 'Working adult, moving into a new field' },
]

const features = [
  { icon: Briefcase, text: 'Future roles that fit your skills' },
  { icon: BarChart3, text: 'AI trend signals with sources' },
  { icon: Route, text: 'A learning roadmap with free courses' },
  { icon: Globe, text: 'Links to the UN Sustainable Development Goals' },
]

const initials = (name: string) => name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()

export default function LoginPage({ onSignIn }: { onSignIn: (user: DemoUser) => void }) {
  return (
    <div className="login-split">
      <div className="login-brand">
        <h1>SkillShift AI</h1>
        <p>See which future roles fit your skills, and what to learn next.</p>
        <ul>
          {features.map(f => (
            <li key={f.text}>
              <f.icon size={18} aria-hidden="true" />
              {f.text}
            </li>
          ))}
        </ul>
      </div>
      <div className="login-panel">
        <div className="login-box">
          <h2>Who's exploring today?</h2>
          <p className="login-sub">Pick a demo persona to see the app with sample data.</p>
          <div className="persona-grid">
            {personas.map(p => (
              <button type="button" key={p.email} className="persona" onClick={() => onSignIn({ name: p.name, email: p.email })}>
                <span className="avatar large">{initials(p.name)}</span>
                <strong>{p.name}</strong>
                <span>{p.blurb}</span>
              </button>
            ))}
          </div>
          <p className="login-note">Demo only. Synthetic data, no passwords or real details.</p>
        </div>
      </div>
    </div>
  )
}