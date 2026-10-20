export default function AccountPage({ name, email, onSignOut }: { name: string; email: string; onSignOut: () => void }) {
  const initials = name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
  return (
    <section>
      <h2>Account</h2>
      <div className="card account-card">
        <div className="account-head">
          <span className="avatar large">{initials}</span>
          <div>
            <h3>{name}</h3>
            <p className="muted">{email}</p>
          </div>
          <span className="badge">Synthetic profile</span>
        </div>
        <div className="account-row">
          <span>Data and privacy</span>
          <span className="muted">Synthetic data only</span>
        </div>
        <div className="account-row">
          <span>Session</span>
          <button type="button" onClick={onSignOut}>Sign out</button>
        </div>
      </div>
    </section>
  )
}