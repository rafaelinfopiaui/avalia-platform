import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { Spinner } from '../components/Spinner'
import { ApiError, createImageAnswer, downloadAnswerImage, listAnswerImages, listAssessments } from '../services/api'
import type { AnswerImage, AnswerWithImages, Assessment } from '../types'

// Resposta por imagem (AV-S06B, DEC-AV-037): a foto é a entrada inicial da
// resposta, sem texto digitado. A resposta fica aguardando transcrição e NÃO é
// encaminhada para correção nesta tela. Avaliação, questão e aluno são
// escolhidos manualmente pelo professor (DEC-AV-021).

// Mesmo limite do backend: 10 MiB = 10_485_760 bytes (base binária).
const MAX_IMAGE_BYTES = 10 * 1024 * 1024
const ACCEPTED_TYPES = ['image/jpeg', 'image/png']
const PENDING_TRANSCRIPTION_NOTICE =
  'Imagem recebida e armazenada. A resposta aguarda transcrição — ainda NÃO foi transcrita nem corrigida.'

function isPublished(assessment: Assessment) {
  return assessment.status === 'PUBLICADA' || assessment.status === 'PUBLISHED'
}

function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} MiB`
  return `${Math.max(1, Math.round(bytes / 1024)).toLocaleString('pt-BR')} KiB`
}

function humanError(error: unknown, action: 'enviar' | 'carregar'): string {
  if (!(error instanceof ApiError)) return action === 'enviar' ? 'Não foi possível enviar a imagem. Tente novamente.' : 'Não foi possível carregar a imagem. Tente novamente.'
  switch (error.status) {
    case 0: return error.message
    case 401: return 'Sua sessão expirou. Entre novamente e repita o envio.'
    case 403: return 'Você não tem permissão para registrar respostas nesta avaliação. Verifique se você é o responsável pela avaliação ou tem vínculo ativo com a turma.'
    case 404: return 'Avaliação, questão ou imagem não encontrada. Atualize a página e selecione novamente.'
    case 413: return 'A imagem excede o limite de 10 MiB. Reduza a resolução ou comprima a foto e envie novamente.'
    case 422: return `${error.body.message || 'Arquivo inválido.'} Envie uma foto JPEG ou PNG legível e confira os campos.`
    default: return action === 'enviar'
      ? 'Não foi possível armazenar a imagem. Nenhuma resposta foi registrada; tente novamente.'
      : 'Não foi possível carregar a imagem. Tente novamente.'
  }
}

function validateFile(file: File | null): string {
  if (!file) return 'Selecione a foto da resposta.'
  if (!ACCEPTED_TYPES.includes(file.type)) return 'Apenas fotos JPEG ou PNG são aceitas.'
  if (file.size === 0) return 'O arquivo selecionado está vazio.'
  if (file.size > MAX_IMAGE_BYTES) return 'A imagem excede o limite de 10 MiB. Reduza a resolução ou comprima a foto.'
  return ''
}

function ImageViewer({ image }: { image: AnswerImage }) {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => () => { if (url) URL.revokeObjectURL(url) }, [url])

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const blob = await downloadAnswerImage(image.id)
      setUrl(URL.createObjectURL(blob))
    } catch (e) {
      setError(humanError(e, 'carregar'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <li className="panel" style={{ listStyle: 'none', marginBottom: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span>
          <strong>{image.original_filename}</strong> · {image.content_type === 'image/png' ? 'PNG' : 'JPEG'} · {formatSize(image.size_bytes)} · enviada em {new Date(image.created_at).toLocaleString('pt-BR')}
        </span>
        {!url && (
          <button type="button" className="button button--secondary" onClick={load} disabled={loading}>
            {loading ? 'Carregando…' : 'Visualizar'}
          </button>
        )}
      </div>
      {loading && <Spinner label="Baixando imagem…" />}
      {error && <Alert>{error} <button type="button" className="link-button" onClick={load}>Tentar novamente</button></Alert>}
      {url && <img src={url} alt={`Foto da resposta (${image.original_filename})`} style={{ display: 'block', maxWidth: '100%', marginTop: '0.75rem', borderRadius: '4px' }} />}
    </li>
  )
}

function SentAnswer({ answer, questionLabel }: { answer: AnswerWithImages; questionLabel: string }) {
  const [images, setImages] = useState<AnswerImage[]>(answer.images)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const refresh = async () => {
    setLoading(true)
    setError('')
    try {
      setImages(await listAnswerImages(answer.id))
    } catch (e) {
      setError(humanError(e, 'carregar'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <article className="panel" style={{ marginBottom: '1rem' }}>
      <p className="eyebrow">Aguardando transcrição</p>
      <h3 style={{ marginTop: 0 }}>{answer.student_name_fake} — {questionLabel}</h3>
      <p><small>Resposta {answer.id}</small></p>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <strong>Imagens armazenadas ({images.length})</strong>
        <button type="button" className="link-button" onClick={refresh} disabled={loading}>
          {loading ? 'Atualizando…' : 'Atualizar lista'}
        </button>
      </div>
      {error && <Alert>{error}</Alert>}
      <ul style={{ padding: 0, marginTop: '0.75rem' }}>
        {images.map(image => <ImageViewer key={image.id} image={image} />)}
      </ul>
    </article>
  )
}

export function ImageAnswerPage() {
  const [searchParams] = useSearchParams()
  const [assessments, setAssessments] = useState<Assessment[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [assessmentId, setAssessmentId] = useState(searchParams.get('avaliacao') || '')
  const [questionId, setQuestionId] = useState('')
  const [student, setStudent] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [sent, setSent] = useState<{ answer: AnswerWithImages; questionLabel: string }[]>([])
  const fileInput = useRef<HTMLInputElement>(null)

  const load = () => {
    setLoading(true)
    setLoadError('')
    listAssessments()
      .then(items => setAssessments(items.filter(isPublished)))
      .catch(e => setLoadError(e instanceof Error ? e.message : 'Não foi possível carregar as avaliações.'))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const assessment = assessments.find(item => item.id === assessmentId)
  const questions = assessment?.questions || []
  const questionIndex = questions.findIndex(q => q.id === questionId)
  const question = questionIndex >= 0 ? questions[questionIndex] : undefined
  const questionLabel = question ? `Questão ${question.position || questionIndex + 1}` : ''

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (busy) return
    if (!question?.id) { setError('Selecione a avaliação e a questão.'); return }
    if (!student.trim()) { setError('Informe a identificação fictícia do aluno.'); return }
    const fileError = validateFile(file)
    if (fileError || !file) { setError(fileError); return }
    setBusy(true)
    setError('')
    try {
      const answer = await createImageAnswer({ question_id: question.id, student_name: student.trim(), file })
      setSent(previous => [{ answer, questionLabel }, ...previous])
      setFile(null)
      setStudent('')
      if (fileInput.current) fileInput.current.value = ''
    } catch (e) {
      setError(humanError(e, 'enviar'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Link className="back-link" to="/avaliacoes">← Voltar às avaliações</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Avaliação publicada</p>
          <h1>Resposta por foto</h1>
          <p>Envie a foto da resposta manuscrita de um aluno fictício. A foto é registrada como a resposta e fica aguardando transcrição.</p>
        </div>
      </div>
      {loadError && <Alert>{loadError} <button type="button" className="link-button" onClick={load}>Tentar novamente</button></Alert>}
      {error && <Alert>{error}</Alert>}
      {sent.length > 0 && <Alert type="warning">{PENDING_TRANSCRIPTION_NOTICE}</Alert>}

      {loading ? (
        <Spinner label="Carregando avaliações…" />
      ) : !loadError && assessments.length === 0 ? (
        <Alert type="info">Nenhuma avaliação publicada disponível. Publique uma avaliação para registrar respostas.</Alert>
      ) : !loadError ? (
        <div className="two-column">
          <form className="panel form-stack" onSubmit={submit}>
            <label>
              Avaliação
              <select value={assessmentId} onChange={e => { setAssessmentId(e.target.value); setQuestionId('') }} disabled={busy} required>
                <option value="" disabled>Selecione uma avaliação...</option>
                {assessments.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}
              </select>
            </label>
            <label>
              Questão
              <select value={questionId} onChange={e => setQuestionId(e.target.value)} disabled={busy || !assessment} required>
                <option value="" disabled>Selecione uma questão...</option>
                {questions.map((q, i) => <option key={q.id} value={q.id}>Questão {q.position || i + 1}</option>)}
              </select>
            </label>
            {question && <p><small>{question.statement}</small></p>}
            <label>
              Identificação fictícia do aluno
              <input value={student} onChange={e => setStudent(e.target.value)} disabled={busy || !question} required placeholder="Ex.: Aluno A" />
            </label>
            <label>
              Foto da resposta (JPEG ou PNG, até 10 MiB)
              <input
                ref={fileInput}
                type="file"
                accept="image/jpeg,image/png"
                onChange={e => { setFile(e.target.files?.[0] || null); setError('') }}
                disabled={busy || !question}
                required
              />
            </label>
            {file && <small>{file.name} · {formatSize(file.size)}</small>}
            <button className="button button--primary" disabled={busy || !question}>
              {busy ? 'Enviando imagem…' : 'Enviar foto da resposta'}
            </button>
            {busy && <Spinner label="Enviando e armazenando a imagem…" />}
            <small>Uma foto por resposta de uma questão. A resposta ficará aguardando transcrição.</small>
          </form>

          <section>
            <h2>Respostas enviadas nesta sessão</h2>
            {sent.length === 0 ? (
              <p>Nenhuma resposta por foto enviada ainda.</p>
            ) : (
              sent.map(item => <SentAnswer key={item.answer.id} answer={item.answer} questionLabel={item.questionLabel} />)
            )}
          </section>
        </div>
      ) : null}
    </>
  )
}
