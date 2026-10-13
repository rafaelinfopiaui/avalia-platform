import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { Spinner } from '../components/Spinner'
import { createAnswer, getAssessment, requestCorrection } from '../services/api'
import { readWorkflow, writeWorkflow } from '../services/workflow'
import type { Assessment } from '../types'

// O cache local (sessionStorage) só é populado quando a avaliação é
// criada/editada/publicada nesta mesma aba (AssessmentEditorPage). Chegar aqui
// por qualquer outro caminho — link direto da lista, recarregar a página, abrir
// uma aba nova — deixa esse cache vazio ou com os dados de OUTRA avaliação, e a
// tela ficava presa em "Os dados da avaliação não possuem questões
// disponíveis." mesmo com a avaliação publicada e válida no backend. Só
// confiamos no cache quando ele é exatamente desta avaliação e já traz as
// questões; qualquer outro caso busca da API.
function cachedAssessment(id?: string) {
  const candidate = readWorkflow().assessment
  if (!id || candidate?.id !== id || !candidate.questions?.length) return undefined
  return candidate
}

export function AnswerPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [assessment, setAssessment] = useState<Assessment | undefined>(() => cachedAssessment(id))
  const [loadError, setLoadError] = useState('')
  const [selectedQuestionId, setSelectedQuestionId] = useState<string>('')

  useEffect(() => {
    if (!id) return
    // Trocar de avaliação sem desmontar a página (A → B) deixaria a questão
    // escolhida em A selecionada sob a URL de B.
    setSelectedQuestionId('')
    setLoadError('')
    const hit = cachedAssessment(id)
    if (hit) {
      setAssessment(hit)
      return
    }
    let active = true
    getAssessment(id)
      .then(data => {
        if (!active) return
        setAssessment(data)
        writeWorkflow({ assessment: data })
      })
      .catch(e => {
        if (!active) return
        setLoadError(e instanceof Error ? e.message : 'Não foi possível carregar a avaliação.')
      })
    return () => { active = false }
  }, [id])

  // O efeito acima só roda depois da renderização: no primeiro render após uma
  // troca de id, `assessment` ainda é o da avaliação anterior. Filtrar por id
  // aqui impede que os dados de A apareçam, mesmo que por um frame, sob a URL
  // de B — nesse intervalo a tela mostra o carregamento.
  const current = assessment?.id === id ? assessment : undefined
  const loading = Boolean(id) && !current && !loadError
  const questions = current?.questions || []
  const assessmentMaxScore = current?.assessment_max_score || questions.reduce((s, q) => s + (Number(q.max_score) || 0), 0)

  const [student, setStudent] = useState('Aluno fictício')
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const selectedQuestion = questions.find(q => q.id === selectedQuestionId)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!selectedQuestion?.id) {
      setError('Selecione uma questão.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const answer = await createAnswer({ question_id: selectedQuestion.id, student_name: student, text })
      const job = await requestCorrection(answer.id)
      writeWorkflow({ answer, job })
      navigate(`/correcoes/${job.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Não foi possível solicitar a análise.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Link className="back-link" to={id ? `/avaliacoes/${id}` : '/avaliacoes'}>← Voltar à avaliação</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Avaliação publicada</p>
          <h1>Inserir resposta</h1>
          <p>Registre a resposta digital de um aluno fictício para solicitar a análise assistida.</p>
        </div>
      </div>
      {error && <Alert>{error}</Alert>}
      {loadError && <Alert>{loadError}</Alert>}

      {loading ? (
        <Spinner label="Carregando dados da avaliação…" />
      ) : questions.length > 0 ? (
        <div className="two-column">
          <aside className="panel question-preview">
            <span className="label">Questão</span>
            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="question-select" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                Selecione a questão a ser respondida
              </label>
              <select
                id="question-select"
                value={selectedQuestionId}
                onChange={e => setSelectedQuestionId(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
              >
                <option value="" disabled>Selecione uma questão...</option>
                {questions.map((q, i) => (
                  <option key={q.id} value={q.id}>
                    Questão {q.position || i + 1}
                  </option>
                ))}
              </select>
            </div>

            {selectedQuestion && (
              <>
                <h2>{selectedQuestion.statement}</h2>
                <p><strong>Valor da questão:</strong> {selectedQuestion.max_score.toLocaleString('pt-BR')} pontos</p>
                <div style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
                  <p><strong>Pontuação máxima da avaliação:</strong> {assessmentMaxScore.toLocaleString('pt-BR')} pontos</p>
                </div>
              </>
            )}
            {!selectedQuestion && (
              <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f3f4f6', borderRadius: '4px', fontStyle: 'italic', color: '#4b5563' }}>
                Selecione uma questão acima para visualizar seu enunciado.
              </div>
            )}
          </aside>

          <form className="panel form-stack" onSubmit={submit}>
            <label>
              Identificação fictícia do aluno
              <input required value={student} onChange={e => setStudent(e.target.value)} disabled={!selectedQuestion} />
            </label>
            <label>
              Resposta do aluno
              <textarea rows={10} required minLength={2} value={text} onChange={e => setText(e.target.value)} placeholder="Digite a resposta exatamente como foi entregue" disabled={!selectedQuestion} />
            </label>
            <button className="button button--ai" disabled={!selectedQuestion || busy}>
              {busy ? 'Solicitando análise…' : 'Solicitar análise da IA'}
            </button>
            <small>A IA fará uma sugestão. A nota só será definida após sua revisão.</small>
          </form>
        </div>
      ) : !loadError ? (
        <Alert>Os dados da avaliação não possuem questões disponíveis. Abra a avaliação pela lista e tente novamente.</Alert>
      ) : null}
    </>
  )
}
