import type { Answer, Assessment, CorrectionJob } from '../types'

const KEY = 'avalia_demo_workflow'
interface Workflow { assessment?: Assessment; answer?: Answer; job?: CorrectionJob }
export function readWorkflow(): Workflow { try { return JSON.parse(sessionStorage.getItem(KEY) || '{}') as Workflow } catch { return {} } }
export function writeWorkflow(patch: Partial<Workflow>) { sessionStorage.setItem(KEY, JSON.stringify({ ...readWorkflow(), ...patch })) }
