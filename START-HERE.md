# Start here — Java Fieldnotes

This is the updated practical Java learning studio. The browser UI is already built; no Node, pnpm, AI service or account is needed to use it.

## Windows quick start

1. Extract the ZIP. Open PowerShell **inside** the extracted `Java-Fieldnotes-Learning-Studio` folder, beside `README.md` and `runtime-lock.txt`.
2. Install Python and a **full JDK 21 or later** (both `java` and `javac`). The tested interpreter was Python 3.14. Other platforms/versions remain unverified.
3. Create the Python environment and install the locked runtime:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r runtime-lock.txt
```

If you already use uv, the equivalent is `uv venv .venv`, then `uv pip install --python .\.venv\Scripts\python.exe -r runtime-lock.txt`.

4. Make your full JDK visible through `JAVA_HOME` or PATH. A JRE/Java 8 is not enough. For example, replace the placeholder path below with your actual JDK folder:

```powershell
$env:JAVA_HOME = 'C:\path\to\your\jdk-21'
Remove-Item Env:JAVA_STUDIO_DATA_DIR -ErrorAction SilentlyContinue
Remove-Item Env:JAVA_STUDIO_QA_MODE -ErrorAction SilentlyContinue
& .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

5. Open **http://127.0.0.1:8000** in your browser. Keep PowerShell open; Ctrl+C stops the server. Use one worker and keep it on loopback. If the page reports a missing JDK, correct JAVA_HOME/PATH and restart.

## What is included

- Source, prebuilt frontend, local fonts/licenses, prerequisite-ordered course and five original source PDFs.
- Original Luna findings plus primary fix-review and executed test evidence. The two findings are fixed; no subsequent Luna approval is claimed.
- Clean runtime dependency lock and optional development/verification lock.

The archive excludes learner/QA data, local environments, node_modules, JDK binaries and legacy Java demonstrations. Your progress/database and saved-project files are created locally under `data/` on first use. Initial dependency/JDK installation may need Internet access; the application itself has no remote grading or AI dependency.

Use Java code you trust: execution is bounded but **not an OS sandbox**. Explanations/design use disclosed learner self-checks. Automated checks do not prove learning effectiveness. See `README.md`, `VERIFICATION.md` and `LEARNER-TRIAL.md`.

Made with love by Maria.
