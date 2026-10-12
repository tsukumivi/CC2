import type { ConceptProgress, Course, HealthData, ProgressData, Project, RunResult } from './types'

const API_BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  const text = await response.text()
  let body: unknown = null
  try { body = text ? JSON.parse(text) : null } catch { body = text }
  if (!response.ok) {
    const detail = typeof body === 'object' && body !== null && 'detail' in body
      ? String((body as { detail: unknown }).detail)
      : `Request failed (${response.status})`
    throw new Error(detail)
  }
  return body as T
}

function record(value: unknown): Record<string, unknown> {
  return typeof value === 'object' && value !== null ? value as Record<string, unknown> : {}
}

export async function getHealth(): Promise<HealthData> {
  return request<HealthData>('/health')
}

export async function getCourse(): Promise<Course> {
  const data = record(await request<unknown>('/course'))
  return (data.course ?? data) as Course
}

export async function getProgress(): Promise<ProgressData> {
  const data = record(await request<unknown>('/progress'))
  return {
    concepts: Array.isArray(data.concepts) ? data.concepts as ProgressData['concepts'] : [],
    summary: typeof data.summary === 'object' && data.summary !== null ? data.summary as ProgressData['summary'] : undefined,
  }
}

export interface ProgressSubmission {
  concept_id: string
  activity_type: string
  result: string | boolean | Record<string, unknown>
  response?: string
  code?: string
}

export async function saveProgress(payload: ProgressSubmission): Promise<{ attempt_id: string; progress: ConceptProgress }> {
  return request<{ attempt_id: string; progress: ConceptProgress }>('/progress', { method: 'POST', body: JSON.stringify(payload) })
}

export async function getProjects(): Promise<Project[]> {
  const data = await request<unknown>('/projects')
  if (Array.isArray(data)) return data as Project[]
  const wrapped = record(data)
  return Array.isArray(wrapped.projects) ? wrapped.projects as Project[] : []
}

export async function saveProject(project: Project): Promise<Project> {
  const data = record(await request<unknown>('/projects', { method: 'POST', body: JSON.stringify(project) }))
  return (data.project ?? data) as Project
}

export async function runJava(source: string, stdin: string): Promise<RunResult> {
  return request<RunResult>('/run', {
    method: 'POST',
    body: JSON.stringify({ source, stdin, timeout_seconds: 5 }),
  })
}

