import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCapabilities } from '../context/CapabilitiesContext'

export function Layout() {
  const { user, logout } = useAuth(); const navigate = useNavigate()
  // DEBT-AV-013: o item de menu "Gestão Acadêmica" ficava sempre visível, mesmo
  // com o módulo desligado. Agora depende da capacidade publicada pelo backend.
  // O contexto já é fail-closed: enquanto carregando ou em caso de falha,
  // academicModuleEnabled é false e o item NÃO é renderizado (AC-02/AC-04).
  const { academicModuleEnabled } = useCapabilities()
  return <div className="app-shell">
    <header className="topbar">
      <NavLink to="/avaliacoes" className="brand" aria-label="AvalIA — início"><span>Aval</span><strong>IA</strong></NavLink>
      <nav aria-label="Navegação principal">
        <NavLink to="/avaliacoes">Avaliações</NavLink>
        {academicModuleEnabled && <NavLink to="/academico">Gestão Acadêmica</NavLink>}
      </nav>
      <div className="user-area"><span>{user?.name || user?.email}</span><button className="button button--ghost" onClick={() => { logout(); navigate('/login') }}>Sair</button></div>
    </header>
    <main className="page"><Outlet /></main>
  </div>
}
