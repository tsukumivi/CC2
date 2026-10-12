# Practical Java Studio — Implementation Contract

Scope approved by Maria on 2026-10-11. Implements CORPUS-REVIEW-AND-PLAN.md, not only a prototype or a vertical slice.

## Locked Decisions
- Implementation stays inline in the primary session. No Sol subagents. A Luna reviewer with xhigh effort may run only after all approved amendments and initial verification are complete.
- Keep the local FastAPI/SQLite and React/CodeMirror application. No remote grading, accounts, telemetry, AI dependency, or new desktop shell.
- Keep the original notes and archive untouched. New explanations/examples are explicitly authored course material, not implied quotations from PDFs.
- Preserve Uika's canonical light/dark tokens verbatim. Validate the bundled provenance. Keep local fonts, readable contrast, keyboard access, reduced motion, and responsive layouts.
- Endpoint: independently produce, test, and run a small maintainable Java console record manager with recovery, methods, collections, objects, and restart persistence. No professional-readiness claim.
- Manual explanation checks are learner self-assessments. Exact/output tasks are checked by the server. Passing supplied tests is evidence for their scope, not a proof of correctness or genuine independence.
- Java execution is for trusted local code only; it is NOT a security sandbox. Bind loopback, reject foreign origins/hosts, bound execution/output, and document host filesystem/network access.

## Acceptance Checklist

### Integrity & Progress
- [x] Every runnable starter/example uses real source line breaks; intentional Java string escapes retain their meaning.
- [x] Every lesson belongs to exactly one matching module. Explicit prerequisites refer to earlier lessons. Optional ternary work does not block the core route.
- [x] Initial algorithm/flowchart/pseudocode activities require no untaught Java syntax.
- [x] Diagram, walkthrough, prediction, answer key, example, and activity describe the same rules.
- [x] Reviewer covers every core concept with meaningful predict, explain, repair/modify/build practice; reference answers remain hidden until explicit assistance-marking reveal. Payload history and idempotent replay do not expose legacy answer keys.
- [x] No recall key is inferred from a different trace. Each task owns its answer/rubric.
- [x] Save drafts, responses, Java source, test evidence, assistance state, time, and retry history locally.
- [x] Client-supplied scores cannot establish completion. Free text uses explicit self-check criteria, never keyword pseudo-grading.
- [x] Compilation alone and any failed attempt do not mark a task or lesson complete.
- [x] Continue advances through completed core requirements. Prerequisites and weak/due review are visible without locking browsing.
- [x] Record reference-assisted practice separately from independent assessed completion.

### Full Curriculum
- [x] Program structure, output, comments, naming, compiler diagnostics and language-independent planning.
- [x] Variables/types, escapes, calculations, decimal versus integer division, assignment/update operations.
- [x] Scanner tokens versus lines, text operations, strict numeric conversion and recovery introduced when needed.
- [x] Decisions, String content equality, Boolean rules, guards, switch, optional ternary.
- [x] while/for/do-while, counters/accumulators, termination, retry, repeated menus and boundaries.
- [x] Methods/parameters/returns/scope, specific exceptions, systematic debugging and test tables.
- [x] Arrays/search, ArrayList, basic classes/constructors/fields/encapsulation, inventory project.
- [x] UTF-8 file save/load, missing/malformed files, overwrite/append, resource handling and restart tests.
- [x] Capstone: repeatable record manager, invalid-input recovery, separate methods/record objects, documented format, restart persistence and requirements-based test evidence.
- [x] A running project grows across stages, alongside independent-domain transfer tasks.
- [x] Explain → predict → scaffolded repair/modify → build → revisit. Scaffolding reduces as complexity rises.
- [x] Correct reference solutions with normal, boundary and failure cases. Explain why the tempting wrong approach fails.
- [x] Source ledger separates original lecture references from authored expansion and technical Java references.

### Application
- [x] Guided lesson route and practical review modes share the same durable task contract.
- [x] Code Bench retains editor history, standard input, bounded stdout/stderr and actionable compile/runtime feedback.
- [x] Save/open/download projects; preserve per-project local data files and demonstrate cross-run persistence.
- [x] Inspect/import/export project data safely; no traversal, accidental fixture reuse, arbitrary project folder selection or deletion without confirmation.
- [x] Source PDF links open locally. Original Java notes are not automatically executed or exposed as modern reference solutions.
- [x] Activity checks do not execute learner code against hidden system paths. Validation uses explicit fresh test workspaces and transparent fixtures.
- [x] Navigation and editor drafts survive view changes/reload; stale async results cannot complete the wrong task.
- [x] Empty/offline/error/loading states, keyboard controls, clear saving state, mobile and both Uika themes.

### Verification & Delivery
- [x] Red → green regressions for persistence, grading, progress and corpus defects; unit/API/storage tests pass.
- [x] Compile every authored runnable example/starter/reference under Java 21. Run every reference against its declared cases. Run starters to confirm predictable, purposeful non-completion.
- [x] Exercise timeout, output limit, syntax/runtime errors, UTF-8 input/output, absent toolchain and byte limits.
- [x] Exercise legacy SQLite migration without deleting old progress/projects. New independent mastery cannot inherit unchecked legacy scores.
- [x] Browser tests exercise actual Java grading, review failure/retry, navigation/reload, project save/open/file persistence, themes and narrow layout.
- [x] Build/typecheck, code lint/security review, bundled design provenance and canonical CSS equality pass.
- [x] Setup/run/test instructions work on this machine and specify portability expectations; dependencies are reproducible.
- [x] Luna xhigh completed the initial source review after the initial gate. Correct both findings inline and re-run affected tests; final primary self-review authorized by Maria instead of another agent invocation.
- [x] Provide executed evidence, exact run instructions, remaining limitations and learner-trial protocol. Human learning effectiveness stays unverified until an actual learner trial.

## Execution State
Initial baseline: pnpm frozen install and frontend production build passed. Python environment created locally. Microsoft OpenJDK 21 downloaded to .tools from the vendor redirect; system Java/PATH were not changed. Bundled design hashes and canonical CSS match passed. No implementation delegate has been started.

Verification output and final counts belong in VERIFICATION.md. This file is an operational checklist, not agent-governing instructions.
