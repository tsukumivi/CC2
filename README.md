# Java Fieldnotes — Practical Learning Studio

A local-first Java course and code workspace. The endpoint is a small console record manager with bad-input recovery, methods, objects, collections and restart persistence. This is a practical foundation, **not professional-readiness certification or evidence of proven learning outcomes**.

Made with love by Maria — https://github.com/mariyaholic

## Course and application

The authored course has **8 stages, 42 lessons (41 core), 136 tasks and 8 optional novel-domain transfer programs**:

1. First working program; structure, output, diagnostics and language-independent planning.
2. Values, types, escapes, arithmetic and assignment.
3. Input, tokens versus lines, text and strict numeric conversion.
4. Decisions, Boolean rules, guards, String equality and switch; optional ternary.
5. Loops, termination, counters, accumulators, retry and repeated menus.
6. Methods, parameters, returns, scope, specific exceptions, debugging and test tables.
7. Arrays, searching, ArrayList, classes, constructors and encapsulation.
8. UTF-8 persistence, recovery, append/overwrite, resource handling and a record-manager capstone.

**Study Desk** suggests the next unfinished core lesson. **Learning Path** supplies explanations, numbered connection models, worked traces and explain/predict/repair/modify/build tasks. **Practical Review** has weak/due/new queues. **Code Bench** runs real Java. **Project Shelf** keeps source and each project's data. **Source Library** distinguishes original PDFs from authored expansion.

## Optional public website

For a no-login public pilot with a host-provided `workers.dev` URL and isolated Java execution, follow [the Cloudflare deployment guide](cloudflare/DEPLOY.md). That setup uses Cloudflare Workers Static Assets and D1 on their Free plans, streams the five public class PDFs from this repository, and runs Java through SandboxAPI Basic. The shared free runner allowance is up to 500 Java executions each month. One source PDF contains an instructor contact email; review sharing permission and that contact detail before deployment. The existing local Python/JDK workflow remains available and is still the default for the shared ZIP.

### Assessment contract

- Predictions check their own declared answer on the server. Program tasks compile and run declared cases, including file/restart checks. Compilation alone is not completion. Output comparison normalizes line endings and outer whitespace.
- Explanations and structural design criteria use explicit **learner self-checks**, not keyword grading or an AI judge.
- A core lesson needs all required independent checks. Hint/reference use marks assistance. Submission feedback and history never reveal reference answers; use the explicit assistance-marking Reveal Reference flow. Fresh Attempt resets a draft, not saved history. Its durable generation rejects older autosaves/submissions, including delayed writes from another tab.
- Failed checks are due now; assisted passes in one day; independent passes in three days. Optional transfer programs revisit a skill in another domain without becoming progression gates.
- This is not cheat-proof: source and answers exist locally. Passing shows the stated checks and learner confirmations were met, not honest independence or correctness for every input.

## Start the shared ZIP

Extract the ZIP, open PowerShell in its `Java-Fieldnotes-Learning-Studio` folder, and follow `START-HERE.md`. Install Python and a full JDK 21+ first. The built frontend is included, so **Node/pnpm are not needed just to use the app**.

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r runtime-lock.txt
Remove-Item Env:JAVA_STUDIO_DATA_DIR -ErrorAction SilentlyContinue
Remove-Item Env:JAVA_STUDIO_QA_MODE -ErrorAction SilentlyContinue
& .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. One server serves the built frontend and API. Keep the terminal open; Ctrl+C stops it. Use one worker. Never expose the port, bind `0.0.0.0`, or use it as a shared multi-user service.

The shared archive contains source, built frontend assets, local fonts/licenses, the five original PDFs and verification evidence. It excludes local environments, JDK binaries, node_modules, learner/QA data and historical Java demonstrations. The original archive/notes remain untouched on the development machine. `runtime-lock.txt` pins the small tested runtime; `requirements-lock.txt` is optional for the full development/verification environment.

## Reproduce setup

Validated here on Windows 11, Python 3.14, Node 26 and Microsoft JDK 21. Python 3.11+, Node 22+ and a full JDK 21+ are intended requirements; other platforms/versions remain untested.

`requirements-lock.txt` pins the full tested runtime and verification environment; `frontend/pnpm-lock.yaml` locks frontend resolutions. `requirements.txt` is the smaller runtime declaration.

```powershell
# uv is installed on this computer. At the project root:
uv venv .venv
uv pip install --python .\.venv\Scripts\python.exe -r requirements-lock.txt
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend run build
& .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Without uv, use `python -m venv .venv` then `.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt`. Do not assume this machine's system Python includes pip.

Install a full JDK 21+ using its vendor's installer, set `JAVA_HOME`, or extract a `jdk-*` folder under `.tools`. The app checks a complete runtime/compiler pair: JAVA_HOME first, portable JDK next, PATH last. Java 8 alone is insufficient. Restart after changing a working toolchain; unsuccessful probes are retried instead of cached forever.

**Development only:** start the API, then `pnpm --dir frontend dev --host 127.0.0.1`. Vite uses strict port **5173**, forwarding `/api` to 8000. Production needs no Vite process. Build `frontend/dist` before starting a fresh production server.

## Source and data workflow

Code uses `public class Main`. Standard Input is a **complete batch**, not a live terminal: supply every required line before Run; stdin closes afterward. Saved projects run in separate persistent workspaces. Unsaved programs run in fresh temporary directories.

Data controls inspect/import/edit/export/delete UTF-8 files up to 64,000 bytes. Supported extensions: `.txt`, `.csv`, `.json`, `.md`, `.log`, `.dat`. The API rejects traversal, Windows device names and replacing class/source files. Source copies do not silently copy another project's data. Export `Main.java` and data files separately. Deletion asks for confirmation.

### Run exported Main.java without the app

Put it in its own folder. Use a JDK on PATH, or this copy's portable JDK explicitly:

```powershell
$Jdk = $env:JAVA_HOME # Set this to the full JDK installation, not a JRE.
# Change into the folder containing your downloaded Main.java.
& "$Jdk\bin\javac.exe" --release 21 -encoding UTF-8 -proc:none Main.java
& "$Jdk\bin\java.exe" -Dfile.encoding=UTF-8 Main
```

Stdin is interactive here. For the capstone: `add|Orbit|2`, `save`, `q`; run again with `list`, `q`. Its `records.txt` format is one `name|quantity` record per line. The portability audit compiles **unwrapped Main.java** and checks save, restart and corrupt-file retention without an HTTP server.

## Storage and backup

Default storage: **`data/learning.db`** and **`data/workspaces/<project-id>/`**. SQLite retains drafts, responses, Java source, actual grading evidence, assistance flags and attempt history. Browser storage is an additional draft cache; the saving label distinguishes browser caching from successful SQLite sync.

Legacy projects and activity are retained. Unchecked legacy scores do not become independent completion. Back up by stopping the server and copying **the entire `data/` directory**. Never delete learner data to reset QA.

`JAVA_STUDIO_DATA_DIR` selects another store. Browser QA also requires `JAVA_STUDIO_QA_MODE=1` and non-default storage; it refuses ordinary learner storage.

## Safety and resource limits

**Trusted local code only. Not an OS sandbox.** Java has your account's filesystem/network permissions. Never paste untrusted code. Other local processes and explicitly allowed loopback web origins can access this unauthenticated API.

Limits per server process: two Java jobs, 20-second compilation, default 4-second run, 48,000 UTF-8 source bytes, 8,000 stdin bytes and 16,000 captured bytes per output stream. Heaps are explicit: 256 MB compiler, 128 MB program; these are **not total native/JVM memory ceilings**. Timeouts terminate process trees. Learner Java receives a restricted environment, not inherited API credentials. These controls reduce accidents, not deliberate host I/O or network behavior.

The default local application needs no remote grader, account, AI service or hosted font. The optional public deployment sends Java source and run inputs to its disclosed remote sandbox provider. Official Java links are optional external navigation. Arbitrary learner code is not necessarily offline.

## Verification

See `VERIFICATION.md` for executed evidence and `IMPLEMENTATION-STATUS.md` for acceptance coverage. Run heavy JVM suites **serially** on this laptop.

```powershell
& .\.venv\Scripts\python.exe -m pytest tests -q
& .\.venv\Scripts\ruff.exe check backend content scripts tests
node --experimental-strip-types --test frontend/tests/learning.test.ts
pnpm --dir frontend run build
& .\.venv\Scripts\python.exe scripts/verify_course.py
& .\.venv\Scripts\python.exe scripts/verify_portability.py
node uika-design/verify.mjs
```

Real browser QA needs installed Chrome (the scripts use its Windows path) and an **isolated server**. Stop the normal server first:

```powershell
$env:JAVA_STUDIO_QA_MODE='1'
$env:JAVA_STUDIO_DATA_DIR=(Join-Path (Get-Location) 'artifacts/qa-data')
& .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# In another terminal at the project root:
& .\.venv\Scripts\python.exe scripts/editor_qa.py
& .\.venv\Scripts\python.exe scripts/browser_qa.py
```

Then stop QA, clear both variables and restart normally. Reports/screenshots are under `artifacts/`; QA projects must not masquerade as a learner's work.

## Provenance and remaining evidence

Original notes/archive remain untouched. Original PDFs are local with page/provenance references; expanded explanations/exercises/solutions are authored material, not PDF quotations. Historical Java notes are not executed or exposed as modern reference solutions; demonstration credentials are not repeated in authored material. The capstone gives a requirement trace rather than its full build solution as an ordinary worked example.

Both Uika themes preserve supplied canonical tokens. Outfit, Cinzel and JetBrains Mono are local with their licenses. Automated code/storage/browser checks establish implementation behavior, **not educational effectiveness**. `LEARNER-TRIAL.md` defines the next human trial and delayed transfer check.
