import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { Spinner } from '../components/Spinner'
import { attachAssessmentClassGroup, createAssessment, getAssessment, isAcademicModuleEnabled, listClassGroups, publishAssessment, saveRubric } from '../services/api'
import { writeWorkflow } from '../services/workflow'
import type { Assessment, ClassGroup, Criterion } from '../types'

const blankCriterion = (): Criterion => ({ name: '', description: '', max_score: 0 })
export function AssessmentEditorPage() {
  const { id } = useParams(); const navigate = useNavigate(); const editing = Boolean(id)
  const academicModuleEnabled = isAcademicModuleEnabled()
  const [title, setTitle] = useState(''); const [statement, setStatement] = useState(''); const [reference, setReference] = useState(''); const [maxScore, setMaxScore] = useState(5)
  const [criteria, setCriteria] = useState<Criterion[]>([blankCriterion()]); const [assessment, setAssessment] = useState<Assessment | null>(null)
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([])
  const [classGroupId, setClassGroupId] = useState<string>('')
  const [busyLinkClass, setBusyLinkClass] = useState(false)
  const [loading, setLoading] = useState(editing); const [busy, setBusy] = useState<'draft' | 'publish' | ''>(''); const [error, setError] = useState(''); const [success, setSuccess] = useState('')

  useEffect(() => {
    listClassGroups()
      .then(setClassGroups)
      .catch((e: unknown) => {
        const msg = e instanceof Error ? e.message : 'Não foi possível carregar as turmas.'
        setError(prev => (prev ? `${prev} | ${msg}` : msg))
      })
  }, [])

  useEffect(() => {
    if (!id) return
    getAssessment(id).then(a => {
      setAssessment(a)
      setTitle(a.title)
      if (a.class_group_id) setClassGroupId(a.class_group_id)
      const q = a.question || a.questions?.[0]
      if (q) {
        setStatement(q.statement)
        setReference(q.reference_answer)
        setMaxScore(q.max_score)
        setCriteria(q.rubric?.criteria?.length ? q.rubric.criteria : [blankCriterion()])
      }
    }).catch(e => setError(e.message)).finally(() => setLoading(false))
  }, [id])

  const total = useMemo(() => criteria.reduce((sum, item) => sum + (Number(item.max_score) || 0), 0), [criteria])
  const sameTotal = Math.abs(total - maxScore) < 0.001
  const complete = Boolean(
    title.trim() &&
    statement.trim() &&
    reference.trim() &&
    maxScore > 0 &&
    criteria.length &&
    criteria.every(c => c.name.trim() && c.description.trim() && c.max_score > 0) &&
    (!academicModuleEnabled || Boolean(classGroupId))
  )
  const canPublish = complete && sameTotal
  const setCriterion = (index: number, patch: Partial<Criterion>) => setCriteria(old => old.map((item, i) => i === index ? { ...item, ...patch } : item))

  async function handleAttachClassGroup() {
    if (!assessment?.id || !classGroupId) return
    setError('')
    setSuccess('')
    setBusyLinkClass(true)
    try {
      const updated = await attachAssessmentClassGroup(assessment.id, classGroupId)
      setAssessment(updated)
      setSuccess('Turma vinculada à avaliação com sucesso!')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Não foi possível vincular a turma.')
    } finally {
      setBusyLinkClass(false)
    }
  }

  async function persist(publish: boolean) {
    if (academicModuleEnabled && !classGroupId) {
      setError('A seleção de uma turma vinculada é obrigatória no modo acadêmico.')
      return
    }
    setError(''); setSuccess(''); setBusy(publish ? 'publish' : 'draft')
    try {
      const payload = {
        title: title.trim(),
        class_group_id: classGroupId || undefined,
        question: { statement: statement.trim(), reference_answer: reference.trim(), max_score: maxScore },
      }
      let saved = assessment
      if (!saved) {
        saved = await createAssessment(payload)
      } else if (classGroupId && classGroupId !== saved.class_group_id) {
        saved = await attachAssessmentClassGroup(saved.id, classGroupId)
      }
      const question = saved.question || saved.questions?.[0]
      if (!question?.id) throw new Error('A avaliação foi salva, mas o servidor não informou o identificador da questão.')
      await saveRubric(question.id, criteria)
      if (publish) saved = await publishAssessment(saved.id)
      const hydrated = { ...saved, question: { ...question, ...payload.question, rubric: { criteria } } }
      setAssessment(hydrated); writeWorkflow({ assessment: hydrated })
      if (publish) navigate(`/avaliacoes/${saved.id}/resposta`)
      else setSuccess('Rascunho salvo. Você pode continuar editando ou publicar quando estiver pronto.')
    } catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível salvar a avaliação.') } finally { setBusy('') }
  }
  const submit = (event: FormEvent) => { event.preventDefault(); void persist(false) }
  if (loading) return <Spinner label="Carregando avaliação…" />
  return <><div className="page-heading"><div><Link className="back-link" to="/avaliacoes">← Avaliações</Link><p className="eyebrow">{editing ? 'Editar rascunho' : 'Nova avaliação'}</p><h1>Configure a avaliação</h1></div></div>
    {error && <Alert>{error}</Alert>}{success && <Alert type="success">{success}</Alert>}
    <form onSubmit={submit} className="editor-layout">
      <section className="panel">
        <h2>Dados da questão</h2>
        <label>Título da avaliação<input required value={title} onChange={e => setTitle(e.target.value)} placeholder="Ex.: Estruturas de dados" /></label>
        <label>
          Turma vinculada{academicModuleEnabled ? ' (obrigatória)' : ' (opcional)'}
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <select
              required={academicModuleEnabled}
              value={classGroupId}
              onChange={e => setClassGroupId(e.target.value)}
              style={{ flex: 1 }}
            >
              <option value="">
                {academicModuleEnabled ? 'Selecione uma turma obrigatória...' : 'Selecione uma turma (opcional)...'}
              </option>
              {classGroups.map(cg => (
                <option key={cg.id} value={cg.id}>
                  Turma {cg.code} ({cg.period})
                </option>
              ))}
            </select>
            {editing && classGroupId && classGroupId !== (assessment?.class_group_id || '') && (
              <button
                type="button"
                className="button button--secondary"
                onClick={() => void handleAttachClassGroup()}
                disabled={busyLinkClass || Boolean(busy)}
              >
                {busyLinkClass ? 'Vinculando…' : 'Vincular turma'}
              </button>
            )}
          </div>
          {academicModuleEnabled && !classGroupId && (
            <small style={{ color: '#c53030', display: 'block', marginTop: '0.25rem' }}>
              Turma é obrigatória para novas avaliações quando o módulo acadêmico está ativo.
            </small>
          )}
          {assessment?.class_group_id && (
            <small style={{ color: '#087a55', fontWeight: 600, display: 'block', marginTop: '0.25rem' }}>
              ✓ Avaliação vinculada à turma {classGroups.find(c => c.id === assessment.class_group_id)?.code || assessment.class_group_id}
            </small>
          )}
        </label>
        <label>Enunciado<textarea required rows={4} value={statement} onChange={e => setStatement(e.target.value)} placeholder="Digite o que o aluno deve responder" /></label>
        <label>Resposta de referência<textarea required rows={5} value={reference} onChange={e => setReference(e.target.value)} placeholder="Descreva os pontos esperados na resposta" /></label>
        <label className="short-field">Valor máximo da questão<input type="number" min="0.1" step="0.1" required value={maxScore} onChange={e => setMaxScore(Number(e.target.value))} /></label>
      </section>
      <section className="panel"><div className="section-heading"><div><h2>Rubrica por critérios</h2><p>Defina como os {maxScore.toLocaleString('pt-BR')} pontos serão distribuídos.</p></div><button type="button" className="button button--secondary" onClick={() => setCriteria(c => [...c, blankCriterion()])}>Adicionar critério</button></div>
        <div className={`total-check ${sameTotal ? 'total-check--ok' : 'total-check--error'}`} role="status"><span>Soma dos critérios</span><strong>{total.toLocaleString('pt-BR')} de {maxScore.toLocaleString('pt-BR')} pontos</strong><small>{sameTotal ? 'A soma está correta.' : `Ajuste a rubrica: faltam ${Math.abs(maxScore - total).toLocaleString('pt-BR')} ponto(s) ${total < maxScore ? 'para completar' : 'em excesso'}.`}</small></div>
        <div className="criteria-list">{criteria.map((criterion, index) => <fieldset className="criterion-editor" key={index}><legend>Critério {index + 1}</legend><label>Nome<input required value={criterion.name} onChange={e => setCriterion(index, { name: e.target.value })} /></label><label>Descrição<textarea required rows={2} value={criterion.description} onChange={e => setCriterion(index, { description: e.target.value })} /></label><label className="short-field">Pontos máximos<input type="number" min="0.1" step="0.1" required value={criterion.max_score} onChange={e => setCriterion(index, { max_score: Number(e.target.value) })} /></label>{criteria.length > 1 && <button type="button" className="link-button link-button--danger" onClick={() => setCriteria(c => c.filter((_, i) => i !== index))}>Remover critério</button>}</fieldset>)}</div>
      </section>
      <div className="sticky-actions"><button className="button button--secondary" disabled={Boolean(busy)}>{busy === 'draft' ? 'Salvando…' : 'Salvar rascunho'}</button><div><button type="button" className="button button--primary" disabled={!canPublish || Boolean(busy)} onClick={() => void persist(true)}>{busy === 'publish' ? 'Publicando…' : 'Publicar e inserir resposta'}</button>{!canPublish && <small className="action-hint">{academicModuleEnabled && !classGroupId ? 'Selecione uma turma vinculada, preencha todos os campos e faça a soma da rubrica coincidir com o valor da questão.' : 'Preencha todos os campos e faça a soma da rubrica coincidir com o valor da questão.'}</small>}</div></div>
    </form></>
}

