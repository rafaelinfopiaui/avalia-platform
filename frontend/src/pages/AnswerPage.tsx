import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { createAnswer, requestCorrection } from '../services/api'
import { readWorkflow, writeWorkflow } from '../services/workflow'

export function AnswerPage() {
  const { id } = useParams(); const navigate = useNavigate(); const assessment = readWorkflow().assessment
  const question = assessment?.question || assessment?.questions?.[0]
  const [student, setStudent] = useState('Aluno fictício'); const [text, setText] = useState(''); const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  const submit = async (event: FormEvent) => { event.preventDefault(); if (!question?.id) { setError('Não foi possível identificar a questão. Volte à avaliação e tente novamente.'); return } setBusy(true); setError(''); try { const answer = await createAnswer({ question_id: question.id, student_name: student, text }); const job = await requestCorrection(answer.id); writeWorkflow({ answer, job }); navigate(`/correcoes/${job.id}`) } catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível solicitar a análise.') } finally { setBusy(false) } }
  return <><Link className="back-link" to={id ? `/avaliacoes/${id}` : '/avaliacoes'}>← Voltar à avaliação</Link><div className="page-heading"><div><p className="eyebrow">Avaliação publicada</p><h1>Inserir resposta</h1><p>Registre a resposta digital de um aluno fictício para solicitar a análise assistida.</p></div></div>
    {error && <Alert>{error}</Alert>}{question ? <div className="two-column"><aside className="panel question-preview"><span className="label">Questão</span><h2>{question.statement}</h2><p><strong>Valor:</strong> {question.max_score.toLocaleString('pt-BR')} pontos</p></aside><form className="panel form-stack" onSubmit={submit}><label>Identificação fictícia do aluno<input required value={student} onChange={e => setStudent(e.target.value)} /></label><label>Resposta do aluno<textarea rows={10} required minLength={2} value={text} onChange={e => setText(e.target.value)} placeholder="Digite a resposta exatamente como foi entregue" /></label><button className="button button--ai" disabled={busy}>{busy ? 'Solicitando análise…' : 'Solicitar análise da IA'}</button><small>A IA fará uma sugestão. A nota só será definida após sua revisão.</small></form></div> : <Alert>Os dados da questão não estão disponíveis nesta sessão. Abra a avaliação pela lista e tente novamente.</Alert>}
  </>
}
