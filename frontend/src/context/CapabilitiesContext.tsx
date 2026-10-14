import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { getCapabilities } from '../services/api'

interface CapabilitiesValue {
  /** Única fonte de decisão de UI sobre o módulo acadêmico (BL-AV-S03B-02). */
  academicModuleEnabled: boolean
  /**
   * true enquanto uma consulta a GET /v1/config/capabilities está em voo
   * (a inicial ou uma disparada por `retry()`). Estado DESCONHECIDO.
   */
  loading: boolean
  /**
   * true quando a última consulta falhou DEFINITIVAMENTE (rede, 5xx, resposta
   * inválida) e nenhuma outra está em curso. Distinto de `loading`: aqui a
   * configuração real nunca foi obtida e não será, até alguém chamar `retry()`.
   * Consumidores em caminho de ESCRITA devem tratar este estado como
   * "configuração desconhecida" e NÃO como "módulo comprovadamente desligado"
   * (ver `AssessmentEditorPage.tsx`).
   */
  error: boolean
  /**
   * Repete a consulta a GET /v1/config/capabilities. Volta imediatamente para
   * `loading = true` / `error = false`, mantendo a capacidade em `false`
   * (fail-closed) até a nova resposta real chegar.
   */
  retry: () => void
}

const CapabilitiesContext = createContext<CapabilitiesValue | null>(null)

export function CapabilitiesProvider({ children }: { children: ReactNode }) {
  const [academicModuleEnabled, setAcademicModuleEnabled] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  // Contador de tentativas: incrementá-lo é o que re-dispara o efeito de
  // consulta. Mantém a consulta em UM único lugar (o efeito), em vez de
  // duplicar a lógica de fetch/normalização dentro de `retry()`.
  const [attempt, setAttempt] = useState(0)

  const retry = useCallback(() => {
    // Volta ao estado DESCONHECIDO antes de refazer a chamada: nunca deixamos
    // um `error` antigo (ou um valor anterior) visível durante a nova tentativa.
    setAcademicModuleEnabled(false)
    setError(false)
    setLoading(true)
    setAttempt(previous => previous + 1)
  }, [])

  useEffect(() => {
    let cancelled = false
    getCapabilities()
      .then(data => {
        if (cancelled) return
        // REGRA CRÍTICA DE SEGURANÇA (fail-closed, AC-04): só habilitamos a
        // capacidade quando o backend respondeu LITERALMENTE true. Qualquer
        // outro valor (undefined, string "true", null, campo ausente por
        // divergência de contrato) é tratado como DESLIGADO.
        setAcademicModuleEnabled(data?.academic_module_enabled === true)
        setError(false)
      })
      .catch(() => {
        if (cancelled) return
        // REGRA CRÍTICA DE SEGURANÇA (fail-closed, AC-04): a falha ao obter a
        // configuração NUNCA pode habilitar funcionalidade. Endpoint fora do
        // ar, timeout, CORS, 4xx/5xx — todos resultam em módulo DESLIGADO.
        // Nunca usar `true` como fallback de erro nem "manter o último valor
        // conhecido" vindo de env var/localStorage.
        setAcademicModuleEnabled(false)
        setError(true)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [attempt])

  // REGRA CRÍTICA DE SEGURANÇA (fail-closed, AC-02/AC-04): enquanto
  // loading === true o estado da capacidade é DESCONHECIDO, e desconhecido é
  // tratado como desligado. O valor inicial do estado já é `false` e a
  // normalização abaixo torna isso explícito e independente da ordem dos
  // setState — a ausência ou falha de consulta de configuração não pode
  // habilitar o módulo acadêmico nem por uma renderização.
  //
  // ATENÇÃO (lacuna 1, saneamento AV-S03B): este `false` normalizado colapsa
  // TRÊS situações diferentes — carregando, falha definitiva e "backend
  // respondeu false". Isso é adequado para consumidores que só ESCONDEM coisas
  // (`Layout.tsx`, `AcademicPage.tsx`): esconder a mais nunca é inseguro.
  // Consumidores em caminho de ESCRITA precisam olhar `loading` e `error`
  // SEPARADAMENTE, porque para eles "desconhecido" ≠ "desligado": tratar
  // falha definitiva como "modo legado confirmado" deixaria o usuário preencher
  // e tentar salvar algo que o backend pode recusar (422).
  const value: CapabilitiesValue = {
    academicModuleEnabled: loading || error ? false : academicModuleEnabled,
    loading,
    error,
    retry,
  }

  return <CapabilitiesContext.Provider value={value}>{children}</CapabilitiesContext.Provider>
}

export function useCapabilities(): CapabilitiesValue {
  const value = useContext(CapabilitiesContext)
  if (!value) throw new Error('CapabilitiesProvider ausente')
  return value
}
