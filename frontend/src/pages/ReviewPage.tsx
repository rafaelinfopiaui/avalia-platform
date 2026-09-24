import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { Confidence } from '../components/Confidence'
import { getCorrectionContext, submitReview, ApiError } from '../services/api'
import { readWorkflow } from '../services/workflow'
import type { Assessment, Answer, CorrectionJob, Question, Criterion, CriterionSuggestion, HumanReviewSummary } from '../types'

export type ReviewData = {
  assessment?: Pick<Assessment, 'id' | 'title'> & { question?: Question, questions?: Question[] };
  answer?: Answer;
  job?: CorrectionJob;
  human_review?: HumanReviewSummary | null;
}

const num = (value?: number) => Number(value || 0)

function formatScore(value: number | string | undefined): string {
  if (value === undefined || value === null) return '0'
  const n = Number(value)
  return isNaN(n) ? String(value) : n.toLocaleString('pt-BR')
}

function formatDateTime(isoString?: string): string {
  if (!isoString) return ''
  const parsed = new Date(isoString)
  return isNaN(parsed.getTime()) ? isoString : parsed.toLocaleString('pt-BR')
}

export function ReviewPage() {
  const { id } = useParams<{ id: string }>()
  const [params] = useSearchParams()
  const manual = params.get('manual') === '1'

  const [loading, setLoading] = useState(true)
  const [hasCachedData, setHasCachedData] = useState(false)
  const [errorObj, setErrorObj] = useState<{ message: string; status?: number } | null>(null)

  const [data, setData] = useState<ReviewData>({})

  useEffect(() => {
    if (!id) {
      setLoading(false)
      return
    }

    let active = true

    const current = readWorkflow()
    const hasCache = current.job?.id === id && current.assessment && current.answer
    setHasCachedData(!!hasCache)
    setLoading(true)

    getCorrectionContext(id)
      .then((ctx) => {
        if (!active) return
        const newData: ReviewData = {
          job: ctx.job,
          answer: ctx.answer,
          assessment: { ...ctx.assessment, question: ctx.question },
          human_review: ctx.human_review ?? null,
        }
        setData(newData)
        setErrorObj(null)
      })
      .catch((e) => {
        if (!active) return
        if (e instanceof ApiError && e.status === 403) {
          setErrorObj({ message: 'Você não tem permissão para acessar esta correção.', status: 403 })
        } else {
          setErrorObj({ message: e instanceof Error ? e.message : 'Não foi possível carregar os dados.', status: e instanceof ApiError ? e.status : 0 })
        }
      })
      .finally(() => {
        if (!active) return
        setLoading(false)
      })

    return () => {
      active = false
    }
  }, [id])

  if (loading) {
    return <div className="page-heading"><div><p>{hasCachedData ? 'Carregando dados de uma resposta já vista antes...' : 'Carregando dados da revisão...'}</p></div></div>
  }

  if (errorObj) {
    if (errorObj.status === 403) {
      return <Alert type="error">{errorObj.message}</Alert>
    }
    return <Alert type="error">{errorObj.message} <Link to="/avaliacoes">Volte às avaliações</Link>.</Alert>
  }

  // Guarda contra dados obsoletos: se o :id da URL mudou (navegação client-side
  // entre duas revisões) mas o useEffect ainda não repovoou `data` para o novo
  // id, não renderizar o ReviewForm com os dados antigos autorizados — isso
  // vazaria dados de uma revisão anterior (possivelmente de outro professor)
  // até a nova resposta da API chegar.
  if (data.job?.id !== id) {
    return <div className="page-heading"><div><p>Carregando dados da revisão...</p></div></div>
  }

  if (!data.job || !data.answer || (!data.assessment?.question && !data.assessment?.questions)) {
    return <Alert>Os dados da revisão não estão disponíveis nesta sessão. <Link to="/avaliacoes">Volte às avaliações</Link> e abra a resposta novamente.</Alert>
  }

  return <ReviewForm data={data} manual={manual} />
}

function ReviewForm({ data, manual }: { data: ReviewData, manual: boolean }) {
  const navigate = useNavigate(); const { assessment, answer, job, human_review: humanReview } = data; const correction = job?.latest_execution
  const isReadOnly = Boolean(humanReview)
  const question = assessment?.question || assessment?.questions?.[0]; const rubric = question?.rubric?.criteria || []
  const nameFor = (criterionId: string, index: number) => rubric.find((c: Criterion) => c.id === criterionId)?.name || `Critério ${index + 1}`
  const suggestions: CriterionSuggestion[] = correction?.criterion_scores || rubric.map((c: Criterion) => ({ criterion_id: c.id || c.name, max_score: c.max_score, score: 0, evidence: undefined as string | undefined, reason: undefined as string | undefined, confidence: undefined as number | undefined }))
  const finalScoresMap = useMemo(() => {
    const map = new Map<string, string | number>()
    if (humanReview?.final_scores) {
      for (const item of humanReview.final_scores) {
        map.set(item.criterion_id, item.score)
      }
    }
    return map
  }, [humanReview])
  const [mode, setMode] = useState<'view' | 'alter'>(!isReadOnly && manual ? 'alter' : 'view'); const [scores, setScores] = useState<Record<string, number>>(() => Object.fromEntries(suggestions.map((s: CriterionSuggestion) => [s.criterion_id, num(s.score)])))
  const [justification, setJustification] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const total = useMemo(() => Object.values(scores).reduce((a, b) => a + num(b), 0), [scores]); const suggestedTotal = suggestions.reduce((a: number, b: CriterionSuggestion) => a + num(b.score), 0)
  const validScores = suggestions.every((s: CriterionSuggestion) => scores[s.criterion_id] >= 0 && scores[s.criterion_id] <= s.max_score); const canAlter = validScores && Boolean(justification.trim())
  const send = async (decision: 'APPROVE' | 'ALTER') => { const jobId = job?.id; if (!jobId) { setError('O servidor não forneceu o identificador da correção. Não é possível registrar a decisão.'); return } setBusy(true); setError(''); try { await submitReview(jobId, decision === 'APPROVE' ? { decision } : { decision, criteria_scores: suggestions.map((s: CriterionSuggestion) => ({ criterion_id: s.criterion_id, score: scores[s.criterion_id] })), justification: justification.trim() }); navigate('/avaliacoes', { state: { reviewSaved: true } }) } catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível registrar sua decisão.') } finally { setBusy(false) } }
  return <>{isReadOnly ? <div className="page-heading"><div><p className="eyebrow">Decisão humana registrada</p><h1>Revisão concluída</h1><p>Esta correção já foi revisada. Os dados abaixo são exibidos em modo somente leitura.</p></div><div><Link to="/avaliacoes" className="button button--secondary">Voltar às avaliações</Link></div></div> : <div className="page-heading"><div><p className="eyebrow">Revisão humana obrigatória</p><h1>Revise antes de confirmar</h1><p>A sugestão apoia sua análise. A decisão final é sempre sua.</p></div></div>}
    {isReadOnly && humanReview && <Alert type="info"><strong>Decisão humana já registrada.</strong> Decisão: {humanReview.decision === 'APPROVE' ? 'Aprovação (APPROVE)' : 'Alteração (ALTER)'} • Nota final: {formatScore(humanReview.final_total)} pontos • Revisado por: {humanReview.reviewer_email || humanReview.reviewer_id} em {formatDateTime(humanReview.created_at)}.{humanReview.justification ? ` Justificativa: ${humanReview.justification}` : ''}</Alert>}
    {!isReadOnly && correction?.engine_mode === 'simulated' && <Alert type="warning"><strong>Análise em modo simulado.</strong> Este resultado não foi gerado pelo modelo real e deve ser usado apenas para demonstração. Faça a revisão manual completa.</Alert>}
    {!isReadOnly && manual && <Alert type="warning"><strong>Modo de correção manual.</strong> A IA não produziu uma sugestão. Preencha a pontuação de cada critério.</Alert>}{error && <Alert>{error}</Alert>}
    <div className="review-layout"><section className="panel review-source"><span className="label">Enunciado</span><h2>{question?.statement}</h2><div className="answer-box"><span className="label">Resposta do aluno — somente leitura</span><p>{answer?.text}</p></div></section>
      <section className="review-criteria" aria-label="Critérios de correção">{suggestions.map((item: CriterionSuggestion, index: number) => {
        const finalScore = isReadOnly ? (finalScoresMap.get(item.criterion_id) ?? item.score) : item.score
        return <article className="criterion-review" key={item.criterion_id}><div className="criterion-title"><div><span className="label">Critério {index + 1}</span><h2>{nameFor(item.criterion_id, index)}</h2></div><strong>{!isReadOnly && mode === 'alter' ? <><input className="score-input" aria-label={`Pontuação para ${nameFor(item.criterion_id, index)}`} type="number" min="0" max={item.max_score} step="0.1" value={scores[item.criterion_id]} onChange={e => setScores(s => ({ ...s, [item.criterion_id]: Number(e.target.value) }))} /> / {item.max_score}</> : isReadOnly ? <>{formatScore(finalScore)} / {item.max_score}</> : <>{item.score} / {item.max_score}</>}</strong></div>
          {!manual && <div className="ai-suggestion"><span className="ai-label">{isReadOnly ? 'Sugestão da IA' : 'Sugestão da IA — revisar'}</span><p><strong>Evidência:</strong> {item.evidence || 'Nenhum trecho foi informado.'}</p><p><strong>Justificativa:</strong> {item.reason || 'Justificativa não informada.'}</p><Confidence value={item.confidence} /></div>}{!isReadOnly && mode === 'alter' && (scores[item.criterion_id] < 0 || scores[item.criterion_id] > item.max_score) && <small className="field-error">Use um valor entre 0 e {item.max_score}.</small>}</article>
      })}</section></div>
    <section className="decision-bar"><div className="ai-total"><span>{isReadOnly ? 'Sugestão da IA' : 'Sugestão da IA — revisar'}</span><strong>{manual ? 'Não disponível' : `${suggestedTotal.toLocaleString('pt-BR')} pontos`}</strong>{!manual && <Confidence value={correction?.overall_confidence} />}{correction?.confidence_method_version && <small>Método: {correction.confidence_method_version}</small>}{correction?.flags?.length ? <p><strong>Pontos de atenção:</strong> {correction.flags.join(' • ')}</p> : null}</div>
      <div className="human-decision"><span>Decisão humana</span>{isReadOnly && humanReview ? <><strong>Decisão registrada: {humanReview.decision === 'APPROVE' ? 'Aprovação (APPROVE)' : 'Alteração (ALTER)'}</strong><div><strong>Nota final:</strong> {formatScore(humanReview.final_total)} pontos</div><div><strong>Revisado por:</strong> {humanReview.reviewer_email || humanReview.reviewer_id}</div><div><strong>Data da revisão:</strong> {formatDateTime(humanReview.created_at)}</div>{humanReview.justification ? <div><strong>Justificativa:</strong> {humanReview.justification}</div> : null}<div className="button-row"><Link to="/avaliacoes" className="button button--secondary">Voltar às avaliações</Link></div></> : mode === 'alter' ? <><strong>Nota final a confirmar: {total.toLocaleString('pt-BR')} pontos</strong>{!manual && Math.abs(total - suggestedTotal) > 0.001 && <p className="divergence">Diferença em relação à sugestão da IA: {(total - suggestedTotal).toLocaleString('pt-BR', { signDisplay: 'always' })} ponto(s).</p>}<label>Justificativa da alteração<textarea rows={3} required value={justification} onChange={e => setJustification(e.target.value)} placeholder="Explique por que a decisão humana difere ou como a nota foi definida" /></label><div className="button-row"><button className="button button--ghost" onClick={() => setMode('view')} disabled={busy || manual}>Cancelar alteração</button><button className="button button--primary" disabled={!canAlter || busy} onClick={() => void send('ALTER')}>{busy ? 'Confirmando…' : 'Confirmar alteração'}</button></div></> : <div className="button-row"><button className="button button--secondary" onClick={() => setMode('alter')}>Alterar sugestão</button><button className="button button--primary" disabled={busy} onClick={() => void send('APPROVE')}>{busy ? 'Confirmando…' : 'Aprovar como decisão humana'}</button></div>}</div>
    </section></>
}
