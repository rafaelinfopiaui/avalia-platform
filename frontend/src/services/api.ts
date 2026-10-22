import type {
  ApiErrorBody,
  Assessment,
  Answer,
  AnswerImage,
  AnswerWithImages,
  ClassGroup,
  CorrectionJob,
  Course,
  CourseDiscipline,
  Criterion,
  DeletedAnswerImage,
  Discipline,
  Enrollment,
  EnrollmentStatus,
  HumanReviewSummary,
  JobStatus,
  Organization,
  ProfessorClassLink,
  Student,
  User,
} from '../types'

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/v1').replace(/\/$/, '')
const ACCESS_TOKEN_KEY = 'avalia_access_token'
const REFRESH_TOKEN_KEY = 'avalia_refresh_token'

export class ApiError extends Error {
  constructor(public status: number, public body: ApiErrorBody) {
    super(body.message || defaultMessage(status))
    this.name = 'ApiError'
  }
}

function defaultMessage(status: number) {
  if (status === 401) return 'Sua sessão expirou. Entre novamente para continuar.'
  if (status === 403) return 'Você não tem permissão para acessar este recurso.'
  return 'Não foi possível concluir a operação. Tente novamente.'
}

function getToken() { return sessionStorage.getItem(ACCESS_TOKEN_KEY) }
export function hasSession() { return Boolean(getToken()) }
export function clearSession() { sessionStorage.removeItem(ACCESS_TOKEN_KEY); sessionStorage.removeItem(REFRESH_TOKEN_KEY) }

function parseJson(text: string): unknown {
  if (!text) return undefined
  try { return JSON.parse(text) } catch { return undefined }
}

// Envia a requisição autenticada e lança ApiError se a resposta não for 2xx.
// FormData (upload multipart) segue sem Content-Type explícito: o navegador
// define o boundary.
async function send(path: string, init: RequestInit = {}): Promise<Response> {
  const token = getToken()
  const headers = new Headers(init.headers)
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError(0, { message: 'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.' })
  }
  if (!response.ok) {
    const data = parseJson(await response.text())
    const raw = (data && typeof data === 'object' ? data : {}) as Record<string, unknown>
    const detailObj = raw.detail && typeof raw.detail === 'object' && !Array.isArray(raw.detail)
      ? (raw.detail as Record<string, unknown>)
      : null

    let extractedMessage: string | undefined = undefined
    if (typeof raw.message === 'string' && raw.message.trim()) {
      extractedMessage = raw.message
    } else if (detailObj && typeof detailObj.message === 'string' && detailObj.message.trim()) {
      extractedMessage = detailObj.message
    } else if (typeof raw.detail === 'string' && raw.detail.trim()) {
      extractedMessage = raw.detail
    } else if (Array.isArray(raw.detail) && raw.detail.length > 0) {
      const first = raw.detail[0]
      if (first && typeof first === 'object' && typeof (first as Record<string, unknown>).msg === 'string') {
        extractedMessage = (first as Record<string, unknown>).msg as string
      }
    }

    const body: ApiErrorBody = {
      code: typeof detailObj?.code === 'string' ? detailObj.code : (typeof raw.code === 'string' ? raw.code : undefined),
      message: extractedMessage || defaultMessage(response.status),
      correlation_id: typeof detailObj?.correlation_id === 'string'
        ? detailObj.correlation_id
        : (typeof raw.correlation_id === 'string' ? raw.correlation_id : undefined),
      details: raw.details && typeof raw.details === 'object' && !Array.isArray(raw.details)
        ? (raw.details as Record<string, unknown>)
        : undefined,
      field_errors: Array.isArray(detailObj?.field_errors)
        ? (detailObj.field_errors as ApiErrorBody['field_errors'])
        : (Array.isArray(raw.field_errors) ? (raw.field_errors as ApiErrorBody['field_errors']) : undefined),
    }
    if (response.status === 401) {
      // Evita disparar o evento repetidamente quando várias chamadas concorrentes
      // recebem 401 ao mesmo tempo (ex.: token expira com a tela fazendo polling +
      // outras chamadas em paralelo) — sem isso, múltiplos disparos de navegação
      // quase simultâneos contribuíam para o SecurityError de
      // history.replaceState() (>100 chamadas/10s) descrito no bug corrigido em
      // AuthContext.tsx. Só notifica se havia sessão para limpar.
      if (hasSession()) { clearSession(); window.dispatchEvent(new Event('avalia:unauthorized')) }
    }
    throw new ApiError(response.status, body)
  }
  return response
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await send(path, init)
  return parseJson(await response.text()) as T
}

export async function login(email: string, password: string) {
  const result = await request<{ access_token: string; refresh_token?: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
  sessionStorage.setItem(ACCESS_TOKEN_KEY, result.access_token)
  if (result.refresh_token) sessionStorage.setItem(REFRESH_TOKEN_KEY, result.refresh_token)
}
export const getMe = () => request<User>('/me')
export async function listAssessments(): Promise<Assessment[]> {
  const data = await request<Assessment[] | { items?: Assessment[]; assessments?: Assessment[] }>('/assessments')
  return Array.isArray(data) ? data : data.items || data.assessments || []
}
export const getAssessment = (id: string) => request<Assessment>(`/assessments/${id}`)
export const createAssessment = (payload: {
  title: string
  class_group_id?: string | null
  questions: Omit<import('../types').Question, 'id' | 'rubric' | 'rubrics' | 'position'>[]
}) => request<Assessment>('/assessments', { method: 'POST', body: JSON.stringify(payload) })
export const updateAssessment = (id: string, payload: unknown) => request<Assessment>(`/assessments/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
export const createQuestion = (assessmentId: string, payload: Omit<import('../types').Question, 'id' | 'rubric' | 'rubrics' | 'position'>) => request<import('../types').Question>(`/assessments/${assessmentId}/questions`, { method: 'POST', body: JSON.stringify(payload) })
export const updateQuestion = (questionId: string, payload: Omit<import('../types').Question, 'id' | 'rubric' | 'rubrics' | 'position'>) => request<import('../types').Question>(`/questions/${questionId}`, { method: 'PATCH', body: JSON.stringify(payload) })
export const deleteQuestion = (questionId: string) => request<void>(`/questions/${questionId}`, { method: 'DELETE' })
export const reorderQuestions = (assessmentId: string, questionIds: string[]) => request<Assessment>(`/assessments/${assessmentId}/questions/order`, { method: 'PUT', body: JSON.stringify({ question_ids: questionIds }) })
export const cloneAssessment = (assessmentId: string) => request<Assessment>(`/assessments/${assessmentId}/clone`, { method: 'POST' })
export const saveRubric = (questionId: string, criteria: Criterion[]) => request(`/questions/${questionId}/rubric`, { method: 'POST', body: JSON.stringify({ criteria: criteria.map(({ name, description, max_score }) => ({ name, description, max_score })) }) })
export const publishAssessment = (id: string) => request<{ status: 'PUBLICADA' }>(`/assessments/${id}/publish`, { method: 'POST' })
export const createAnswer = (payload: { question_id: string; student_name: string; text: string }) => request<Answer>('/answers', { method: 'POST', body: JSON.stringify({ question_id: payload.question_id, student_name_fake: payload.student_name, text: payload.text }) })
export async function requestCorrection(answerId: string): Promise<Pick<CorrectionJob, 'id' | 'status'>> {
  const result = await request<{ id?: string; job_id?: string; status: JobStatus }>(`/answers/${answerId}/corrections`, { method: 'POST' })
  // Defesa adicional: normaliza "id" a partir de "job_id" caso o backend retorne
  // apenas um dos dois campos (bug corrigido no Core, mas mantemos a normalização
  // aqui para não repetir a navegação para "/correcoes/undefined" caso volte a
  // divergir).
  const id = result.id || result.job_id
  if (!id) throw new ApiError(0, { message: 'O servidor não retornou um identificador para acompanhar a análise.' })
  return { id, status: result.status }
}
export const getCorrectionJob = (id: string) => request<CorrectionJob>(`/correction-jobs/${id}`)

// ---------------- Resposta por imagem (AV-S06B, DEC-AV-037) ----------------
// A foto é a entrada inicial da resposta: não há texto, e a resposta nasce
// aguardando transcrição (não pode ser corrigida até ter transcrição confirmada).
export const createImageAnswer = (payload: { question_id: string; student_name: string; file: File }) => {
  const form = new FormData()
  form.append('question_id', payload.question_id)
  form.append('student_name_fake', payload.student_name)
  form.append('file', payload.file)
  return request<AnswerWithImages>('/answers/image', { method: 'POST', body: form })
}
export const listAnswerImages = (answerId: string) => request<AnswerImage[]>(`/answers/${answerId}/images`)
// Retomada (DEBT-AV-014): respostas por imagem já persistidas da avaliação,
// opcionalmente restritas a uma questão. Somente leitura.
export const listImageAnswers = (assessmentId: string, questionId?: string) => {
  const query = questionId ? `?question_id=${encodeURIComponent(questionId)}` : ''
  return request<AnswerWithImages[]>(`/assessments/${encodeURIComponent(assessmentId)}/image-answers${query}`)
}
// Transcrição manual (AV-S08B, DEC-AV-040): expected_version é a versão que a
// tela carregou; se outra sessão a avançou, o backend responde 409 com o estado
// atual em details.current_answer. Confirmar é definitivo e não inicia correção.
export const saveManualTranscriptionDraft = (answerId: string, text: string, expectedVersion: number) =>
  request<AnswerWithImages>(`/answers/${encodeURIComponent(answerId)}/manual-transcription/draft`, {
    method: 'PATCH',
    body: JSON.stringify({ text, expected_version: expectedVersion }),
  })
export const confirmManualTranscription = (answerId: string, text: string, expectedVersion: number) =>
  request<AnswerWithImages>(`/answers/${encodeURIComponent(answerId)}/manual-transcription/confirm`, {
    method: 'POST',
    body: JSON.stringify({ text, expected_version: expectedVersion }),
  })
// Extração OCR/visão EXPERIMENTAL (AV-S07B): o texto extraído é dado não
// confiável e exige conferência humana. O backend só preenche o rascunho se ele
// estiver vazio (draft_updated) e nunca confirma a transcrição. Erros 409:
// EXTRACTION_IN_PROGRESS, ANSWER_HAS_NO_ACTIVE_IMAGE, TRANSCRIPTION_ALREADY_CONFIRMED.
export type TranscriptionExtractionStatus = 'ok' | 'vazio' | 'falha'
export interface TranscriptionExtraction {
  extraction_id: string
  status: TranscriptionExtractionStatus
  extracted_text: string
  draft_updated: boolean
  draft_origin?: string | null
  answer_image_id?: string
  transcription_version?: number
  message: string
}
export const extractTranscription = (answerId: string) =>
  request<TranscriptionExtraction>(`/answers/${encodeURIComponent(answerId)}/transcription/extract`, { method: 'POST' })
// Retomada após reload (somente leitura): saída bruta do OCR (raw_text),
// origem do rascunho humano e estado confirmado vêm separados.
export interface LatestTranscriptionExtraction {
  extraction_id: string
  status: TranscriptionExtractionStatus | 'processando'
  created_at: string
  model: string
  image_id: string
  has_raw_output: boolean
  raw_text: string
  raw_text_truncated: boolean
  error_detail?: string | null
}
export interface TranscriptionExtractionState {
  answer_id: string
  transcription_status: string
  transcription_version: number
  text_state: 'VAZIO' | 'RASCUNHO' | 'CONFIRMADA'
  draft_origin: 'OCR' | 'OCR_EDITADO' | 'MANUAL' | null
  draft_source_extraction_id: string | null
  draft_source_raw_text: string | null
  latest_extraction: LatestTranscriptionExtraction | null
}
export const getTranscriptionExtractionState = (answerId: string) =>
  request<TranscriptionExtractionState>(`/answers/${encodeURIComponent(answerId)}/transcription/extractions`)
// Download autenticado (Bearer): a imagem nunca é servida por URL pública.
export async function downloadAnswerImage(imageId: string): Promise<Blob> {
  const response = await send(`/answer-images/${imageId}/download`)
  return response.blob()
}
// Exclusão lógica reversível (BL-AV-4B-05): só enquanto a resposta aguarda
// transcrição; depois da confirmação o backend responde 409 ANSWER_IMAGES_LOCKED.
// Nada é removido do armazenamento.
export const deleteAnswerImage = (imageId: string) =>
  request<DeletedAnswerImage>(`/answer-images/${encodeURIComponent(imageId)}`, { method: 'DELETE' })
export const restoreAnswerImage = (imageId: string) =>
  request<AnswerImage>(`/answer-images/${encodeURIComponent(imageId)}/restore`, { method: 'POST' })
export const listDeletedAnswerImages = (answerId: string) =>
  request<DeletedAnswerImage[]>(`/answers/${encodeURIComponent(answerId)}/images/deleted`)

export interface CorrectionJobContext {
  job: CorrectionJob;
  answer: Answer;
  question: import('../types').Question;
  assessment: { id: string; title: string };
  human_review?: HumanReviewSummary | null;
}

export const getCorrectionContext = (jobId: string) => request<CorrectionJobContext>(`/correction-jobs/${jobId}/context`)

export const submitReview = (correctionId: string, payload: { decision: 'APPROVE' | 'ALTER'; criteria_scores?: { criterion_id: string; score: number }[]; justification?: string }) => request(`/corrections/${correctionId}/reviews`, { method: 'POST', body: JSON.stringify(payload) })

// ---------------- Gestão Acadêmica (BL-AV-2-04) ----------------
export const attachAssessmentClassGroup = (assessmentId: string, classGroupId: string) =>
  request<Assessment>(`/assessments/${assessmentId}/class-group`, {
    method: 'POST',
    body: JSON.stringify({ class_group_id: classGroupId }),
  })

export const listOrganizations = () => request<Organization[]>('/organizations')
export const createOrganization = (payload: { name: string }) =>
  request<Organization>('/organizations', { method: 'POST', body: JSON.stringify(payload) })

export const listCourses = () => request<Course[]>('/courses')
export const createCourse = (payload: { organization_id: string; name: string; code: string }) =>
  request<Course>('/courses', { method: 'POST', body: JSON.stringify(payload) })

export const listDisciplines = () => request<Discipline[]>('/disciplines')
export const createDiscipline = (payload: { organization_id: string; name: string; code: string }) =>
  request<Discipline>('/disciplines', { method: 'POST', body: JSON.stringify(payload) })

export const listCourseDisciplines = () => request<CourseDiscipline[]>('/course-disciplines')
export const createCourseDiscipline = (payload: { course_id: string; discipline_id: string }) =>
  request<CourseDiscipline>('/course-disciplines', { method: 'POST', body: JSON.stringify(payload) })

export const listClassGroups = () => request<ClassGroup[]>('/class-groups')
export const createClassGroup = (payload: { course_discipline_id: string; period: string; code: string }) =>
  request<ClassGroup>('/class-groups', { method: 'POST', body: JSON.stringify(payload) })

export const listStudents = () => request<Student[]>('/students')
export const createStudent = (payload: { organization_id: string; name: string; external_id: string }) =>
  request<Student>('/students', { method: 'POST', body: JSON.stringify(payload) })

export const listEnrollments = () => request<Enrollment[]>('/enrollments')
export const createEnrollment = (payload: {
  class_group_id: string
  student_id: string
  status?: EnrollmentStatus
}) => request<Enrollment>('/enrollments', { method: 'POST', body: JSON.stringify(payload) })

export const listProfessorClassLinks = () => request<ProfessorClassLink[]>('/professor-class-links')

// ---------------- Capacidades do backend (BL-AV-S03B-01/02) ----------------
// NOTA (DEBT-AV-012, resolvido aqui): até AV-S03B o frontend decidia se o módulo
// acadêmico estava ligado lendo sua PRÓPRIA variável de ambiente
// (VITE_ACADEMIC_MODULE_ENABLED, via a antiga função isAcademicModuleEnabled()).
// Isso eram duas configurações independentes que podiam divergir em operação.
// A função foi REMOVIDA — não existe mais fonte de decisão de UI baseada em env
// var estático. A fonte única de verdade é GET /v1/config/capabilities, exposta
// à UI exclusivamente por useCapabilities() (src/context/CapabilitiesContext.tsx).
// Não reintroduzir leitura de VITE_ACADEMIC_MODULE_ENABLED aqui.
export interface Capabilities {
  academic_module_enabled: boolean
}

export const getCapabilities = () => request<Capabilities>('/config/capabilities')

