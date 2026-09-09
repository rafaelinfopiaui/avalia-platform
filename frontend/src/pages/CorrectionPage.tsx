import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { Spinner } from '../components/Spinner'
import { getCorrectionJob } from '../services/api'
import { readWorkflow, writeWorkflow } from '../services/workflow'
import type { CorrectionJob } from '../types'

const labels = { PENDENTE: 'Análise na fila', PROCESSANDO: 'Análise em processamento', SUGERIDA: 'Sugestão pronta para revisão', FALHA: 'A análise não pôde ser concluída' }
export function CorrectionPage() {
  const { id } = useParams(); const navigate = useNavigate(); const [job, setJob] = useState<CorrectionJob | undefined>(readWorkflow().job); const [error, setError] = useState(''); const timer = useRef<number>()
  useEffect(() => { let active = true; const poll = async () => { if (!id) return; try { const next = await getCorrectionJob(id); if (!active) return; setJob(next); writeWorkflow({ job: next }); if (next.status === 'SUGERIDA') { navigate(`/correcoes/${id}/revisao`, { replace: true }); return } if (next.status === 'PENDENTE' || next.status === 'PROCESSANDO') timer.current = window.setTimeout(poll, 2000) } catch (e) { if (active) setError(e instanceof Error ? e.message : 'Não foi possível consultar o processamento.') } }; void poll(); return () => { active = false; if (timer.current) window.clearTimeout(timer.current) } }, [id, navigate])
  const status = job?.status || 'PENDENTE'
  return <section className="processing-card"><div className={`process-icon process-icon--${status.toLowerCase()}`} aria-hidden="true">{status === 'FALHA' ? '!' : 'AI'}</div><p className="eyebrow">Correção assistida</p><h1>{labels[status]}</h1>{error && <Alert>{error}</Alert>}
    {(status === 'PENDENTE' || status === 'PROCESSANDO') && <><Spinner label={status === 'PENDENTE' ? 'Aguardando início…' : 'Analisando critérios e evidências…'} /><p>Você pode manter esta tela aberta. O status é atualizado automaticamente.</p></>}
    {status === 'FALHA' && <><Alert>Não foi possível analisar esta resposta. Tente novamente ou encaminhe para correção manual.</Alert>{job?.error_message && <p>{job.error_message}</p>}<div className="button-row"><Link className="button button--secondary" to="/avaliacoes">Voltar às avaliações</Link><Link className="button button--primary" to={`/correcoes/${id}/revisao?manual=1`}>Seguir para revisão manual</Link></div></>}
  </section>
}
