export type AssessmentStatus = 'DRAFT' | 'PUBLISHED' | 'RASCUNHO' | 'PUBLICADA'
export type JobStatus = 'PENDENTE' | 'PROCESSANDO' | 'SUGERIDA' | 'FALHA'
export type EnrollmentStatus = 'ACTIVE' | 'SUSPENDED' | 'WITHDRAWN' | 'COMPLETED'
export type ProfessorRole = 'responsible' | 'collaborator'

export interface Organization {
  id: string
  name: string
}

export interface Course {
  id: string
  organization_id: string
  name: string
  code: string
}

export interface Discipline {
  id: string
  organization_id: string
  name: string
  code: string
}

export interface CourseDiscipline {
  id: string
  course_id: string
  discipline_id: string
}

export interface ClassGroup {
  id: string
  course_discipline_id: string
  period: string
  code: string
}

export interface Student {
  id: string
  organization_id: string
  name: string
  external_id: string
}

export interface Enrollment {
  id: string
  class_group_id: string
  student_id: string
  status: EnrollmentStatus
  enrolled_at: string
  ended_at?: string | null
}

export interface ProfessorClassLink {
  id: string
  professor_id: string
  class_group_id: string
  role: ProfessorRole
  active: boolean
  starts_at?: string | null
  ends_at?: string | null
}

export interface User { id?: string; name?: string; email: string; role?: string }
export interface Criterion { id?: string; name: string; description: string; max_score: number }
export interface Rubric { id?: string; question_id?: string; version?: number; is_published?: boolean; criteria: Criterion[] }
export interface Question { id?: string; statement: string; reference_answer: string; max_score: number; position?: number; rubrics?: Rubric[]; rubric?: { criteria: Criterion[] } }
export interface Assessment { id: string; title: string; status: AssessmentStatus; class_group_id?: string | null; cloned_from_id?: string | null; assessment_max_score?: number; question?: Question; questions?: Question[]; created_at?: string; updated_at?: string }
export type AnswerSource = 'TEXT' | 'IMAGE'
export type TranscriptionStatus = 'AGUARDANDO_TRANSCRICAO' | 'TRANSCRICAO_CONFIRMADA'
// text é null na resposta por imagem ainda sem transcrição (DEC-AV-037).
export interface Answer { id: string; question_id: string; student_name?: string; student_name_fake?: string; text?: string | null; source?: AnswerSource; transcription_status?: TranscriptionStatus; created_at?: string }
export interface AnswerImage { id: string; answer_id: string; original_filename: string; content_type: string; size_bytes: number; sha256_hash: string; uploaded_by_id: string; created_at: string }
// Imagem excluída logicamente (BL-AV-4B-05): projeção mínima, sem nome original,
// hash ou download — só o necessário para identificar e restaurar.
export interface DeletedAnswerImage { id: string; deleted_at: string; deleted_by_id: string }
// Transcrição manual (AV-S08B): rascunho atual + versão para o lock otimista.
export interface AnswerWithImages extends Answer {
  images: AnswerImage[]
  manual_transcription_draft?: string | null
  transcription_version: number
  transcription_confirmed_by_id?: string | null
  transcription_confirmed_at?: string | null
}
// Alinhado ao schema real do Core (app/schemas.py CriterionScoreOut / AIExecutionOut / CorrectionJobOut)
export interface CriterionSuggestion { criterion_id: string; criterion_name?: string; score: number; max_score: number; reason?: string; evidence?: string; confidence?: number; was_clamped?: boolean }
export interface AIExecutionResult { id: string; engine_mode?: 'real' | 'simulated'; model?: string; confidence_method_version?: string; overall_confidence?: number; review_recommendation?: string; duration_ms?: number; flags?: string[]; criterion_scores: CriterionSuggestion[] }
export interface CorrectionJob { id: string; answer_id?: string; status: JobStatus; attempt?: number; error_message?: string; latest_execution?: AIExecutionResult }
export interface HumanReviewCriterionScore { criterion_id: string; score: string | number }
export interface HumanReviewSummary {
  id: string;
  reviewer_id: string;
  reviewer_email: string;
  decision: 'APPROVE' | 'ALTER';
  final_total: number | string;
  final_scores: HumanReviewCriterionScore[];
  justification?: string | null;
  created_at: string;
}
export interface ApiErrorBody { code?: string; message?: string; correlation_id?: string; details?: Record<string, unknown>; field_errors?: { field?: string; reason?: string }[] }

