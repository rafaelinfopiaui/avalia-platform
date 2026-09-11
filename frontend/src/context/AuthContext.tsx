import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { clearSession, getMe, hasSession, login as apiLogin } from '../services/api'
import type { User } from '../types'

interface AuthValue { user: User | null; loading: boolean; login: (email: string, password: string) => Promise<void>; logout: () => void }
const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(hasSession())
  useEffect(() => {
    if (!hasSession()) return
    getMe().then(setUser).catch(() => setUser(null)).finally(() => setLoading(false))
  }, [])
  useEffect(() => {
    // Bug corrigido: quando o token expira/é rejeitado (401), api.ts limpa a sessão
    // (clearSession) e dispara este evento, mas nunca atualizava o "user" mantido
    // aqui. Isso deixava SessionGuard (que só sai da rota protegida quando "user"
    // é nulo) e LoginPage (que redireciona de volta quando "user" existe) com
    // visões inconsistentes de quem está logado, causando um loop infinito de
    // navegação entre "/login" e a rota protegida — history.replaceState() disparado
    // dezenas de vezes por segundo até o navegador bloquear por segurança
    // (SecurityError: Attempt to use history.replaceState() more than 100 times per
    // 10 seconds). Zerar "user" aqui garante que as duas telas concordem sobre o
    // estado de sessão e o redirecionamento pare em uma única navegação.
    const handler = () => setUser(null)
    window.addEventListener('avalia:unauthorized', handler)
    return () => window.removeEventListener('avalia:unauthorized', handler)
  }, [])
  const login = async (email: string, password: string) => { await apiLogin(email, password); setUser(await getMe()) }
  const logout = () => { clearSession(); setUser(null) }
  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error('AuthProvider ausente'); return value }
