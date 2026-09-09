export type AssessmentStatus = 'DRAFT' | 'PUBLISHED' | 'RASCUNHO' | 'PUBLICADA'
export type JobStatus = 'PENDENTE' | 'PROCESSANDO' | 'SUGERIDA' | 'FALHA'

export interface User { id?: string; name?: string; email: string; role?: string }
export interface Criterion { id?: string; name: string; description: string; max_score: number }
export interface Question { id?: string; statement: string; reference_answer: string; max_score: number; rubric?: { criteria: Criterion[] } }
export interface Assessment { id: string; title: string; status: AssessmentStatus; question?: Question; questions?: Question[]; created_at?: string; updated_at?: string }
export interface Answer { id: string; question_id: string; student_name?: string; text: string }
// Alinhado ao schema real do Core (app/schemas.py CriterionScoreOut / AIExecutionOut / CorrectionJobOut)
export interface CriterionSuggestion { criterion_id: string; criterion_name?: string; score: number; max_score: number; reason?: string; evidence?: string; confidence?: number; was_clamped?: boolean }
export interface AIExecutionResult { id: string; engine_mode?: 'real' | 'simulated'; model?: string; confidence_method_version?: string; overall_confidence?: number; review_recommendation?: string; duration_ms?: number; flags?: string[]; criterion_scores: CriterionSuggestion[] }
export interface CorrectionJob { id: string; answer_id?: string; status: JobStatus; attempt?: number; error_message?: string; latest_execution?: AIExecutionResult }
export interface ApiErrorBody { code?: string; message?: string; correlation_id?: string; field_errors?: { field?: string; reason?: string }[] }
