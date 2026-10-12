import type { Concept, Course, Draft, Kind, Learning, Task, View } from './studioTypes'

export interface Route {view: View; lesson: string; task: string; project: string}
const VIEWS: View[] = ['home','learn','review','bench','projects','sources']
export function readRoute(search: string = window.location.search): Route {
  const params = new URLSearchParams(search.replace(/^\//,''))
  const candidate = params.get('view') as View
  return {view: VIEWS.includes(candidate) ? candidate : 'home', lesson:params.get('lesson') ?? '', task:params.get('task') ?? '', project:params.get('project') ?? ''}
}
export function routeHref(view: View, lesson='', task='', project=''): string {
  const params = new URLSearchParams({view})
  if (lesson) params.set('lesson',lesson)
  if (task) params.set('task',task)
  if (project) params.set('project',project)
  return `?${params.toString()}`
}
export function initialDraft(task: Task, generation=0): Draft {
  return {generation,response:'',code:task.starter_code ?? '',stdin:task.starter_input ?? '',assisted:false,rubric_checks:task.rubric.map(()=>false)}
}
export function nextTask(concept: Concept, state: Learning): Task {
  return concept.tasks.find(t=>t.required && !state.task_progress[t.id]?.independent_passed) ?? concept.tasks[0]
}
export function reviewQueue(course: Course, state: Learning, status: string, kind: Kind | 'any', conceptId: string) {
  return course.concepts.filter(c=>!c.optional || c.id===conceptId).flatMap(concept=>concept.tasks.map(task=>({concept,task})))
    .filter(({concept,task})=>(!conceptId || concept.id===conceptId) && (kind==='any' || task.kind===kind)
      && (status==='all' || status==='weak' && state.weak_task_ids.includes(task.id)
          || status==='due' && state.due_task_ids.includes(task.id)
          || status==='new' && !state.task_progress[task.id]))
}
export function readLocal<T>(key: string): T | null {
  try { const raw=localStorage.getItem(key); return raw ? JSON.parse(raw) as T : null } catch { return null }
}
export function saveLocal(key: string, value: unknown): boolean {
  try { localStorage.setItem(key,JSON.stringify(value)); return true } catch { return false }
}
export function downloadText(name: string, text: string) {
  const url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'}))
  const link=document.createElement('a'); link.href=url; link.download=name; link.click()
  setTimeout(()=>URL.revokeObjectURL(url),1000)
}
export const errorMessage = (error: unknown) => error instanceof Error ? error.message : 'The operation failed. Retry after checking the Studio connection.'
export const kindLabel: Record<Kind,string> = {explain:'Explain',predict:'Predict',repair:'Repair',modify:'Modify',build:'Build'}
