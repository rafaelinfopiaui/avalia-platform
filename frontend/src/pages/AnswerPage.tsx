import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { createAnswer, requestCorrection } from '../services/api'
import { readWorkflow, writeWorkflow } from '../services/workflow'

export function AnswerPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const assessment = readWorkflow().assessment

  const questions = assessment?.questions || []
  const assessmentMaxScore = assessment?.assessment_max_score || questions.reduce((s, q) => s + (Number(q.max_score) || 0), 0)

  const [selectedQuestionId, setSelectedQuestionId] = useState<string>('')
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

      {questions.length > 0 ? (
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
              <input required value={student} onChange={e => setStudent(e.target.value)} disabled={!selectedQuestionId} />
            </label>
            <label>
              Resposta do aluno
              <textarea rows={10} required minLength={2} value={text} onChange={e => setText(e.target.value)} placeholder="Digite a resposta exatamente como foi entregue" disabled={!selectedQuestionId} />
            </label>
            <button className="button button--ai" disabled={!selectedQuestionId || busy}>
              {busy ? 'Solicitando análise…' : 'Solicitar análise da IA'}
            </button>
            <small>A IA fará uma sugestão. A nota só será definida após sua revisão.</small>
          </form>
        </div>
      ) : (
        <Alert>Os dados da avaliação não possuem questões disponíveis. Abra a avaliação pela lista e tente novamente.</Alert>
      )}
    </>
  )
}
