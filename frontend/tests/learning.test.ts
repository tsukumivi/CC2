import { test } from 'node:test'
import assert from 'node:assert/strict'
import { initialDraft, nextTask, readRoute, reviewQueue, routeHref } from '../src/learning.ts'
import type { Course, Learning, Task } from '../src/studioTypes.ts'

const a = {id:'a-predict',kind:'predict',required:true,rubric:[],hint_count:1} as Task
const b = {id:'a-build',kind:'build',required:true,rubric:['rule'],starter_code:'// start',starter_input:'Ada\n',hint_count:2} as Task
const course = {concepts:[{id:'a', optional:false, tasks:[a,b]},{id:'optional',optional:true,tasks:[{...a,id:'optional-predict'}]}]} as Course
const state = {task_progress:{'a-predict':{independent_passed:true}},weak_task_ids:['a-build'],due_task_ids:['a-predict']} as Learning

test('a prior failed/assisted attempt never makes next task skip a required build', () => {
  assert.equal(nextTask(course.concepts[0], state).id,'a-build')
})
test('draft starts with a real multiline starter and unchecked design criteria', () => {
  assert.deepEqual(initialDraft(b),{generation:0,response:'',code:'// start',stdin:'Ada\n',assisted:false,rubric_checks:[false]})
})
test('weak filter returns exactly known weak core tasks', () => {
  assert.deepEqual(reviewQueue(course,state,'weak','any','').map(t=>t.task.id),['a-build'])
  assert.deepEqual(reviewQueue(course,state,'due','build','').map(t=>t.task.id),[])
})
test('a fresh retry carries its server generation into later autosaves', () => {
  assert.equal(initialDraft(b, 7).generation, 7)
})
test('route values round-trip without replacing identifiers', () => {
  const href=routeHref('review','a/b','task & one')
  assert.equal(readRoute(href).lesson,'a/b')
  assert.equal(readRoute(href).task,'task & one')
  assert.equal(readRoute('?view=not-real').view,'home')
})
