import type { Assessment, Course, Draft, Health, Learning, Project, ProjectFile, Reference, RunResult } from './studioTypes'

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, { ...init, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', ...init?.headers } })
  const text = await response.text()
  let body: unknown
  try { body = text ? JSON.parse(text) : null } catch { throw new Error('The Studio API did not return JSON. Reload the page and retry.') }
  if (!response.ok) {
    const detail = body && typeof body === 'object' && 'detail' in body ? (body as {detail: unknown}).detail : null
    const message = Array.isArray(detail) ? detail.map((e: {msg?: string}) => e.msg ?? 'Invalid input').join('; ') : typeof detail === 'string' ? detail : `Request failed (${response.status}). Retry when the Studio API is available.`
    throw new Error(message)
  }
  return body as T
}
const json = (method: string, payload: unknown): RequestInit => ({method, body: JSON.stringify(payload)})
const taskPath = (id: string) => `/tasks/${encodeURIComponent(id)}`
export const getCourse = () => request<Course>('/course')
export const getHealth = () => request<Health>('/health')
export const getLearning = () => request<Learning>('/learning')
export const getDraft = (id: string) => request<Draft>(`${taskPath(id)}/draft`)
export const saveDraft = (id: string, draft: Draft) => request<Draft>(`${taskPath(id)}/draft`, json('PUT', draft))
export const retryTask = (id: string) => request<Draft>(`${taskPath(id)}/retry`, {method: 'POST'})
export const getReference = (id: string) => request<Reference>(`${taskPath(id)}/reference`)
export const getHint = (id: string, index: number) => request<{hint: string}>(`${taskPath(id)}/hint/${index}`, {method: 'POST'})
export const getHistory = (id: string) => request<{attempts: Assessment[]}>(`${taskPath(id)}/history`)
export const submitTask = (id: string, draft: Draft, request_id: string) => request<Assessment>(`${taskPath(id)}/submit`, json('POST', {...draft, request_id}))
export const runJava = (source: string, stdin: string, project_id?: string) => request<RunResult>('/run', json('POST', {source, stdin, project_id, timeout_seconds: 4}))
export const getProjects = async () => (await request<{projects: Project[]}>('/projects')).projects
export const getProject = (id: string) => request<Project>(`/projects/${encodeURIComponent(id)}`)
export const saveProject = async (project: Project) => (await request<{project: Project}>('/projects', json('POST', project))).project
export const getFiles = (id: string) => request<{files: ProjectFile[]; truncated: boolean}>(`/projects/${encodeURIComponent(id)}/files`)
export const getFile = (id: string, name: string) => request<{name: string; content: string}>(`/projects/${encodeURIComponent(id)}/files/${encodeURIComponent(name)}`)
export const putFile = (id: string, name: string, content: string) => request<{name: string; bytes: number}>(`/projects/${encodeURIComponent(id)}/files/${encodeURIComponent(name)}`, json('PUT', {content}))
export const deleteFile = (id: string, name: string) => request<{deleted: string}>(`/projects/${encodeURIComponent(id)}/files/${encodeURIComponent(name)}`, {method: 'DELETE'})
export const exportWorkspace = () => request<Record<string, unknown>>('/workspace/export')
export const eraseWorkspace = () => request<{deleted: boolean}>('/workspace', {method: 'DELETE'})
