export default function Navbar({ username }) {
  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="logo">
          <span className="logo-icon">🔥</span>
          SECURECORP
        </div>
        <div className="nav-actions">
          <span className="session-status">
            {username ? `Conectado como ${username}` : 'Invitado'}
          </span>
        </div>
      </div>
    </nav>
  );
}
