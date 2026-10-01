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
export interface Answer { id: string; question_id: string; student_name?: string; text: string }
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
export interface ApiErrorBody { code?: string; message?: string; correlation_id?: string; field_errors?: { field?: string; reason?: string }[] }

