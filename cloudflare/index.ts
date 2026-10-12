import sourceCourse from "../content/course.json"
import { makeHarness, type HarnessCase } from "./java_harness"

type Env = {
  DB: any
  ASSETS: { fetch(request: Request): Promise<Response> }
  SANDBOX_API_KEY?: string
  MONTHLY_EXECUTION_LIMIT?: string
}

const SESSION_COOKIE = "fieldnotes_guest"
const MAX_SOURCE_BYTES = 48_000
const MAX_STDIN_BYTES = 8_000
const MAX_OUTPUT_BYTES = 16_000
const MAX_FILE_BYTES = 64_000
const MAX_REQUEST_BYTES = 120_000
const MAX_ATTEMPTS_PER_GUEST = 200
const MAX_PROJECTS_PER_GUEST = 20
const DATA_EXTENSIONS = new Set([".txt", ".csv", ".json", ".md", ".log", ".dat"])
const DEVICE_NAME = /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i

type Task = Record<string, any>
type Concept = Record<string, any>

const immutableCourse = sourceCourse as unknown as Record<string, any>

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
      "referrer-policy": "same-origin",
      "permissions-policy": "camera=(), microphone=(), geolocation=()",
      "content-security-policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    },
  })
}

function cookieValue(request: Request): string | null {
  const raw = request.headers.get("Cookie") ?? ""
  for (const item of raw.split(";")) {
    const separator = item.indexOf("=")
    if (separator < 0 || item.slice(0, separator).trim() !== SESSION_COOKIE) continue
    const value = item.slice(separator + 1).trim()
    return /^[a-f0-9]{64}$/.test(value) ? value : null
  }
  return null
}

function newCookie(request: Request, ownerId: string): string {
  const secure = new URL(request.url).protocol === "https:" ? "; Secure" : ""
  return `${SESSION_COOKIE}=${ownerId}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Strict${secure}`
}

function withCookie(response: Response, cookie: string | null): Response {
  if (!cookie) return response
  const headers = new Headers(response.headers)
  headers.append("set-cookie", cookie)
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers })
}

function session(request: Request): { ownerId: string; cookie: string | null } {
  const current = cookieValue(request)
  if (current) return { ownerId: current, cookie: null }
  const bytes = crypto.getRandomValues(new Uint8Array(32))
  const ownerId = Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join("")
  return { ownerId, cookie: newCookie(request, ownerId) }
}

function assertSameOrigin(request: Request): void {
  const origin = request.headers.get("Origin")
  if (!origin || origin !== new URL(request.url).origin) throw new ApiError(403, "Use the Java Fieldnotes site to make this change.")
}

async function body(request: Request): Promise<Record<string, any>> {
  const length = Number(request.headers.get("Content-Length") ?? 0)
  if (length > MAX_REQUEST_BYTES) throw new ApiError(413, "Request exceeds the 120 KB limit.")
  const reader = request.body?.getReader()
  if (!reader) throw new ApiError(400, "Request body must be valid JSON.")
  const chunks: Uint8Array[] = []
  let size = 0
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    size += value.byteLength
    if (size > MAX_REQUEST_BYTES) {
      await reader.cancel()
      throw new ApiError(413, "Request exceeds the 120 KB limit.")
    }
    chunks.push(value)
  }
  const bytes = new Uint8Array(size)
  let offset = 0
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength }
  let parsed: unknown
  try { parsed = JSON.parse(new TextDecoder().decode(bytes)) } catch { throw new ApiError(400, "Request body must be valid JSON.") }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) throw new ApiError(400, "Request body must be a JSON object.")
  return parsed as Record<string, any>
}

function utf8Bytes(value: string): number { return new TextEncoder().encode(value).length }

function getCourse(): Record<string, any> {
  const result = JSON.parse(JSON.stringify(immutableCourse)) as Record<string, any>
  const byId = new Map<string, Concept>(result.concepts.map((concept: Concept) => [concept.id, concept]))
  for (const module of result.modules ?? []) {
    module.concepts = (module.concept_ids ?? []).map((id: string) => byId.get(id)).filter(Boolean)
  }
  for (const concept of result.concepts ?? []) {
    for (const task of concept.tasks ?? []) {
      for (const key of ["answer", "accepted_answers", "reference_code", "explanation", "walkthrough"]) delete task[key]
      task.hint_count = Array.isArray(task.hints) ? task.hints.length : 0
      delete task.hints
    }
  }
  return result
}

function findTask(taskId: string): { concept: Concept; task: Task } {
  for (const concept of immutableCourse.concepts as Concept[]) {
    const task = (concept.tasks ?? []).find((item: Task) => item.id === taskId)
    if (task) return { concept, task }
  }
  throw new ApiError(404, "That task does not exist in this course.")
}

function safeFilename(name: string): string {
  if (!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$/.test(name) || DEVICE_NAME.test(name)
      || name.endsWith(".") || name.toLowerCase() === "main.java" || name.toLowerCase().endsWith(".class")) {
    throw new ApiError(422, "Use a simple data filename, without folders, traversal, or executable files.")
  }
  const dot = name.lastIndexOf(".")
  const extension = dot < 0 ? "" : name.slice(dot).toLowerCase()
  if (!DATA_EXTENSIONS.has(extension)) throw new ApiError(422, "Use a text data file: .txt, .csv, .json, .md, .log or .dat.")
  return name
}

function stripAssessment(value: Record<string, any>): Record<string, any> {
  const { answer: _answer, explanation: _explanation, ...visible } = value
  return visible
}

function stable(value: any): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${stable(value[key])}`).join(",")}}`
  }
  return JSON.stringify(value)
}

async function sha256(value: string): Promise<string> {
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value))
  return Array.from(new Uint8Array(bytes), byte => byte.toString(16).padStart(2, "0")).join("")
}

function isoNow(date = new Date()): string { return date.toISOString().replace(/\.\d{3}Z$/, "Z") }

function initialDraft(): Record<string, any> {
  return { generation: 0, response: "", code: "", stdin: "", assisted: false, rubric_checks: [] }
}

async function draftPayload(env: Env, ownerId: string, taskId: string): Promise<Record<string, any>> {
  const [draft, generation] = await Promise.all([
    env.DB.prepare("SELECT payload FROM task_drafts WHERE owner_id=? AND task_id=?").bind(ownerId, taskId).first(),
    env.DB.prepare("SELECT generation FROM task_draft_generations WHERE owner_id=? AND task_id=?").bind(ownerId, taskId).first(),
  ])
  const payload = draft ? JSON.parse(draft.payload) : initialDraft()
  return { ...payload, generation: generation?.generation ?? 0 }
}

async function requireGeneration(env: Env, ownerId: string, taskId: string, generation: number): Promise<void> {
  const row = await env.DB.prepare("SELECT generation FROM task_draft_generations WHERE owner_id=? AND task_id=?").bind(ownerId, taskId).first()
  if (generation !== (row?.generation ?? 0)) throw new ApiError(409, "A fresh attempt replaced this draft. Reload before editing or submitting it.")
}

function nextReview(now: Date, passed: boolean, assisted: boolean): string {
  const days = !passed ? 0 : assisted ? 1 : 3
  return isoNow(new Date(now.getTime() + days * 86_400_000))
}

async function learningState(env: Env, ownerId: string): Promise<Record<string, any>> {
  const course = immutableCourse
  const result = await env.DB.prepare("SELECT * FROM task_attempts WHERE owner_id=? ORDER BY created_at, id")
    .bind(ownerId).all()
  const progress: Record<string, any> = {}
  for (const row of result.results ?? []) {
    const item = progress[row.task_id] ??= { attempts: 0, passed: false, independent_passed: false }
    const attempt = JSON.parse(row.result_json)
    item.last_passed = Boolean(row.passed)
    item.assisted = Boolean(row.assisted)
    item.assessment = row.assessment
    item.last_attempt_at = row.created_at
    item.next_review_at = row.next_review_at
    item.attempts += 1
    item.passed ||= Boolean(row.passed)
    item.independent_passed ||= Boolean(row.passed) && !Boolean(row.assisted)
    item.last_feedback = attempt.feedback
  }
  const completed = [] as string[]
  for (const concept of course.concepts as Concept[]) {
    const required = (concept.tasks ?? []).filter((task: Task) => task.required !== false)
    if (required.length && required.every((task: Task) => progress[task.id]?.independent_passed)) completed.push(concept.id)
  }
  const next = (course.concepts as Concept[]).find(concept => !concept.optional && !completed.includes(concept.id))
  const activeIds = new Set((course.concepts as Concept[]).flatMap(concept => (concept.tasks ?? []).map((task: Task) => task.id)))
  const now = isoNow()
  const weak = Object.keys(progress).filter(id => activeIds.has(id) && !progress[id].last_passed)
  const due = Object.keys(progress).filter(id => activeIds.has(id) && progress[id].next_review_at <= now)
  return {
    task_progress: progress,
    completed_concept_ids: completed,
    next_concept_id: next?.id ?? null,
    weak_task_ids: weak,
    due_task_ids: due,
    course_version: course.version ?? 2,
  }
}

async function touchGuest(env: Env, ownerId: string): Promise<void> {
  const now = isoNow()
  await env.DB.prepare(
    "INSERT INTO guest_sessions(owner_id,last_seen_at) VALUES(?,?) ON CONFLICT(owner_id) DO UPDATE SET last_seen_at=excluded.last_seen_at WHERE substr(guest_sessions.last_seen_at,1,10)<>substr(excluded.last_seen_at,1,10)",
  ).bind(ownerId, now).run()
}

async function reserveRun(env: Env): Promise<void> {
  const month = new Date().toISOString().slice(0, 7)
  const configured = Number(env.MONTHLY_EXECUTION_LIMIT ?? "500")
  const limit = Number.isFinite(configured) ? Math.min(500, Math.max(1, configured)) : 500
  const row = await env.DB.prepare(
    "INSERT INTO execution_quota(month,count) VALUES(?,1) ON CONFLICT(month) DO UPDATE SET count=count+1 WHERE count<? RETURNING count",
  ).bind(month, limit).first()
  if (!row) throw new ApiError(429, "This shared site's free Java execution allowance is used for this month. Lessons, saved work and review remain available.")
}

type SandboxResult = { status: string; stdout: string; stderr: string; exit_code: number | null; truncated?: boolean; execution_time_ms?: number }

async function sandbox(env: Env, source: string, cases: HarnessCase[], collectFiles = false): Promise<{ report: any; execution: SandboxResult }> {
  if (!env.SANDBOX_API_KEY) throw new ApiError(503, "The isolated Java runner is not configured yet.")
  await reserveRun(env)
  const code = makeHarness({ source, cases, collectFiles })
  const response = await fetch("https://sandboxapi.p.rapidapi.com/v1/execute", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "X-RapidAPI-Key": env.SANDBOX_API_KEY,
      "X-RapidAPI-Host": "sandboxapi.p.rapidapi.com",
    },
    body: JSON.stringify({ language: "java", code, timeout: 30, stdin: "" }),
  })
  let execution: SandboxResult
  try { execution = await response.json() as SandboxResult } catch { throw new ApiError(503, "The isolated Java runner returned an invalid response. Try again later.") }
  if (response.status === 429) throw new ApiError(429, "The isolated Java runner is at its free request limit. Try again later.")
  if (!response.ok) throw new ApiError(503, "The isolated Java runner is temporarily unavailable. Try again later.")
  if (execution.status === "timeout") throw new ApiError(504, "The Java task exceeded the runner's total execution limit. Simplify the program and retry.")
  if (execution.status !== "completed") throw new ApiError(503, "The isolated Java runner could not start this program. Try again later.")
  const marker = "__FIELDNOTES_RESULT__"
  const position = execution.stdout.lastIndexOf(marker)
  if (position < 0) throw new ApiError(503, "The isolated Java runner did not return a usable result. Try again later.")
  try { return { report: JSON.parse(execution.stdout.slice(position + marker.length).trim()), execution } }
  catch { throw new ApiError(503, "The isolated Java runner returned an unreadable result. Try again later.") }
}

function normalize(value: string): string { return value.replace(/\r\n/g, "\n").replace(/\n$/, "") }

async function gradeTask(env: Env, task: Task, source: string): Promise<Record<string, any>> {
  if (!source.trim()) throw new ApiError(422, "Write or load your Java code before running the task checks.")
  const cases: HarnessCase[] = (task.tests ?? []).map((test: Record<string, any>) => ({
    name: test.name,
    files: test.files ?? {},
    steps: (test.runs ?? [test]).map((step: Record<string, any>) => ({
      stdin: step.stdin ?? "",
      timeoutSeconds: step.timeout_seconds ?? 4,
      expectedStdout: step.expected_stdout ?? "",
      expectedFiles: step.expected_files ?? {},
    })),
  }))
  const { report, execution } = await sandbox(env, source, cases)
  if (report.status === "compile_error") {
    const run = { status: "compile_error", stdout: "", stderr: report.compile_stderr ?? "Compilation did not succeed.",
      exit_code: 1, compile_success: false, jdk_available: true, duration_ms: execution.execution_time_ms ?? 0 }
    return { passed: false, feedback: "Compilation did not succeed. Read the compiler message and repair the first reported error.", cases: [], run }
  }
  if (report.status !== "compiled" || !Array.isArray(report.cases)) throw new ApiError(503, "The isolated Java runner did not complete the task checks. Try again later.")
  const results = [] as Record<string, any>[]
  for (let index = 0; index < cases.length; index++) {
    const input = cases[index]
    const output = report.cases[index]
    const steps = input.steps
    for (let stepIndex = 0; stepIndex < steps.length; stepIndex++) {
      const step = output?.runs?.[stepIndex] ?? { status: "skipped", stdout: "", stderr: "Runner did not return this step.", exit_code: null, files: [] }
      const expected = steps[stepIndex]
      const files = (step.files ?? []).map((file: Record<string, any>) => ({
        name: file.name, expected: file.expected, actual: file.actual, passed: Boolean(file.passed),
      }))
      const passed = step.status === "completed" && !step.output_truncated
        && normalize(step.stdout ?? "") === normalize(expected.expectedStdout ?? "")
        && files.every((file: Record<string, any>) => file.passed)
      results.push({
        name: input.name + (steps.length > 1 ? ` / run ${stepIndex + 1}` : ""),
        passed, status: step.status, stdin: expected.stdin,
        expected_stdout: expected.expectedStdout ?? "", actual_stdout: step.stdout ?? "",
        stderr: step.stderr ?? "", exit_code: step.exit_code ?? null, files,
      })
      if (step.status !== "completed") break
    }
  }
  const passed = results.length > 0 && results.length === cases.reduce((sum, item) => sum + item.steps.length, 0)
    && results.every(item => item.passed)
  return { passed, cases: results,
    feedback: passed ? "All declared checks passed. This is evidence for these cases, not proof for all possible inputs."
      : "Some checks failed. Compare actual and expected output, repair one cause, and rerun." }
}

async function routeApi(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url)
  const path = url.pathname.replace(/\/+$/, "") || "/"
  const method = request.method.toUpperCase()
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) assertSameOrigin(request)
  if (method === "GET" && path === "/api/session") {
    const guest = session(request)
    await touchGuest(env, guest.ownerId)
    return withCookie(json({ ready: true }), guest.cookie)
  }
  if (method === "GET" && path === "/api/health") {
    const ready = Boolean(env.SANDBOX_API_KEY)
    return json({ status: "ok", app: "Java Fieldnotes Learning Studio", storage: "Cloudflare D1 guest workspaces",
      runner_isolation: "Remote Java 21 execution through a per-request gVisor sandbox; the runner receives no persistent workspace or application secrets.",
      execution_mode: "remote_sandbox", jdk_available: ready, runner_ready: ready,
      java_version: ready ? "Java 21 remote sandbox" : null, compiler_version: ready ? "Java 21 compiler" : null,
      setup_message: ready ? "Isolated Java runner ready. Source and input are sent to the external sandbox service only when you run or check code." : "The isolated Java runner is not configured yet." })
  }
  if (method === "GET" && path === "/api/course") return json(getCourse())
  if (method === "GET" && path === "/api/progress") return json({ concepts: [], summary: { total_concepts: 0, practiced_concepts: 0, not_started_concepts: 0, activity_count: 0 } })
  const guest = session(request)
  const ownerId = guest.ownerId
  await touchGuest(env, ownerId)

  if (method === "GET" && path === "/api/learning") return withCookie(json(await learningState(env, ownerId)), guest.cookie)
  if (method === "GET" && path === "/api/workspace/export") {
    const [attempts, drafts, projects, files] = await Promise.all([
      env.DB.prepare("SELECT task_id,concept_id,response,code,stdin,passed,assisted,assessment,result_json,created_at,next_review_at FROM task_attempts WHERE owner_id=? ORDER BY created_at,id").bind(ownerId).all(),
      env.DB.prepare("SELECT task_id,payload,updated_at FROM task_drafts WHERE owner_id=? ORDER BY task_id").bind(ownerId).all(),
      env.DB.prepare("SELECT id,title,description,code,created_at,updated_at FROM projects WHERE owner_id=? ORDER BY updated_at DESC").bind(ownerId).all(),
      env.DB.prepare("SELECT project_id,name,content,updated_at FROM project_files WHERE owner_id=? ORDER BY project_id,name").bind(ownerId).all(),
    ])
    return withCookie(json({ version: 1, exported_at: isoNow(), attempts: attempts.results ?? [], drafts: drafts.results ?? [],
      projects: projects.results ?? [], files: files.results ?? [] }), guest.cookie)
  }
  if (method === "DELETE" && path === "/api/workspace") {
    await env.DB.batch([
      env.DB.prepare("DELETE FROM project_files WHERE owner_id=?").bind(ownerId),
      env.DB.prepare("DELETE FROM projects WHERE owner_id=?").bind(ownerId),
      env.DB.prepare("DELETE FROM task_attempts WHERE owner_id=?").bind(ownerId),
      env.DB.prepare("DELETE FROM task_drafts WHERE owner_id=?").bind(ownerId),
      env.DB.prepare("DELETE FROM task_draft_generations WHERE owner_id=?").bind(ownerId),
    ])
    return withCookie(json({ deleted: true }), guest.cookie)
  }
  if (path === "/api/run" && method === "POST") {
    const input = await body(request)
    const source = typeof input.source === "string" ? input.source : ""
    const stdin = typeof input.stdin === "string" ? input.stdin : ""
    if (!source.trim()) throw new ApiError(422, "Write some Java code before running it.")
    if (utf8Bytes(source) > MAX_SOURCE_BYTES || utf8Bytes(stdin) > MAX_STDIN_BYTES) throw new ApiError(413, "Source must be at most 48 KB and input at most 8 KB of UTF-8 bytes.")
    const timeout = Number(input.timeout_seconds ?? 4)
    if (!Number.isFinite(timeout) || timeout < 0.5 || timeout > 8) throw new ApiError(422, "Run timeout must be between 0.5 and 8 seconds.")
    let files: Record<string, string> = {}
    if (input.project_id) {
      const project = await env.DB.prepare("SELECT id FROM projects WHERE owner_id=? AND id=?").bind(ownerId, input.project_id).first()
      if (!project) throw new ApiError(404, "Save or open this project before running it with its data workspace.")
      const rows = await env.DB.prepare("SELECT name,content FROM project_files WHERE owner_id=? AND project_id=? ORDER BY name")
        .bind(ownerId, input.project_id).all()
      files = Object.fromEntries((rows.results ?? []).map((row: any) => [row.name, row.content]))
    }
    for (const [name, value] of Object.entries(files)) { safeFilename(name); if (utf8Bytes(value) > MAX_FILE_BYTES) delete files[name] }
    const testCase: HarnessCase = { name: "Run", files, steps: [{ stdin, timeoutSeconds: timeout }] }
    const { report, execution } = await sandbox(env, source, [testCase], Boolean(input.project_id))
    if (report.status === "compile_error") return withCookie(json({ status: "compile_error", stdout: "", stderr: report.compile_stderr ?? "Compilation failed.",
      exit_code: 1, timed_out: false, compile_success: false, jdk_available: true, duration_ms: execution.execution_time_ms ?? 0 }), guest.cookie)
    if (report.status !== "compiled" || !Array.isArray(report.cases) || !report.cases[0]?.runs?.[0]) throw new ApiError(503, "The isolated Java runner returned an incomplete result.")
    const result = report.cases[0].runs[0]
    if (input.project_id && Array.isArray(report.files)) {
      for (const file of report.files) {
        const name = safeFilename(file.name)
        if (typeof file.content !== "string" || utf8Bytes(file.content) > MAX_FILE_BYTES) continue
        await env.DB.prepare("INSERT INTO project_files(owner_id,project_id,name,content,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(owner_id,project_id,name) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at")
          .bind(ownerId, input.project_id, name, file.content, isoNow()).run()
      }
    }
    return withCookie(json({ status: result.status, stdout: result.stdout ?? "", stderr: result.stderr ?? "", exit_code: result.exit_code ?? null,
      timed_out: Boolean(result.timed_out), output_truncated: Boolean(result.output_truncated), compile_success: true,
      jdk_available: true, duration_ms: execution.execution_time_ms ?? 0 }), guest.cookie)
  }

  const taskRoute = path.match(/^\/api\/tasks\/([^/]+)(?:\/(draft|retry|hint\/([^/]+)|reference|history|submit))?$/)
  if (taskRoute) {
    let taskId: string
    try { taskId = decodeURIComponent(taskRoute[1]) } catch { throw new ApiError(404, "That task does not exist.") }
    const action = taskRoute[2] ?? ""
    const { concept, task } = findTask(taskId)
    if (action === "draft" && method === "GET") return withCookie(json(await draftPayload(env, ownerId, taskId)), guest.cookie)
    if (action === "draft" && method === "PUT") {
      const draft = await body(request)
      if (!Number.isInteger(draft.generation) || draft.generation < 0) throw new ApiError(422, "Draft generation is invalid.")
      const response = String(draft.response ?? "")
      const code = String(draft.code ?? "")
      const stdin = String(draft.stdin ?? "")
      if (response.length > 12_000 || utf8Bytes(code) > MAX_SOURCE_BYTES || utf8Bytes(stdin) > MAX_STDIN_BYTES) throw new ApiError(413, "Draft exceeds a field size limit.")
      await requireGeneration(env, ownerId, taskId, draft.generation)
      const old = await draftPayload(env, ownerId, taskId)
      const payload = { generation: draft.generation, response, code, stdin,
        assisted: Boolean(draft.assisted) || Boolean(old.assisted),
        rubric_checks: Array.isArray(draft.rubric_checks) && draft.rubric_checks.every((value: unknown) => typeof value === "boolean") ? draft.rubric_checks.slice(0, 20) : [] }
      await env.DB.prepare("INSERT INTO task_drafts(owner_id,task_id,payload,updated_at) VALUES(?,?,?,?) ON CONFLICT(owner_id,task_id) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at")
        .bind(ownerId, taskId, JSON.stringify(payload), isoNow()).run()
      return withCookie(json(payload), guest.cookie)
    }
    if (action === "retry" && method === "POST") {
      const row = await env.DB.prepare("INSERT INTO task_draft_generations(owner_id,task_id,generation) VALUES(?,?,1) ON CONFLICT(owner_id,task_id) DO UPDATE SET generation=task_draft_generations.generation+1 RETURNING generation")
        .bind(ownerId, taskId).first()
      await env.DB.prepare("DELETE FROM task_drafts WHERE owner_id=? AND task_id=?").bind(ownerId, taskId).run()
      return withCookie(json({ ...initialDraft(), generation: row?.generation ?? 1 }), guest.cookie)
    }
    if (action.startsWith("hint/") && method === "POST") {
      const index = Number(taskRoute[3])
      const hints = task.hints ?? []
      if (!Number.isInteger(index) || index < 0 || index >= hints.length) throw new ApiError(404, "That hint does not exist.")
      return withCookie(json({ hint: hints[index] }), guest.cookie)
    }
    if (action === "reference" && method === "GET") return withCookie(json({
      answer: task.answer ?? "", code: task.reference_code ?? "", explanation: task.explanation ?? "", walkthrough: task.walkthrough ?? [],
    }), guest.cookie)
    if (action === "history" && method === "GET") {
      const rows = await env.DB.prepare("SELECT result_json,response,code,stdin FROM task_attempts WHERE owner_id=? AND task_id=? ORDER BY created_at DESC,id DESC LIMIT 50")
        .bind(ownerId, taskId).all()
      return withCookie(json({ attempts: (rows.results ?? []).map((row: any) => ({
        ...stripAssessment(JSON.parse(row.result_json)), response: row.response, code: row.code, stdin: row.stdin,
      })) }), guest.cookie)
    }
    if (action === "submit" && method === "POST") {
      const submission = await body(request)
      const requestId = String(submission.request_id ?? "")
      if (!/^[A-Za-z0-9-]{1,64}$/.test(requestId)) throw new ApiError(422, "Submission request ID is invalid.")
      const payload = { ...submission }
      delete payload.request_id
      if (payload.generation === 0) delete payload.generation
      const requestHash = await sha256(stable([taskId, payload]))
      const existing = await env.DB.prepare("SELECT result_json,request_hash FROM task_attempts WHERE owner_id=? AND id=?").bind(ownerId, requestId).first()
      if (existing) {
        if (existing.request_hash !== requestHash) throw new ApiError(409, "That request ID already belongs to a different submission.")
        return withCookie(json(stripAssessment(JSON.parse(existing.result_json))), guest.cookie)
      }
      const generation = Number(submission.generation ?? 0)
      await requireGeneration(env, ownerId, taskId, generation)
      const draft = await draftPayload(env, ownerId, taskId)
      const response = String(submission.response ?? "")
      const code = String(submission.code ?? "")
      const stdin = String(submission.stdin ?? "")
      if (response.length > 12_000 || utf8Bytes(code) > MAX_SOURCE_BYTES || utf8Bytes(stdin) > MAX_STDIN_BYTES) throw new ApiError(413, "Submission exceeds a field size limit.")
      const assisted = Boolean(submission.assisted) || Boolean(draft.assisted)
      const checks = Array.isArray(submission.rubric_checks) && submission.rubric_checks.every((value: unknown) => typeof value === "boolean") ? submission.rubric_checks : []
      const attemptCount = await env.DB.prepare("SELECT COUNT(*) AS count FROM task_attempts WHERE owner_id=?").bind(ownerId).first()
      if (Number(attemptCount?.count ?? 0) >= MAX_ATTEMPTS_PER_GUEST) throw new ApiError(429, "This guest workspace has reached 200 saved attempts. Export a backup, then erase the workspace to start over.")
      let assessment = task.kind === "explain" ? "self_check" : task.kind === "predict" ? "exact" : "tests"
      let result: Record<string, any>
      if (task.kind === "explain") {
        if (checks.length !== (task.rubric ?? []).length || !response.trim()) throw new ApiError(422, "Write your explanation and assess every rubric criterion.")
        const passed = checks.every(Boolean)
        result = { passed, feedback: passed ? "Self-check recorded, not machine-graded." : "Revise the unchecked criteria and retry.", cases: [] }
      } else if (task.kind === "predict") {
        const answer = response.trim().replace(/\r\n/g, "\n")
        const accepted = task.accepted_answers ?? [task.answer]
        const passed = accepted.some((item: string) => item.trim().replace(/\r\n/g, "\n") === answer)
        result = { passed, feedback: passed ? "Correct." : "Not yet. Revise your trace, or reveal the reference for assisted practice.", cases: [] }
      } else {
        if (task.rubric?.length && checks.length !== task.rubric.length) throw new ApiError(422, "Assess every design criterion before submitting your program.")
        result = await gradeTask(env, task, code)
        if (task.rubric?.length && !checks.every(Boolean)) {
          result.passed = false
          result.feedback += " Design self-check is not complete."
        }
      }
      const now = new Date()
      const output = { ...result, task_id: taskId, attempt_id: requestId, assisted, assessment,
        created_at: isoNow(now), next_review_at: nextReview(now, Boolean(result.passed), assisted) }
      await env.DB.prepare("INSERT OR IGNORE INTO task_attempts(owner_id,id,task_id,concept_id,response,code,stdin,passed,assisted,assessment,result_json,created_at,next_review_at,request_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)")
        .bind(ownerId, requestId, taskId, concept.id, response, code, stdin, Number(Boolean(result.passed)), Number(assisted), assessment,
          JSON.stringify(output), output.created_at, output.next_review_at, requestHash).run()
      const saved = await env.DB.prepare("SELECT result_json,request_hash FROM task_attempts WHERE owner_id=? AND id=?").bind(ownerId, requestId).first()
      if (!saved || saved.request_hash !== requestHash) throw new ApiError(409, "That submission could not be saved. Retry the task.")
      return withCookie(json(stripAssessment(JSON.parse(saved.result_json))), guest.cookie)
    }
  }

  if (path === "/api/projects" && method === "GET") {
    const rows = await env.DB.prepare("SELECT id,title,description,code,created_at,updated_at FROM projects WHERE owner_id=? ORDER BY updated_at DESC")
      .bind(ownerId).all()
    return withCookie(json({ projects: rows.results ?? [] }), guest.cookie)
  }
  if (path === "/api/projects" && method === "POST") {
    const project = await body(request)
    const title = typeof project.title === "string" ? project.title.trim() : ""
    const description = typeof project.description === "string" ? project.description : ""
    const code = typeof project.code === "string" ? project.code : ""
    if (!title || title.length > 120 || description.length > 1000 || utf8Bytes(code) > MAX_SOURCE_BYTES) throw new ApiError(422, "Project title, notes or source exceed a size limit.")
    const now = isoNow()
    const id = project.id ? String(project.id) : crypto.randomUUID()
    if (!/^[a-f0-9-]{36}$/i.test(id)) throw new ApiError(422, "Project ID is invalid.")
    const existing = await env.DB.prepare("SELECT id,created_at FROM projects WHERE owner_id=? AND id=?").bind(ownerId, id).first()
    if (project.id && !existing) throw new ApiError(404, "Save or open this project before editing it.")
    if (!existing) {
      const count = await env.DB.prepare("SELECT COUNT(*) AS count FROM projects WHERE owner_id=?").bind(ownerId).first()
      if (Number(count?.count ?? 0) >= MAX_PROJECTS_PER_GUEST) throw new ApiError(429, "This guest workspace can keep up to 20 projects. Export this workspace, then erase it to start over.")
    }
    await env.DB.prepare("INSERT INTO projects(owner_id,id,title,description,code,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(owner_id,id) DO UPDATE SET title=excluded.title,description=excluded.description,code=excluded.code,updated_at=excluded.updated_at")
      .bind(ownerId, id, title, description, code, existing?.created_at ?? now, now).run()
    const saved = await env.DB.prepare("SELECT id,title,description,code,created_at,updated_at FROM projects WHERE owner_id=? AND id=?").bind(ownerId, id).first()
    return withCookie(json({ project: saved, created: !existing }), guest.cookie)
  }
  const projectRoute = path.match(/^\/api\/projects\/([^/]+)(\/files(?:\/([^/]+))?)?$/)
  if (projectRoute) {
    let projectId: string
    try { projectId = decodeURIComponent(projectRoute[1]) } catch { throw new ApiError(404, "That project does not exist.") }
    const project = await env.DB.prepare("SELECT * FROM projects WHERE owner_id=? AND id=?").bind(ownerId, projectId).first()
    if (!project) throw new ApiError(404, "Save or open this project before accessing its data workspace.")
    if (!projectRoute[2] && method === "GET") return withCookie(json(project), guest.cookie)
    if (projectRoute[2] === "/files" && !projectRoute[3] && method === "GET") {
      const rows = await env.DB.prepare("SELECT name,content FROM project_files WHERE owner_id=? AND project_id=? ORDER BY name LIMIT 201")
        .bind(ownerId, projectId).all()
      const files = (rows.results ?? []).slice(0, 200).map((row: any) => ({ name: row.name, bytes: utf8Bytes(row.content), readable: utf8Bytes(row.content) <= MAX_FILE_BYTES }))
      return withCookie(json({ files, truncated: (rows.results ?? []).length > 200 }), guest.cookie)
    }
    if (projectRoute[2] === "/files" && projectRoute[3]) {
      let name: string
      try { name = safeFilename(decodeURIComponent(projectRoute[3])) } catch (error) { if (error instanceof ApiError) throw error; throw new ApiError(422, "Data filename is invalid.") }
      if (method === "GET") {
        const row = await env.DB.prepare("SELECT name,content FROM project_files WHERE owner_id=? AND project_id=? AND name=?").bind(ownerId, projectId, name).first()
        if (!row) throw new ApiError(404, "That data file does not exist.")
        if (utf8Bytes(row.content) > MAX_FILE_BYTES) throw new ApiError(413, "This file exceeds the 64 KB text inspection limit.")
        return withCookie(json({ name, content: row.content }), guest.cookie)
      }
      if (method === "PUT") {
        const submission = await body(request)
        if (typeof submission.content !== "string" || utf8Bytes(submission.content) > MAX_FILE_BYTES) throw new ApiError(413, "Imported text must be at most 64 KB of UTF-8 bytes.")
        const existing = await env.DB.prepare("SELECT COUNT(*) AS count FROM project_files WHERE owner_id=? AND project_id=?").bind(ownerId, projectId).first()
        const hasFile = await env.DB.prepare("SELECT name FROM project_files WHERE owner_id=? AND project_id=? AND name=?").bind(ownerId, projectId, name).first()
        if (Number(existing?.count ?? 0) >= 50 && !hasFile) throw new ApiError(413, "Workspace has too many files. Remove an unused data file first.")
        await env.DB.prepare("INSERT INTO project_files(owner_id,project_id,name,content,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(owner_id,project_id,name) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at")
          .bind(ownerId, projectId, name, submission.content, isoNow()).run()
        return withCookie(json({ name, bytes: utf8Bytes(submission.content) }), guest.cookie)
      }
      if (method === "DELETE") {
        const deleted = await env.DB.prepare("DELETE FROM project_files WHERE owner_id=? AND project_id=? AND name=? RETURNING name").bind(ownerId, projectId, name).first()
        if (!deleted) throw new ApiError(404, "That data file does not exist.")
        return withCookie(json({ deleted: name }), guest.cookie)
      }
    }
  }
  const sourceRoute = path.match(/^\/api\/sources\/([^/]+)$/)
  if (sourceRoute && method === "GET") {
    let filename: string
    try { filename = decodeURIComponent(sourceRoute[1]) } catch { throw new ApiError(404, "That source PDF is not part of this course.") }
    const allowed = new Set<string>((immutableCourse.source_files ?? []).map((file: string) => file.split(/[\\/]/).at(-1)))
    for (const concept of immutableCourse.concepts as Concept[]) for (const ref of concept.source_pdfs ?? []) allowed.add(String(ref.file).split(/[\\/]/).at(-1))
    if (!allowed.has(filename) || !filename.toLowerCase().endsWith(".pdf")) throw new ApiError(404, "That source PDF is not part of this course.")
    const sourceUrl = `https://raw.githubusercontent.com/tsukumivi/CC2/main/notes/${encodeURIComponent(filename)}`
    const range = request.headers.get("range")
    const upstream = await fetch(sourceUrl, range ? { headers: { range } } : undefined)
    if (!upstream.ok && upstream.status !== 206) throw new ApiError(upstream.status === 404 ? 404 : 502, "The public source PDF is temporarily unavailable from GitHub.")
    const headers = new Headers(upstream.headers)
    headers.set("content-type", "application/pdf")
    headers.set("content-disposition", `inline; filename*=UTF-8''${encodeURIComponent(filename)}`)
    headers.set("x-content-type-options", "nosniff")
    headers.set("cache-control", "public, max-age=3600")
    return withCookie(new Response(upstream.body, { status: upstream.status, headers }), guest.cookie)
  }
  return withCookie(json({ detail: "Endpoint not found." }, 404), guest.cookie)
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(request)
    try { return await routeApi(request, env) }
    catch (error) {
      if (error instanceof ApiError) return json({ detail: error.message }, error.status)
      console.error("Java Fieldnotes request failed", error instanceof Error ? error.message : "Unknown error")
      return json({ detail: "The Studio could not complete that request. Retry, or reload the page." }, 500)
    }
  },
  async scheduled(_controller: unknown, env: Env): Promise<void> {
    const cutoff = isoNow(new Date(Date.now() - 90 * 86_400_000))
    await env.DB.batch([
      env.DB.prepare("DELETE FROM project_files WHERE owner_id IN (SELECT owner_id FROM guest_sessions WHERE last_seen_at<?)").bind(cutoff),
      env.DB.prepare("DELETE FROM projects WHERE owner_id IN (SELECT owner_id FROM guest_sessions WHERE last_seen_at<?)").bind(cutoff),
      env.DB.prepare("DELETE FROM task_attempts WHERE owner_id IN (SELECT owner_id FROM guest_sessions WHERE last_seen_at<?)").bind(cutoff),
      env.DB.prepare("DELETE FROM task_drafts WHERE owner_id IN (SELECT owner_id FROM guest_sessions WHERE last_seen_at<?)").bind(cutoff),
      env.DB.prepare("DELETE FROM task_draft_generations WHERE owner_id IN (SELECT owner_id FROM guest_sessions WHERE last_seen_at<?)").bind(cutoff),
      env.DB.prepare("DELETE FROM guest_sessions WHERE last_seen_at<?").bind(cutoff),
    ])
  },
}
