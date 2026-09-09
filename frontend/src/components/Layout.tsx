import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Layout() {
  const { user, logout } = useAuth(); const navigate = useNavigate()
  return <div className="app-shell">
    <header className="topbar">
      <NavLink to="/avaliacoes" className="brand" aria-label="AvalIA — início"><span>Aval</span><strong>IA</strong></NavLink>
      <nav aria-label="Navegação principal"><NavLink to="/avaliacoes">Avaliações</NavLink></nav>
      <div className="user-area"><span>{user?.name || user?.email}</span><button className="button button--ghost" onClick={() => { logout(); navigate('/login') }}>Sair</button></div>
    </header>
    <main className="page"><Outlet /></main>
  </div>
}
