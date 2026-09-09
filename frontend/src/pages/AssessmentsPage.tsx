import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { Spinner } from '../components/Spinner'
import { listAssessments } from '../services/api'
import type { Assessment } from '../types'

export function AssessmentsPage() {
  const [items, setItems] = useState<Assessment[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState('')
  const load = () => { setLoading(true); setError(''); listAssessments().then(setItems).catch(e => setError(e.message)).finally(() => setLoading(false)) }
  useEffect(load, [])
  return <><div className="page-heading"><div><p className="eyebrow">Área do professor</p><h1>Suas avaliações</h1><p>Crie uma avaliação e acompanhe a revisão das respostas.</p></div><Link className="button button--primary" to="/avaliacoes/nova">Nova avaliação</Link></div>
    {error && <Alert>{error} <button className="link-button" onClick={load}>Tentar novamente</button></Alert>}
    {loading ? <Spinner label="Carregando avaliações…" /> : items.length === 0 ? <section className="empty-state"><h2>Nenhuma avaliação ainda</h2><p>Comece criando uma questão e sua rubrica de correção.</p><Link className="button button--primary" to="/avaliacoes/nova">Criar primeira avaliação</Link></section> : <div className="card-grid">{items.map(item => { const published = item.status === 'PUBLISHED' || item.status === 'PUBLICADA'; return <article className="assessment-card" key={item.id}><div className={`status status--${item.status.toLowerCase()}`}>{published ? 'Publicada' : 'Rascunho'}</div><h2>{item.title}</h2><p>{item.question?.statement || item.questions?.[0]?.statement || 'Questão em elaboração'}</p><Link className="button button--secondary" to={published ? `/avaliacoes/${item.id}/resposta` : `/avaliacoes/${item.id}`}>{published ? 'Inserir resposta' : 'Continuar edição'}</Link></article> })}</div>}
  </>
}
