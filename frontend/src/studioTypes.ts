export type View = 'home' | 'learn' | 'review' | 'bench' | 'projects' | 'sources'
export type Kind = 'explain' | 'predict' | 'repair' | 'modify' | 'build'
export interface CaseStep { name: string; stdin?: string; expected_stdout?: string; expected_files?: Record<string, string>; timeout_seconds?: number }
export interface TestCase extends CaseStep { files?: Record<string, string>; runs?: CaseStep[] }
export interface Task {
  id: string; kind: Kind; required: boolean; prompt: string; code?: string
  rubric: string[]; hint_count: number; starter_code?: string; starter_input?: string; tests?: TestCase[]
  starter_expected_status?: string
}
export interface Example {
  code: string; text?: string; stdin?: string; expected_stdout: string; walkthrough: string[]
  files?: Record<string, string>; expected_files?: Record<string, string>
}
export interface Concept {
  id: string; module_id: string; title: string; summary: string; explanation: string[]; outcomes: string[]
  prerequisites: string[]; optional: boolean; tasks: Task[]; worked_example: Example
  visual: {kind: string; nodes: string[]; edges: [number, number][]}
  provenance: string; technical_reference: string
  source_pdfs: {file: string; pages?: number[]; basis: string}[]
}
export interface Course {
  id: string; version: number; title: string; description: string
  modules: {id: string; title: string; summary: string; concept_ids: string[]}[]
  concepts: Concept[]; source_files: string[]; assessment_note: string; curriculum_note: string
}
export interface TaskProgress {
  attempts: number; passed: boolean; independent_passed: boolean; last_passed: boolean
  assisted: boolean; assessment: string; last_attempt_at: string; next_review_at: string
}
export interface Learning {
  task_progress: Record<string, TaskProgress>; completed_concept_ids: string[]
  next_concept_id: string | null; weak_task_ids: string[]; due_task_ids: string[]; course_version: number
}
export interface Draft { generation: number; response: string; code: string; stdin: string; assisted: boolean; rubric_checks: boolean[] }
export interface RunResult { status: string; stdout: string; stderr: string; exit_code: number | null; duration_ms?: number; compile_success: boolean; output_truncated?: boolean; jdk_available: boolean }
export interface CaseResult {
  name: string; passed: boolean; status: string; stdin: string; expected_stdout: string; actual_stdout: string; stderr: string
  exit_code: number | null; files: {name: string; passed: boolean; expected: string; actual: string | null}[]
}
export interface Assessment {
  task_id: string; passed: boolean; assisted: boolean; feedback: string; answer?: string; explanation?: string
  assessment: string; cases: CaseResult[]; run?: RunResult; created_at: string; attempt_id: string
  response?: string; code?: string; stdin?: string
}
export interface Reference { answer: string; code: string; explanation: string; walkthrough: string[] }
export interface Project { id?: string; title: string; description: string; code: string; created_at?: string; updated_at?: string }
export interface ProjectFile {name: string; bytes: number; readable: boolean}
export interface Health {jdk_available: boolean; setup_message: string; compiler_version: string | null; java_version: string | null; status: string; execution_mode?: 'remote_sandbox' | 'local_trusted'; runner_ready?: boolean}
export const EMPTY_LEARNING: Learning = {task_progress: {}, completed_concept_ids: [], next_concept_id: null, weak_task_ids: [], due_task_ids: [], course_version: 2}
