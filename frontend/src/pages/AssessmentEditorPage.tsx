import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { Spinner } from '../components/Spinner'
import { attachAssessmentClassGroup, cloneAssessment, createAssessment, createQuestion, deleteQuestion, getAssessment, isAcademicModuleEnabled, listClassGroups, publishAssessment, reorderQuestions, saveRubric, updateAssessment, updateQuestion } from '../services/api'
import { writeWorkflow } from '../services/workflow'
import type { Assessment, ClassGroup, Criterion } from '../types'

const blankCriterion = (): Criterion => ({ name: '', description: '', max_score: 0 })

type LocalQuestion = {
  _key: string
  id?: string
  statement: string
  reference_answer: string
  max_score: number
  criteria: Criterion[]
}

const generateKey = () => Math.random().toString(36).substring(2, 9)

export function AssessmentEditorPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const editing = Boolean(id)
  const academicModuleEnabled = isAcademicModuleEnabled()

  const [title, setTitle] = useState('')
  const [classGroupId, setClassGroupId] = useState<string>('')
  const [localQuestions, setLocalQuestions] = useState<LocalQuestion[]>([
    { _key: generateKey(), statement: '', reference_answer: '', max_score: 5, criteria: [blankCriterion()] }
  ])

  const [assessment, setAssessment] = useState<Assessment | null>(null)
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([])
  const [busyLinkClass, setBusyLinkClass] = useState(false)
  const [loading, setLoading] = useState(editing)
  const [busy, setBusy] = useState<'draft' | 'publish' | 'clone' | ''>('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

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
    getAssessment(id)
      .then(a => {
        setAssessment(a)
        setTitle(a.title)
        if (a.class_group_id) setClassGroupId(a.class_group_id)
        if (a.questions && a.questions.length > 0) {
          setLocalQuestions(
            a.questions.map(q => ({
              _key: generateKey(),
              id: q.id,
              statement: q.statement,
              reference_answer: q.reference_answer,
              max_score: q.max_score,
              criteria: q.rubrics?.[0]?.criteria?.length ? q.rubrics[0].criteria : [blankCriterion()]
            }))
          )
        } else {
          setLocalQuestions([{ _key: generateKey(), statement: '', reference_answer: '', max_score: 5, criteria: [blankCriterion()] }])
        }
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  const isPublished = assessment?.status === 'PUBLICADA' || assessment?.status === 'PUBLISHED'
  const assessmentMaxScore = localQuestions.reduce((s, q) => s + (Number(q.max_score) || 0), 0)

  const allQuestionsValid = localQuestions.every(q => {
    const total = q.criteria.reduce((s, c) => s + (Number(c.max_score) || 0), 0)
    const sameTotal = Math.abs(total - q.max_score) < 0.001
    return (
      q.statement.trim() &&
      q.reference_answer.trim() &&
      q.max_score > 0 &&
      q.criteria.length > 0 &&
      q.criteria.every(c => c.name.trim() && c.description.trim() && c.max_score > 0) &&
      sameTotal
    )
  })

  const complete = Boolean(
    title.trim() &&
    localQuestions.length > 0 &&
    allQuestionsValid &&
    (!academicModuleEnabled || Boolean(classGroupId))
  )

  const canPublish = complete

  const setQuestionField = (qIndex: number, patch: Partial<LocalQuestion>) => {
    setLocalQuestions(prev => prev.map((q, i) => (i === qIndex ? { ...q, ...patch } : q)))
  }

  const setCriterion = (qIndex: number, cIndex: number, patch: Partial<Criterion>) => {
    setLocalQuestions(prev =>
      prev.map((q, i) => {
        if (i !== qIndex) return q
        const newCriteria = q.criteria.map((c, j) => (j === cIndex ? { ...c, ...patch } : c))
        return { ...q, criteria: newCriteria }
      })
    )
  }

  const addCriterion = (qIndex: number) => {
    setLocalQuestions(prev =>
      prev.map((q, i) => (i === qIndex ? { ...q, criteria: [...q.criteria, blankCriterion()] } : q))
    )
  }

  const removeCriterion = (qIndex: number, cIndex: number) => {
    setLocalQuestions(prev =>
      prev.map((q, i) => {
        if (i !== qIndex) return q
        return { ...q, criteria: q.criteria.filter((_, j) => j !== cIndex) }
      })
    )
  }

  const addQuestion = () => {
    if (localQuestions.length >= 50) {
      setError('Uma avaliação pode ter no máximo 50 questões.')
      return
    }
    setLocalQuestions(prev => [
      ...prev,
      { _key: generateKey(), statement: '', reference_answer: '', max_score: 5, criteria: [blankCriterion()] }
    ])
  }

  const removeQuestion = (qIndex: number) => {
    setLocalQuestions(prev => prev.filter((_, i) => i !== qIndex))
  }

  const moveQuestionUp = (qIndex: number) => {
    if (qIndex === 0) return
    setLocalQuestions(prev => {
      const copy = [...prev]
      const temp = copy[qIndex - 1]
      copy[qIndex - 1] = copy[qIndex]
      copy[qIndex] = temp
      return copy
    })
  }

  const moveQuestionDown = (qIndex: number) => {
    if (qIndex === localQuestions.length - 1) return
    setLocalQuestions(prev => {
      const copy = [...prev]
      const temp = copy[qIndex + 1]
      copy[qIndex + 1] = copy[qIndex]
      copy[qIndex] = temp
      return copy
    })
  }

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

  async function handleClone() {
    if (!assessment?.id) return
    setError('')
    setSuccess('')
    setBusy('clone')
    try {
      const cloned = await cloneAssessment(assessment.id)
      navigate(`/avaliacoes/${cloned.id}`, { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Não foi possível clonar a avaliação.')
      setBusy('')
    }
  }

  async function persist(publish: boolean) {
    if (academicModuleEnabled && !classGroupId) {
      setError('A seleção de uma turma vinculada é obrigatória no modo acadêmico.')
      return
    }
    setError('')
    setSuccess('')
    setBusy(publish ? 'publish' : 'draft')
    try {
      let saved = assessment

      if (!saved) {
        const payload = {
          title: title.trim(),
          class_group_id: classGroupId || undefined,
          questions: localQuestions.map(q => ({
            statement: q.statement.trim(),
            reference_answer: q.reference_answer.trim(),
            max_score: q.max_score
          }))
        }
        saved = await createAssessment(payload)
        for (let i = 0; i < (saved.questions || []).length; i++) {
          await saveRubric(saved.questions![i].id!, localQuestions[i].criteria)
        }
        saved = await getAssessment(saved.id)
      } else {
        if (title.trim() !== saved.title) {
          saved = await updateAssessment(saved.id, { title: title.trim() })
        }
        if (classGroupId && classGroupId !== saved.class_group_id) {
          saved = await attachAssessmentClassGroup(saved.id, classGroupId)
        }

        const newIds = new Set(localQuestions.filter(q => q.id).map(q => q.id))
        const oldIds = saved.questions?.map(q => q.id!) || []
        for (const oldId of oldIds) {
          if (!newIds.has(oldId)) {
            await deleteQuestion(oldId)
          }
        }

        const finalQuestionIds: string[] = []
        for (const lq of localQuestions) {
          let qId = lq.id
          if (!qId) {
            const created = await createQuestion(saved.id, {
              statement: lq.statement.trim(),
              reference_answer: lq.reference_answer.trim(),
              max_score: lq.max_score
            })
            qId = created.id!
            lq.id = qId
          } else {
            await updateQuestion(qId, {
              statement: lq.statement.trim(),
              reference_answer: lq.reference_answer.trim(),
              max_score: lq.max_score
            })
          }
          finalQuestionIds.push(qId)
          await saveRubric(qId, lq.criteria)
        }

        if (finalQuestionIds.length > 1) {
          saved = await reorderQuestions(saved.id, finalQuestionIds)
        } else {
          saved = await getAssessment(saved.id)
        }
      }

      if (publish) {
        await publishAssessment(saved.id)
        saved = await getAssessment(saved.id)
      }

      setAssessment(saved)
      setLocalQuestions(
        (saved.questions || []).map(q => ({
          _key: generateKey(),
          id: q.id,
          statement: q.statement,
          reference_answer: q.reference_answer,
          max_score: q.max_score,
          criteria: q.rubrics?.[0]?.criteria?.length ? q.rubrics[0].criteria : [blankCriterion()]
        }))
      )
      writeWorkflow({ assessment: saved })

      if (publish) {
        navigate(`/avaliacoes/${saved.id}/resposta`)
      } else {
        setSuccess('Rascunho salvo. Você pode continuar editando ou publicar quando estiver pronto.')
        if (!editing) navigate(`/avaliacoes/${saved.id}`, { replace: true })
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Não foi possível salvar a avaliação.')
    } finally {
      setBusy('')
    }
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!isPublished) void persist(false)
  }

  if (loading) return <Spinner label="Carregando avaliação…" />

  return (
    <>
      <div className="page-heading">
        <div>
          <Link className="back-link" to="/avaliacoes">
            ← Avaliações
          </Link>
          <p className="eyebrow">{isPublished ? 'Avaliação publicada' : editing ? 'Editar rascunho' : 'Nova avaliação'}</p>
          <h1>{isPublished ? title : 'Configure a avaliação'}</h1>
        </div>
        {isPublished && (
          <button type="button" className="button button--secondary" onClick={() => void handleClone()} disabled={Boolean(busy)}>
            {busy === 'clone' ? 'Clonando...' : 'Clonar para editar'}
          </button>
        )}
      </div>
      {error && <Alert>{error}</Alert>}
      {success && <Alert type="success">{success}</Alert>}
      <form onSubmit={submit} className="editor-layout">
        <section className="panel">
          <h2>Dados da avaliação</h2>
          <label>
            Título da avaliação
            <input required value={title} onChange={e => setTitle(e.target.value)} placeholder="Ex.: Estruturas de dados" disabled={isPublished} />
          </label>
          <label>
            Turma vinculada{academicModuleEnabled ? ' (obrigatória)' : ' (opcional)'}
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <select
                required={academicModuleEnabled}
                value={classGroupId}
                onChange={e => setClassGroupId(e.target.value)}
                style={{ flex: 1 }}
                disabled={isPublished}
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
              {editing && !isPublished && classGroupId && classGroupId !== (assessment?.class_group_id || '') && (
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
          <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f0fdf4', borderRadius: '4px', border: '1px solid #bbf7d0' }}>
            <span style={{ display: 'block', fontSize: '0.875rem', color: '#166534', fontWeight: 500 }}>Pontuação máxima da avaliação</span>
            <strong style={{ display: 'block', fontSize: '1.5rem', color: '#15803d' }}>
              {assessment?.assessment_max_score !== undefined && isPublished ? Number(assessment.assessment_max_score).toLocaleString('pt-BR') : assessmentMaxScore.toLocaleString('pt-BR')} pontos
            </strong>
          </div>
        </section>

        {localQuestions.map((q, qIndex) => {
          const total = q.criteria.reduce((s, c) => s + (Number(c.max_score) || 0), 0)
          const sameTotal = Math.abs(total - q.max_score) < 0.001

          return (
            <section key={q._key} className="panel" style={{ borderLeft: '4px solid #3b82f6' }}>
              <div className="section-heading">
                <div>
                  <h2>Questão {qIndex + 1}</h2>
                </div>
                {!isPublished && (
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button type="button" aria-label="Mover acima" className="button button--secondary" style={{ padding: '0.5rem' }} onClick={() => moveQuestionUp(qIndex)} disabled={qIndex === 0}>
                      ⬆️
                    </button>
                    <button type="button" aria-label="Mover abaixo" className="button button--secondary" style={{ padding: '0.5rem' }} onClick={() => moveQuestionDown(qIndex)} disabled={qIndex === localQuestions.length - 1}>
                      ⬇️
                    </button>
                    <button type="button" aria-label="Remover questão" className="button button--secondary" style={{ color: '#dc2626', borderColor: '#fca5a5' }} onClick={() => removeQuestion(qIndex)}>
                      Remover
                    </button>
                  </div>
                )}
              </div>

              <label>
                Enunciado
                <textarea required rows={4} value={q.statement} onChange={e => setQuestionField(qIndex, { statement: e.target.value })} placeholder="Digite o que o aluno deve responder" disabled={isPublished} />
              </label>
              <label>
                Resposta de referência
                <textarea required rows={5} value={q.reference_answer} onChange={e => setQuestionField(qIndex, { reference_answer: e.target.value })} placeholder="Descreva os pontos esperados na resposta" disabled={isPublished} />
              </label>
              <label className="short-field">
                Valor máximo da questão
                <input type="number" min="0.1" step="0.1" required value={q.max_score} onChange={e => setQuestionField(qIndex, { max_score: Number(e.target.value) })} disabled={isPublished} />
              </label>

              <div style={{ marginTop: '2rem' }}>
                <div className="section-heading">
                  <div>
                    <h3>Rubrica por critérios</h3>
                    <p>Defina como os {q.max_score.toLocaleString('pt-BR')} pontos desta questão serão distribuídos.</p>
                  </div>
                  {!isPublished && (
                    <button type="button" className="button button--secondary" onClick={() => addCriterion(qIndex)}>
                      Adicionar critério
                    </button>
                  )}
                </div>
                <div className={`total-check ${sameTotal ? 'total-check--ok' : 'total-check--error'}`} role="status">
                  <span>Soma dos critérios</span>
                  <strong>{total.toLocaleString('pt-BR')} de {q.max_score.toLocaleString('pt-BR')} pontos</strong>
                  <small>
                    {sameTotal
                      ? 'A soma está correta.'
                      : `Ajuste a rubrica: faltam ${Math.abs(q.max_score - total).toLocaleString('pt-BR')} ponto(s) ${total < q.max_score ? 'para completar' : 'em excesso'}.`}
                  </small>
                </div>
                <div className="criteria-list">
                  {q.criteria.map((criterion, cIndex) => (
                    <fieldset className="criterion-editor" key={cIndex}>
                      <legend>Critério {cIndex + 1}</legend>
                      <label>
                        Nome
                        <input required value={criterion.name} onChange={e => setCriterion(qIndex, cIndex, { name: e.target.value })} disabled={isPublished} />
                      </label>
                      <label>
                        Descrição
                        <textarea required rows={2} value={criterion.description} onChange={e => setCriterion(qIndex, cIndex, { description: e.target.value })} disabled={isPublished} />
                      </label>
                      <label className="short-field">
                        Pontos máximos
                        <input type="number" min="0.1" step="0.1" required value={criterion.max_score} onChange={e => setCriterion(qIndex, cIndex, { max_score: Number(e.target.value) })} disabled={isPublished} />
                      </label>
                      {!isPublished && q.criteria.length > 1 && (
                        <button type="button" className="link-button link-button--danger" onClick={() => removeCriterion(qIndex, cIndex)}>
                          Remover critério
                        </button>
                      )}
                    </fieldset>
                  ))}
                </div>
              </div>
            </section>
          )
        })}

        {!isPublished && (
          <div style={{ display: 'flex', justifyContent: 'center', margin: '2rem 0' }}>
            <button type="button" className="button button--secondary" onClick={addQuestion} disabled={localQuestions.length >= 50 || Boolean(busy)}>
              + Adicionar questão
            </button>
          </div>
        )}

        {!isPublished && (
          <div className="sticky-actions">
            <button className="button button--secondary" disabled={Boolean(busy)}>
              {busy === 'draft' ? 'Salvando…' : 'Salvar rascunho'}
            </button>
            <div>
              <button type="button" className="button button--primary" disabled={!canPublish || Boolean(busy)} onClick={() => void persist(true)}>
                {busy === 'publish' ? 'Publicando…' : 'Publicar e inserir resposta'}
              </button>
              {!canPublish && (
                <small className="action-hint">
                  {localQuestions.length === 0
                    ? 'Adicione ao menos uma questão.'
                    : academicModuleEnabled && !classGroupId
                      ? 'Selecione uma turma vinculada, preencha todos os campos e faça a soma da rubrica coincidir com o valor de cada questão.'
                      : 'Preencha todos os campos e faça a soma da rubrica coincidir com o valor de cada questão.'}
                </small>
              )}
            </div>
          </div>
        )}
      </form>
    </>
  )
}
