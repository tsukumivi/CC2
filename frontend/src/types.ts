export type FlexibleText = string | string[] | Record<string, unknown> | null | undefined

export interface SourcePdfReference {
  file: string
  pages?: number[]
  basis?: string
}

export interface Concept {
  id: string
  title: string
  summary?: string
  source_file?: string
  source_pdfs?: SourcePdfReference[]
  source_concepts?: string[]
  visual?: FlexibleText
  explanation?: FlexibleText
  worked_example?: FlexibleText
  trace?: FlexibleText
  recall_question?: FlexibleText
  activity?: FlexibleText
}

export interface Module {
  id: string
  title: string
  summary?: string
  concepts: Concept[]
}

export interface ReviewerVisual {
  kind: 'memory_slots' | 'flow' | 'branch' | 'switch_routes' | 'calculation_flow' | string
  [key: string]: unknown
}

export interface ReviewerQuestion {
  id: string
  concept_id: string
  prompt: string
  answer: string
  visual: ReviewerVisual
}

export interface CourseReviewer {
  title: string
  purpose: string
  questions: ReviewerQuestion[]
}

export interface Course {
  id: string
  title: string
  description?: string
  source_files?: string[]
  modules: Module[]
  reviewer?: CourseReviewer
}

export interface ConceptProgress {
  concept_id: string
  attempts: number
}

export interface ProgressData {
  concepts: ConceptProgress[]
  summary?: Record<string, number | string>
}

export interface Project {
  id?: string
  title: string
  description?: string
  code: string
  created_at?: string
  updated_at?: string
}

export interface HealthData {
  status?: string
  jdk_available?: boolean
  java_version?: string | null
  compiler?: string | null
  [key: string]: unknown
}

export interface RunResult {
  status?: string
  stdout?: string
  stderr?: string
  exit_code?: number | null
  duration_ms?: number
  jdk_available?: boolean
  compile_success?: boolean
}

