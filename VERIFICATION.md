# Verification — Practical Java Fieldnotes

## Implementation and final primary review: passed

Executed on Windows 11 on 2026-10-11. All product implementation stayed inline. No Sol implementation subagent was used. Luna xhigh completed a source-packet review and found two logic defects. Both were fixed inline. Maria explicitly requested primary self-review and iterative verification instead of another reviewer invocation; no further agent was dispatched.

| Check | Actual executed result | Evidence |
|---|---|---|
| Backend / storage / grading regressions | 48 passed after review fixes | `artifacts/pytest-results.xml` |
| Frontend routing / draft / review helpers | 5 passed, 0 failed | Node test output |
| TypeScript and production build | Passed; 57 modules transformed | `frontend/dist/` and build output |
| Full executable corpus | Passed; 255 aggregate checks, 125 unique compilable sources, 52 references, 38 runnable worked examples | `artifacts/corpus-verification.json` |
| Native export | Passed: unwrapped Main.java compiles; save, separate-JVM restart, file contents and corrupt-file retention | `artifacts/portability-verification.json` |
| Real Chrome editor | Passed: theme preserves undo/redo; Tab indents; Escape then Tab releases focus | `scripts/editor_qa.py` execution |
| Real Chrome workflow | 15 checks passed, no page errors; all six loaded views fit 390px | `artifacts/browser-qa/results.json` and screenshots |
| Python lint | Passed after correcting import formatting | Ruff execution |
| Original source-note integrity | All 9 notes match opaque SHA-256 hashes of archive entries; notes inventory unchanged | `artifacts/release-audit.json` |
| Uika design | Bundled 8 file hashes/provenance passed; 38 complete tokens per theme; canonical CSS byte-equal to estate source | `uika-design/verify.mjs` output; release audit |
| Scoped static safety scan | No findings in authored application/content/test source | `artifacts/release-audit.json` |

The corpus audit compiles actual Java and runs each reference/example in an isolated workspace. Restart steps use separate JVMs with the same case files. Non-completion checks execute starter cases, not fabricated result stubs. The 255 total is aggregate audit assertions, not a claim of 255 independent programs or exhaustive input coverage.

Backend coverage includes failed/assisted/independent progression, real compilation and runtime errors, timeouts, output truncation, UTF-8 source/input/output, byte limits, unavailable-toolchain recovery, occupied capacity, legacy SQLite startup preservation, project isolation/data persistence, platform filenames and malformed origins/hosts. Unicode stdout comparison accounts for actual Windows CRLF rather than changing returned output.

Browser coverage includes hidden answers before prediction, drafts across navigation/reload, failure/fresh retry, actual wrong-output grading and progression, saved source/evidence history, reference assistance, empty filters, saved capstone source, persistent files across JVMs, corrupt-file retention, shelf reopen, local PDF, persisted themes/local fonts, loaded mobile layouts, skip-link focus and truthful offline state. All browser-generated projects/attempts belong to explicitly isolated QA storage, not a learner record.

## Defects caught during verification

- Reference/assistance and failed-attempt due scheduling, Windows reserved filenames, and malformed loopback-host/origin handling received regressions and fixes.
- Theme changes formerly rebuilt CodeMirror and lost undo history; compartment reconfiguration now passes a real Chrome regression.
- An unsuccessful JDK probe could remain cached; actual missing-then-restored-JDK regression now passes. Compiler/program heaps are explicitly bounded.
- Early screenshots sometimes captured loading instead of the completed page; final theme/mobile checks wait for loaded content.
- An interrupted parallel corpus run had two actual process failures. It was terminated, not counted as a pass. The complete serial rerun passed all 255 checks. Resource pressure was observed; no unproved root-cause claim is made.
- Test-authoring mistakes (a wrong capacity symbol and assuming LF from Windows println) were corrected; the final expanded suite passed 41 tests.
- A clipped read introduced a source sentinel during a whole-file replacement. The source was repaired; the final build, browser regression and sentinel scan pass. Future edits should be narrow patches, never full replacements from clipped reads.

## Independent review / final delivery

The first read-only Luna attempt was blocked by tool policy; its successful CLI exit was not approval. The tool-free frozen-source retry completed and returned `passed: false` with two logic findings and no security findings (`artifacts/luna-review-packet.json`). It did not independently execute runtime tests.

Maria then authorized direct inline fixes and primary self-review to streamline delivery. The primary session reviewed the changed assessment/draft routes, transaction ordering, idempotency, migration, browser-cache generations, delayed callbacks and transport types. This is primary self-review, **not a later Luna approval**.

1. **Automatic answer exposure:** removed reference answers/explanations from assessment responses and the feedback UI. Existing stored results are filtered on history and idempotent replay, so old keys cannot leak through those paths. Explicit reference/hint routes still mark assistance. Three regression cases first failed and then passed.
2. **Retry/autosave race:** introduced a durable draft generation. Retry advances it and clears the draft in one immediate SQLite transaction; saves validate generation and preserve assistance under the same write lock. Stale submissions are rejected too, including a second generation check before recording a completed assessment. Existing generation-zero drafts and request hashes remain compatible. The client carries generations through loading/retry/saves and ignores old-generation save replies. Three race/generation regressions first failed and then passed; same-generation assistance is also covered.

Real Chrome tests deliberately held an old autosave **before reaching the server** (eventual HTTP 409) and held an already-successful save **before its response reached the UI** (HTTP 200 with an old generation). In both cases the fresh draft stayed empty/unassisted and survived reload; a new-generation independent submission passed. See `artifacts/review-fixes-browser.json`: four checks, no page errors. The original 15-check browser workflow and editor history/focus test also passed again on isolated port 4173.

The full backend rerun passed 48 tests; Node helpers passed five; typecheck/production build, lint, native capstone portability, source-note integrity and design verification passed. Fourteen course/Java-runner source files were compared against the frozen reviewed manifest and remain unchanged. The existing full 255-check Java corpus result is retained, not falsely described as a new post-fix run.

A clean runtime-only virtual environment installed all 14 locked dependencies from cached wheels. Clean extracted-archive startup/run checks and archive integrity are recorded in `artifacts/delivery-verification.json` when the release is finalized.

The normal learner server was restored separately from isolated QA. No learner database or workspaces are distributed; no learner records were reset for testing.

## Limits of this evidence

- Trusted local Java execution is not an OS sandbox; host filesystem/network access remains possible. Heaps are not total process-memory ceilings. Use one server worker on loopback.
- Explanation/design checks are learner self-assessments, not semantic machine grading. Local answer keys mean independence is not cheat-proof.
- Tested on this Windows environment only; other supported-intent platforms/versions are not validated here.
- Human learning effectiveness, delayed retention and independent transfer are unmeasured. `LEARNER-TRIAL.md` is a protocol, not simulated learner results.

## Re-run

Use the commands in `README.md`. Keep JVM-heavy suites serial on this laptop. Browser QA requires `JAVA_STUDIO_QA_MODE=1` and a non-default `JAVA_STUDIO_DATA_DIR`; never reset or test on normal learner data.
