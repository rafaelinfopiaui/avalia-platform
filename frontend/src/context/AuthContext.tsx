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
  const login = async (email: string, password: string) => { await apiLogin(email, password); setUser(await getMe()) }
  const logout = () => { clearSession(); setUser(null) }
  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error('AuthProvider ausente'); return value }
