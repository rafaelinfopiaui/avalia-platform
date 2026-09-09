import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { Spinner } from '../components/Spinner'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const { user, login } = useAuth(); const navigate = useNavigate(); const location = useLocation()
  const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  if (user) return <Navigate to="/avaliacoes" replace />
  const submit = async (event: FormEvent) => { event.preventDefault(); setError(''); setBusy(true); try { await login(email, password); navigate((location.state as { from?: string } | null)?.from || '/avaliacoes', { replace: true }) } catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível entrar. Tente novamente.') } finally { setBusy(false) } }
  return <main className="login-page"><section className="login-card" aria-labelledby="login-title">
    <div className="brand brand--large"><span>Aval</span><strong>IA</strong></div>
    <p className="eyebrow">Correção assistida para professores</p><h1 id="login-title">Acesse sua conta</h1><p>Entre para revisar sugestões e registrar sua decisão pedagógica.</p>
    {error && <Alert>{error}</Alert>}
    <form onSubmit={submit} className="form-stack">
      <label>E-mail<input type="email" autoComplete="email" required value={email} onChange={e => setEmail(e.target.value)} /></label>
      <label>Senha<input type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} /></label>
      <button className="button button--primary button--full" disabled={busy}>{busy ? <Spinner label="Entrando…" /> : 'Entrar'}</button>
    </form>
  </section></main>
}
