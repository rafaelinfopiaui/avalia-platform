import type { ApiErrorBody, Assessment, Answer, CorrectionJob, Criterion, User } from '../types'

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
    const detail = raw.detail && typeof raw.detail === 'object' ? raw.detail as Record<string, unknown> : raw
    const body: ApiErrorBody = {
      code: typeof detail.code === 'string' ? detail.code : undefined,
      message: typeof detail.message === 'string' ? detail.message : defaultMessage(response.status),
      correlation_id: typeof detail.correlation_id === 'string' ? detail.correlation_id : undefined,
      field_errors: Array.isArray(detail.field_errors) ? detail.field_errors as ApiErrorBody['field_errors'] : undefined,
    }
    if (response.status === 401) { clearSession(); window.dispatchEvent(new Event('avalia:unauthorized')) }
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
export const createAssessment = (payload: { title: string; question: Omit<import('../types').Question, 'id' | 'rubric'> }) => request<Assessment>('/assessments', { method: 'POST', body: JSON.stringify(payload) })
export const updateAssessment = (id: string, payload: unknown) => request<Assessment>(`/assessments/${id}`, { method: 'PUT', body: JSON.stringify(payload) })
export const saveRubric = (questionId: string, criteria: Criterion[]) => request(`/questions/${questionId}/rubric`, { method: 'POST', body: JSON.stringify({ criteria: criteria.map(({ name, description, max_score }) => ({ name, description, max_score })) }) })
export const publishAssessment = (id: string) => request<Assessment>(`/assessments/${id}/publish`, { method: 'POST' })
export const createAnswer = (payload: { question_id: string; student_name: string; text: string }) => request<Answer>('/answers', { method: 'POST', body: JSON.stringify({ question_id: payload.question_id, student_name_fake: payload.student_name, text: payload.text }) })
export const requestCorrection = (answerId: string) => request<CorrectionJob>(`/answers/${answerId}/corrections`, { method: 'POST' })
export const getCorrectionJob = (id: string) => request<CorrectionJob>(`/correction-jobs/${id}`)
export const submitReview = (correctionId: string, payload: { decision: 'APPROVE' | 'ALTER'; criteria_scores?: { criterion_id: string; score: number }[]; justification?: string }) => request(`/corrections/${correctionId}/reviews`, { method: 'POST', body: JSON.stringify(payload) })
