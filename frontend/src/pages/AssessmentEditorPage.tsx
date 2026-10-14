import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { Spinner } from '../components/Spinner'
import { useCapabilities } from '../context/CapabilitiesContext'
import { attachAssessmentClassGroup, cloneAssessment, createAssessment, createQuestion, deleteQuestion, getAssessment, listClassGroups, publishAssessment, reorderQuestions, saveRubric, updateAssessment, updateQuestion } from '../services/api'
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
  // Mesma semântica de antes (turma obrigatória quando o módulo acadêmico está
  // ligado); muda apenas a FONTE do booleano: agora vem do backend via
  // CapabilitiesContext, não de VITE_ACADEMIC_MODULE_ENABLED (DEBT-AV-012).
  //
  // ACHADO BLOQUEANTE DO CODEX (BL-AV-S03B-07), corrigido aqui: para o MENU e
  // para a ROTA /academico, colapsar "desconhecido" em "desligado" é fail-closed
  // (esconder a mais nunca é inseguro). Para ESTE editor, o mesmo colapso era
  // fail-OPEN no caminho de ESCRITA: enquanto a consulta de capacidades estava
  // em voo, `academicModuleEnabled === false` fazia a UI tratar o estado como
  // "modo legado confirmado" e liberava salvar/publicar uma avaliação SEM TURMA.
  // O backend continuava protegido (422 em main.py:149), mas a UI prometia algo
  // que o servidor recusaria. Por isso o editor distingue os TRÊS estados:
  // desconhecido (capabilitiesLoading) ≠ desligado ≠ ligado.
  //
  // SANEAMENTO (lacuna 1, 2026-10-13): a correção acima tratou só a janela de
  // `loading`. Depois de uma falha DEFINITIVA (`error === true`, sem tentativa
  // em curso) o `academicModuleEnabled` normalizado também vale `false`, e o
  // editor voltava a abrir o formulário gravável como se o backend tivesse
  // CONFIRMADO "módulo desligado / modo legado". Se o módulo estivesse de fato
  // ligado, o usuário preencheria a avaliação inteira sem turma para só
  // descobrir o 422 no salvar. São QUATRO estados distintos, e este arquivo
  // trata os quatro: ligado, desligado (resposta real), carregando, falhou.
  const {
    academicModuleEnabled,
    loading: capabilitiesLoading,
    error: capabilitiesError,
    retry: retryCapabilities,
  } = useCapabilities()

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
    // Só consulta turmas depois que a capacidade real é conhecida (item (1) do
    // achado do Codex): antes disso não sabemos sequer se o seletor de turma é
    // obrigatório, opcional ou irrelevante. O mesmo vale para falha definitiva
    // (lacuna 1): nesse estado o formulário nem é renderizado, então listar
    // turmas só produziria um segundo erro em cima do primeiro.
    if (capabilitiesLoading || capabilitiesError) return
    listClassGroups()
      .then(setClassGroups)
      .catch((e: unknown) => {
        const msg = e instanceof Error ? e.message : 'Não foi possível carregar as turmas.'
        setError(prev => (prev ? `${prev} | ${msg}` : msg))
      })
  }, [capabilitiesLoading, capabilitiesError])

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

  // ACH-01 (Antigravity), resolvido aqui: a avaliação JÁ EXISTENTE sem turma é
  // uma avaliação legada no sentido de `DEC-AV-023` ("avaliações legadas
  // nullable com acesso do proprietário/admin, e novas avaliações exigem turma
  // a partir da ativação do módulo acadêmico"). O backend implementa exatamente
  // essa distinção:
  //   - `create_assessment` (core/app/main.py:153) exige `class_group_id` só na
  //     CRIAÇÃO, e só com a flag ligada → 422 sem turma;
  //   - `update_assessment` (core/app/main.py:253) e
  //     `require_assessment_mutation` (core/app/routers/academic.py:165) NÃO
  //     consultam a flag e NÃO exigem turma: para `class_group_id === null`
  //     basta ser dono (ou admin) — editar/salvar/publicar um rascunho legado
  //     continua permitido com o módulo ligado.
  // A UI estava MAIS RESTRITIVA que o backend: exigia turma em qualquer
  // salvamento com o módulo ligado, inclusive de um rascunho legado que o
  // servidor aceitaria. Alinhamos a exigência à regra real do servidor.
  //
  // `assessment !== null` é deliberado: se a carga da avaliação falhou, não
  // sabemos que é legada e mantemos a exigência (conservador).
  const isLegacyAssessmentWithoutClass = Boolean(editing && assessment && !assessment.class_group_id)
  const classGroupRequired = academicModuleEnabled && !isLegacyAssessmentWithoutClass

  const complete = Boolean(
    title.trim() &&
    localQuestions.length > 0 &&
    allQuestionsValid &&
    (!classGroupRequired || Boolean(classGroupId))
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
    // Defesa em profundidade (item (3) do achado do Codex): mesmo que algum
    // caminho futuro de UI chame persist() antes de a capacidade ser conhecida,
    // nada é persistido. Hoje o formulário nem chega a ser renderizado nesse
    // estado, mas a guarda fica aqui porque este é o ponto de ESCRITA.
    if (capabilitiesLoading) {
      setError('Aguarde: ainda estamos verificando a configuração do módulo acadêmico.')
      return
    }
    // Defesa em profundidade para a falha DEFINITIVA (lacuna 1). Mesma razão do
    // guarda acima: sem a configuração confirmada não sabemos se a turma é
    // obrigatória, e escrever "no escuro" é exatamente o que o fail-closed
    // precisa impedir. Hoje o formulário também não é renderizado neste estado.
    if (capabilitiesError) {
      setError('Não foi possível confirmar a configuração do módulo acadêmico. Tente novamente antes de salvar.')
      return
    }
    if (classGroupRequired && !classGroupId) {
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
  // Decisão de UX (correção do achado do Codex, itens (2) e (3)): enquanto a
  // capacidade é DESCONHECIDA, substituímos o formulário inteiro por um
  // Spinner, em vez de apenas desabilitar os botões. Três razões: (a) é o
  // idioma já usado neste arquivo para "ainda não dá para editar"; (b) desabilitar
  // só os botões ainda deixaria o usuário preencher a avaliação toda para só
  // então descobrir que falta turma — pior UX que esperar alguns milissegundos;
  // (c) com o formulário fora da árvore, `complete` e os handlers de submit
  // ficam inalcançáveis, de modo que a janela de escrita simplesmente não
  // existe, em vez de depender de um `disabled` correto em cada botão.
  // Depois que capabilitiesLoading vira false, o comportamento é EXATAMENTE o
  // de antes para os dois valores definitivos de academicModuleEnabled.
  if (capabilitiesLoading) return <Spinner label="Verificando configuração do módulo acadêmico…" />

  // SANEAMENTO (lacuna 1, 2026-10-13): falha DEFINITIVA ≠ "módulo desligado".
  // Aqui a consulta já terminou e fracassou, então um spinner mentiria (nada
  // mais está em curso) e abrir o formulário mentiria pior ainda (afirmaria
  // "turma é opcional" sem nunca ter obtido a configuração real). Mostramos o
  // que de fato aconteceu e oferecemos a única ação útil: tentar novamente.
  if (capabilitiesError) {
    return (
      <>
        <div className="page-heading">
          <div>
            <Link className="back-link" to="/avaliacoes">
              ← Avaliações
            </Link>
            <p className="eyebrow">Configuração não confirmada</p>
            <h1>Não foi possível verificar a configuração do módulo acadêmico</h1>
          </div>
        </div>
        <Alert>
          O servidor não respondeu à consulta de configuração do módulo acadêmico. Sem essa resposta não
          sabemos se vincular uma turma é obrigatório nesta instalação, e por isso o editor não foi aberto:
          você poderia preencher a avaliação inteira e ter o salvamento recusado no fim. Isto não significa
          que o módulo acadêmico esteja desligado — significa que ainda não sabemos.
        </Alert>
        <section className="panel">
          <p>Verifique sua conexão e se o servidor do AvalIA está disponível, e tente novamente.</p>
          <button type="button" className="button button--primary" onClick={retryCapabilities}>
            Tentar novamente
          </button>
        </section>
      </>
    )
  }

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
            Turma vinculada{classGroupRequired ? ' (obrigatória)' : ' (opcional)'}
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <select
                required={classGroupRequired}
                value={classGroupId}
                onChange={e => setClassGroupId(e.target.value)}
                style={{ flex: 1 }}
                disabled={isPublished}
              >
                <option value="">
                  {classGroupRequired ? 'Selecione uma turma obrigatória...' : 'Selecione uma turma (opcional)...'}
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
            {classGroupRequired && !classGroupId && (
              <small style={{ color: '#c53030', display: 'block', marginTop: '0.25rem' }}>
                Turma é obrigatória para novas avaliações quando o módulo acadêmico está ativo.
              </small>
            )}
            {/* ACH-01: avaliação criada antes do módulo acadêmico. O backend
                permite continuar editando sem turma (DEC-AV-023); a UI explica
                isso em vez de bloquear, e o botão "Vincular turma" acima segue
                disponível para quem quiser regularizar. */}
            {isLegacyAssessmentWithoutClass && academicModuleEnabled && !classGroupId && (
              <small style={{ color: '#92400e', display: 'block', marginTop: '0.25rem' }}>
                Esta avaliação foi criada antes da ativação do módulo acadêmico e não tem turma vinculada.
                Você pode continuar editando sem turma; se quiser vinculá-la a uma turma, selecione acima e
                use “Vincular turma”.
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
                    : classGroupRequired && !classGroupId
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
