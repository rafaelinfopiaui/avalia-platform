import type {
  ApiErrorBody,
  Assessment,
  Answer,
  ClassGroup,
  CorrectionJob,
  Course,
  CourseDiscipline,
  Criterion,
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

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers = new Headers(init.headers)
  if (init.body) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError(0, { message: 'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.' })
  }
  const text = await response.text()
  let data: unknown = undefined
  if (text) { try { data = JSON.parse(text) } catch { data = undefined } }
  if (!response.ok) {
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
  return data as T
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

export function isAcademicModuleEnabled(): boolean {
  const envVal = import.meta.env.VITE_ACADEMIC_MODULE_ENABLED
  if (typeof envVal === 'string') {
    return ['1', 'true', 'yes', 'on'].includes(envVal.toLowerCase())
  }
  // O backend (core/app/config.py) usa ACADEMIC_MODULE_ENABLED com default "false".
  // O frontend precisa espelhar o MESMO default para não divergir do backend:
  // sem configuração explícita em ambos os lados, o módulo acadêmico está
  // DESLIGADO. Configure VITE_ACADEMIC_MODULE_ENABLED=true no ambiente do
  // frontend sempre que ACADEMIC_MODULE_ENABLED=true estiver configurado no
  // backend (ver frontend/.env.example).
  return false
}

