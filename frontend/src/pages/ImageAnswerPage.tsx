import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { Spinner } from '../components/Spinner'
import { useAuth } from '../context/AuthContext'
import {
  ApiError,
  confirmManualTranscription,
  createImageAnswer,
  downloadAnswerImage,
  listAnswerImages,
  listAssessments,
  listImageAnswers,
  requestCorrection,
  saveManualTranscriptionDraft,
} from '../services/api'
import { writeWorkflow } from '../services/workflow'
import type { AnswerImage, AnswerWithImages, Assessment } from '../types'

// Resposta por imagem (AV-S06B, DEC-AV-037): a foto é a entrada inicial da
// resposta, sem texto digitado. A resposta fica aguardando transcrição e NÃO é
// encaminhada para correção nesta tela. Avaliação, questão e aluno são
// escolhidos manualmente pelo professor (DEC-AV-021).
// Transcrição manual (AV-S08B, DEC-AV-040): o professor digita o texto, salva
// rascunhos e confirma explicitamente; a confirmação é definitiva e não inicia
// a correção.
// Após a confirmação, a análise da IA é solicitada por ação explícita, a partir
// da MESMA resposta (POST /answers/{id}/corrections), usando o texto confirmado.

// Mesmo limite do backend: 10 MiB = 10_485_760 bytes (base binária).
const MAX_IMAGE_BYTES = 10 * 1024 * 1024
const ACCEPTED_TYPES = ['image/jpeg', 'image/png']
const PENDING_TRANSCRIPTION_NOTICE =
  'Imagem recebida e armazenada. A resposta aguarda transcrição — ainda NÃO foi transcrita nem corrigida.'
const CONFIRMATION_WARNING =
  'Atenção: a confirmação é definitiva nesta versão. Depois de confirmar, a transcrição não poderá mais ser editada. Confira a imagem e o texto lado a lado antes de continuar.'

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

// Mensagens da consulta (leitura): não falam em "registrar" nem exigem vínculo.
function listError(error: unknown): string {
  if (!(error instanceof ApiError)) return 'Não foi possível carregar as respostas por foto.'
  switch (error.status) {
    case 0: return error.message
    case 401: return 'Sua sessão expirou. Entre novamente para consultar as respostas por foto.'
    case 403: return 'Você não tem permissão para consultar as respostas desta avaliação.'
    case 404: return 'Avaliação ou questão não encontrada. Atualize a página e selecione novamente.'
    default: return 'Não foi possível carregar as respostas por foto.'
  }
}

function validateFile(file: File | null): string {
  if (!file) return 'Selecione a foto da resposta.'
  if (!ACCEPTED_TYPES.includes(file.type)) return 'Apenas fotos JPEG ou PNG são aceitas.'
  if (file.size === 0) return 'O arquivo selecionado está vazio.'
  if (file.size > MAX_IMAGE_BYTES) return 'A imagem excede o limite de 10 MiB. Reduza a resolução ou comprima a foto.'
  return ''
}

// Mensagens das ações de transcrição (mutação: exigem vínculo ativo).
function transcriptionError(error: unknown, action: 'salvar' | 'confirmar'): string {
  const fallback = `Não foi possível ${action} a transcrição. Tente novamente.`
  if (!(error instanceof ApiError)) return fallback
  switch (error.body.code) {
    case 'TRANSCRIPTION_VERSION_CONFLICT': return 'Este texto foi alterado em outra sessão ou aba. Carregue a versão mais recente para continuar — o texto digitado aqui NÃO foi salvo (copie-o antes, se precisar).'
    case 'TRANSCRIPTION_ALREADY_CONFIRMED': return 'Esta transcrição já foi confirmada (possivelmente em outra sessão) e não pode mais ser alterada.'
    case 'ANSWER_TEXT_REQUIRED': return 'Digite o texto da transcrição antes de confirmar.'
    case 'ANSWER_NOT_IMAGE_SOURCE': return 'Esta resposta não foi enviada por foto; não há transcrição manual a fazer.'
  }
  switch (error.status) {
    case 0: return error.message
    case 401: return 'Sua sessão expirou. Entre novamente para continuar a transcrição.'
    case 403: return 'Você não tem permissão para alterar respostas desta avaliação. Verifique se você é o responsável pela avaliação e tem vínculo ativo com a turma.'
    case 404: return 'Resposta não encontrada. Atualize a página e selecione novamente.'
    default: return fallback
  }
}

// Mensagens da solicitação de análise da IA a partir da resposta confirmada.
function correctionError(error: unknown): string {
  const fallback = 'Não foi possível solicitar a análise da IA. Tente novamente.'
  if (!(error instanceof ApiError)) return fallback
  switch (error.body.code) {
    case 'ANSWER_NOT_TRANSCRIBED': return 'A transcrição desta resposta ainda não foi confirmada; confirme-a antes de solicitar a análise.'
    case 'RUBRIC_NOT_PUBLISHED': return 'A questão desta resposta não possui rubrica publicada. Publique a rubrica da questão e tente novamente.'
  }
  switch (error.status) {
    case 0: return error.message
    case 401: return 'Sua sessão expirou. Entre novamente e solicite a análise outra vez.'
    case 403: return 'Você não tem permissão para solicitar a análise desta resposta. Verifique se você é o responsável pela avaliação e tem vínculo ativo com a turma.'
    case 404: return 'Resposta não encontrada. Atualize a página e selecione novamente.'
    default: return fallback
  }
}

// Em 409 o backend devolve o estado atual da resposta em details.current_answer.
function conflictState(error: unknown): AnswerWithImages | null {
  if (!(error instanceof ApiError) || error.status !== 409) return null
  const current = error.body.details?.current_answer
  return current && typeof current === 'object' ? (current as AnswerWithImages) : null
}

function ImageViewer({ image, autoLoad = false }: { image: AnswerImage; autoLoad?: boolean }) {
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (autoLoad) load() }, [autoLoad])

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

const sideBySide = { display: 'flex', gap: '1rem', flexWrap: 'wrap' } as const
const sideBySideItem = { flex: '1 1 260px', minWidth: 0 } as const
const transcriptBox = { whiteSpace: 'pre-wrap', margin: '0.5rem 0', padding: '0.75rem', border: '1px solid #ccc', borderRadius: '4px' } as const

function ManualTranscription({ answer, images, onChange }: {
  answer: AnswerWithImages
  images: AnswerImage[]
  onChange: (answer: AnswerWithImages) => void
}) {
  const { user } = useAuth()
  const [text, setText] = useState(answer.manual_transcription_draft || '')
  const [busy, setBusy] = useState<'' | 'salvar' | 'confirmar'>('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [reviewing, setReviewing] = useState(false)
  // Estado mais recente devolvido por um conflito de versão, aplicado só a pedido.
  const [latest, setLatest] = useState<AnswerWithImages | null>(null)

  if (answer.transcription_status === 'TRANSCRICAO_CONFIRMADA') {
    const by = answer.transcription_confirmed_by_id
    const who = !by ? '' : by === user?.id ? ' por você' : ` pelo usuário ${by}`
    const when = answer.transcription_confirmed_at ? ` em ${new Date(answer.transcription_confirmed_at).toLocaleString('pt-BR')}` : ''
    return (
      <section style={{ marginTop: '1rem' }}>
        <strong>Transcrição confirmada</strong>
        <p><small>Confirmada{who}{when}. A confirmação é definitiva nesta versão; o texto não pode mais ser editado.</small></p>
        <div style={transcriptBox}>{answer.text}</div>
      </section>
    )
  }

  const savedDraft = answer.manual_transcription_draft || ''
  const dirty = text !== savedDraft

  const fail = (e: unknown, action: 'salvar' | 'confirmar') => {
    setError(transcriptionError(e, action))
    const current = conflictState(e)
    if (current?.transcription_status === 'TRANSCRICAO_CONFIRMADA') {
      setReviewing(false)
      onChange(current)
    } else if (current) {
      setReviewing(false)
      setLatest(current)
    }
  }

  const saveDraft = async () => {
    if (busy) return
    setBusy('salvar')
    setError('')
    setNotice('')
    try {
      const updated = await saveManualTranscriptionDraft(answer.id, text, answer.transcription_version)
      onChange(updated)
      setText(updated.manual_transcription_draft || '')
      setNotice(updated.manual_transcription_draft ? 'Rascunho salvo. Ele continua disponível se você recarregar a página.' : 'Rascunho limpo.')
    } catch (e) {
      fail(e, 'salvar')
    } finally {
      setBusy('')
    }
  }

  const startReview = () => {
    setNotice('')
    if (!text.trim()) { setError('Digite o texto da transcrição antes de confirmar.'); return }
    setError('')
    setReviewing(true)
  }

  const confirm = async () => {
    if (busy) return
    setBusy('confirmar')
    setError('')
    try {
      onChange(await confirmManualTranscription(answer.id, text, answer.transcription_version))
    } catch (e) {
      fail(e, 'confirmar')
    } finally {
      setBusy('')
    }
  }

  const loadLatest = () => {
    if (!latest) return
    onChange(latest)
    setText(latest.manual_transcription_draft || '')
    setLatest(null)
    setError('')
    setNotice('Versão mais recente carregada.')
  }

  return (
    <section style={{ marginTop: '1rem' }}>
      <label className="form-stack">
        <strong>Transcrição manual</strong>
        <textarea
          rows={8}
          value={text}
          onChange={e => { setText(e.target.value); setNotice('') }}
          placeholder="Digite o texto da resposta exatamente como está na foto"
          disabled={Boolean(busy) || reviewing}
        />
      </label>
      <small>
        {dirty ? 'Há alterações não salvas.' : savedDraft ? 'Rascunho salvo.' : 'Nenhum rascunho salvo.'} O rascunho não confirma a transcrição nem libera a correção.
      </small>
      {error && (
        <Alert>
          {error}{' '}
          {latest && <button type="button" className="link-button" onClick={loadLatest}>Carregar versão mais recente</button>}
        </Alert>
      )}
      {notice && <Alert type="success">{notice}</Alert>}
      {!reviewing ? (
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginTop: '0.75rem' }}>
          <button type="button" className="button button--secondary" onClick={saveDraft} disabled={Boolean(busy) || !dirty || Boolean(latest)}>
            {busy === 'salvar' ? 'Salvando rascunho…' : 'Salvar rascunho'}
          </button>
          <button type="button" className="button button--primary" onClick={startReview} disabled={Boolean(busy) || Boolean(latest)}>
            Confirmar transcrição…
          </button>
        </div>
      ) : (
        <div className="panel" style={{ marginTop: '0.75rem' }}>
          <h4 style={{ marginTop: 0 }}>Revisão final antes de confirmar</h4>
          <Alert type="warning">{CONFIRMATION_WARNING}</Alert>
          <div style={sideBySide}>
            <div style={sideBySideItem}>
              <strong>Imagem da resposta</strong>
              <ul style={{ padding: 0, marginTop: '0.5rem' }}>
                {images.map(image => <ImageViewer key={image.id} image={image} autoLoad />)}
              </ul>
            </div>
            <div style={sideBySideItem}>
              <strong>Texto que será confirmado</strong>
              <div style={transcriptBox}>{text}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button type="button" className="button button--primary" onClick={confirm} disabled={Boolean(busy)}>
              {busy === 'confirmar' ? 'Confirmando…' : 'Confirmar definitivamente'}
            </button>
            <button type="button" className="button button--secondary" onClick={() => setReviewing(false)} disabled={Boolean(busy)}>
              Voltar à edição
            </button>
          </div>
          <small>Confirmar não inicia a correção; a análise continua sendo uma ação separada.</small>
        </div>
      )}
    </section>
  )
}

// Sem endpoint de leitura de jobs por resposta, o "já solicitada" só vale para
// as solicitações feitas nesta tela, nesta sessão.
function CorrectionRequest({ answer }: { answer: AnswerWithImages }) {
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [requested, setRequested] = useState(false)

  const request = async () => {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      const job = await requestCorrection(answer.id)
      setRequested(true)
      writeWorkflow({ answer, job })
      navigate(`/correcoes/${job.id}`)
    } catch (e) {
      setError(correctionError(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section style={{ marginTop: '1rem' }}>
      {error && <Alert>{error}</Alert>}
      {requested && <Alert type="success">Análise da IA já solicitada para esta resposta. Uma nova solicitação gera uma nova tentativa.</Alert>}
      <button type="button" className="button button--primary" onClick={request} disabled={busy}>
        {busy ? 'Solicitando análise…' : requested ? 'Solicitar nova análise da IA' : 'Solicitar análise da IA'}
      </button>
      {busy && <Spinner label="Solicitando a análise da IA…" />}
      <small style={{ display: 'block', marginTop: '0.5rem' }}>A análise usa exatamente o texto confirmado acima.</small>
    </section>
  )
}

function SentAnswer({ answer: initial, questionLabel }: { answer: AnswerWithImages; questionLabel: string }) {
  const [answer, setAnswer] = useState(initial)
  const [images, setImages] = useState<AnswerImage[]>(initial.images)
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
      <p className="eyebrow">{answer.transcription_status === 'TRANSCRICAO_CONFIRMADA' ? 'Transcrição confirmada' : 'Aguardando transcrição'}</p>
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
      <ManualTranscription answer={answer} images={images} onChange={setAnswer} />
      {answer.transcription_status === 'TRANSCRICAO_CONFIRMADA' && <CorrectionRequest answer={answer} />}
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
  // Envios desta sessão + respostas já persistidas no backend (retomada, DEBT-AV-014).
  const [sent, setSent] = useState<AnswerWithImages[]>([])
  const [persisted, setPersisted] = useState<AnswerWithImages[]>([])
  const [listLoading, setListLoading] = useState(false)
  const [listLoadError, setListLoadError] = useState('')
  const listRequest = useRef(0)
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
  const selectedAssessmentId = assessment?.id || ''

  const loadPersisted = () => {
    // Limpa antes de buscar e descarta respostas de seleções anteriores.
    const requestId = ++listRequest.current
    setPersisted([])
    setListLoadError('')
    if (!selectedAssessmentId) { setListLoading(false); return }
    setListLoading(true)
    listImageAnswers(selectedAssessmentId, questionId || undefined)
      .then(items => { if (requestId === listRequest.current) setPersisted(items) })
      .catch(e => { if (requestId === listRequest.current) setListLoadError(listError(e)) })
      .finally(() => { if (requestId === listRequest.current) setListLoading(false) })
  }
  useEffect(loadPersisted, [selectedAssessmentId, questionId])

  const labelFor = (id: string) => {
    const index = questions.findIndex(q => q.id === id)
    return index >= 0 ? `Questão ${questions[index].position || index + 1}` : 'Questão'
  }
  // Só respostas da seleção atual; sem duplicar o que foi enviado nesta sessão.
  const visibleAnswers = (() => {
    const byId = new Map<string, AnswerWithImages>()
    for (const item of [...sent, ...persisted]) {
      const inSelection = questionId ? item.question_id === questionId : questions.some(q => q.id === item.question_id)
      if (inSelection && !byId.has(item.id)) byId.set(item.id, item)
    }
    return [...byId.values()].sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
  })()

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
      setSent(previous => [answer, ...previous])
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
          <p>Envie a foto da resposta manuscrita de um aluno fictício. A foto é registrada como a resposta e fica aguardando transcrição; depois, digite e confirme a transcrição manualmente.</p>
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
            <h2>Respostas por foto desta seleção</h2>
            {!assessment ? (
              <p>Selecione uma avaliação para ver as respostas por foto já registradas.</p>
            ) : listLoading ? (
              <Spinner label="Carregando respostas por foto…" />
            ) : listLoadError ? (
              <Alert>{listLoadError} <button type="button" className="link-button" onClick={loadPersisted}>Tentar novamente</button></Alert>
            ) : visibleAnswers.length === 0 ? (
              <p>Nenhuma resposta por foto nesta seleção.</p>
            ) : (
              visibleAnswers.map(item => <SentAnswer key={item.id} answer={item} questionLabel={labelFor(item.question_id)} />)
            )}
          </section>
        </div>
      ) : null}
    </>
  )
}
