from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

ROOT_DIR = Path(__file__).resolve().parents[1]
COURSE_PATH = ROOT_DIR / "content" / "course.json"
DATA_DIR = Path(os.environ.get("JAVA_STUDIO_DATA_DIR", str(ROOT_DIR / "data")))
DATABASE_PATH = DATA_DIR / "learning.db"
MAX_SOURCE_BYTES = 48_000
MAX_STDIN_BYTES = 8_000
MAX_OUTPUT_BYTES = 16_000
DEFAULT_RUN_TIMEOUT = 4.0


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_time(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat(timespec="seconds")


def get_course() -> dict:
    with COURSE_PATH.open("r", encoding="utf-8-sig") as course_file:
        course_data = json.load(course_file)
    concepts_by_id = {item["id"]: item for item in course_data.get("concepts", [])}
    for module in course_data.get("modules", []):
        module["concepts"] = [
            concepts_by_id[concept_id]
            for concept_id in module.get("concept_ids", [])
            if concept_id in concepts_by_id
        ]
    return course_data


def connect_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize_db() -> None:
    with connect_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS concept_progress (
                concept_id TEXT PRIMARY KEY,
                attempts INTEGER NOT NULL DEFAULT 0,
                explain_best REAL NOT NULL DEFAULT 0,
                trace_best REAL NOT NULL DEFAULT 0,
                guided_best REAL NOT NULL DEFAULT 0,
                build_best REAL NOT NULL DEFAULT 0,
                last_result TEXT,
                last_activity_type TEXT,
                last_attempt_at TEXT,
                mastered_at TEXT,
                next_review_at TEXT
            );
            CREATE TABLE IF NOT EXISTS attempts (
                id TEXT PRIMARY KEY,
                concept_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                score REAL NOT NULL,
                response TEXT,
                code TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (concept_id) REFERENCES concept_progress(concept_id)
            );
            CREATE INDEX IF NOT EXISTS idx_attempts_concept_time
                ON attempts(concept_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                code TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_db()
    from backend.learning import initialize
    initialize(sys.modules[__name__])
    yield


app = FastAPI(
    title="Java Learning Studio API",
    version="0.1.0",
    description="Local-first learning progress and Java execution API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def loopback_only(request: Request, call_next):
    """Keep all app endpoints local to this computer, including the code runner."""
    from urllib.parse import urlsplit
    origin = request.headers.get("origin")
    if origin:
        try:
            value = urlsplit(origin)
            valid_origin = (value.scheme == "http" and value.hostname in ("127.0.0.1", "localhost", "::1")
                            and value.port in (8000, 5173, 4173) and not value.username and not value.password
                            and not value.path and not value.query and not value.fragment)
        except ValueError:
            valid_origin = False
        if not valid_origin:
            return fastapi_response(403, {"detail": "Use the local Studio origin."})
    allowed_hosts = {host for host in ("127.0.0.1", "localhost", "[::1]")}
    allowed_hosts |= {f"{host}:{port}" for host in tuple(allowed_hosts) for port in (8000, 5173, 4173)}
    if request.headers.get("host", "").lower() not in allowed_hosts:
        return fastapi_response(403, {"detail": "Use localhost or 127.0.0.1, not a custom host."})
    client = request.client
    if client is None:
        return fastapi_response(403, {"detail": "This application only accepts local connections."})
    host = client.host.split("%", 1)[0]
    if host.lower() == "localhost":
        return await call_next(request)
    try:
        import ipaddress

        if ipaddress.ip_address(host).is_loopback:
            return await call_next(request)
    except ValueError:
        pass
    return fastapi_response(403, {"detail": "This application only accepts local connections."})


def fastapi_response(status_code: int, body: dict):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status_code, content=body)


@lru_cache(maxsize=1)
def _discover_java_toolchain() -> dict:
    """Use one complete JDK pair: explicit JAVA_HOME, local portable JDK, then PATH."""
    suffix = ".exe" if os.name == "nt" else ""
    homes = []
    if os.environ.get("JAVA_HOME"):
        homes.append(Path(os.environ["JAVA_HOME"]))
    homes.extend(sorted((ROOT_DIR / ".tools").glob("jdk-*"), reverse=True))
    pairs = [(h / "bin" / ("java" + suffix), h / "bin" / ("javac" + suffix)) for h in homes]
    if shutil.which("java") and shutil.which("javac"):
        pairs.append((Path(shutil.which("java") or ""), Path(shutil.which("javac") or "")))
    for java_path, javac_path in pairs:
        if not java_path.is_file() or not javac_path.is_file() or java_path.resolve().parent != javac_path.resolve().parent:
            continue
        try:
            probe_options = [["-Xmx64m", "-XX:+UseSerialGC"], ["-J-Xmx128m", "-J-XX:+UseSerialGC"]]
            versions = [subprocess.run([str(p), *options, "-version"], capture_output=True, text=True, timeout=15, check=True,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                        for p, options in zip((java_path, javac_path), probe_options, strict=True)]
            text = [(v.stdout + v.stderr).strip().splitlines()[0] for v in versions]
            match = re.search(r"javac (\d+)", text[1])
            runtime = re.search(r'(?:openjdk|java) version "(\d+)', text[0])
            if not match or not runtime or int(match.group(1)) < 21 or int(runtime.group(1)) < 21:
                continue
            return {"jdk_available": True, "runner_ready": True, "java_version": text[0], "compiler_version": text[1],
                    "java_path": str(java_path), "javac_path": str(javac_path), "setup_message": "Java 21+ JDK ready. Trusted local code only; not a sandbox."}
        except (OSError, subprocess.SubprocessError, IndexError):
            continue
    return {"jdk_available": False, "runner_ready": False, "java_version": None, "compiler_version": None,
            "java_path": None, "javac_path": None, "setup_message": "Install a full JDK 21 or newer. Set JAVA_HOME or place its extracted jdk-* folder under .tools, then restart the Studio."}


def java_toolchain() -> dict:
    tools = _discover_java_toolchain()
    if not tools["jdk_available"]:
        # A failed probe or missing installation must not poison later requests.
        _discover_java_toolchain.cache_clear()
    return tools


java_toolchain.cache_clear = _discover_java_toolchain.cache_clear


@app.get("/api/health")
def health() -> dict:
    tools = java_toolchain()
    return {
        "status": "ok",
        "app": "Java Learning Studio",
        "storage": "local SQLite",
        "qa_mode": os.environ.get("JAVA_STUDIO_QA_MODE") == "1" and DATA_DIR.resolve() != (ROOT_DIR / "data").resolve(),
        "runner_isolation": "temporary directory, compile/run timeouts, bounded output, and a 128 MB Java heap; not an operating-system sandbox",
        **tools,
    }


@app.get("/api/course")
def course() -> dict:
    data = get_course()
    for concept in data.get("concepts", []):
        for task in concept.get("tasks", []):
            for key in ("answer", "accepted_answers", "reference_code", "explanation", "walkthrough"):
                task.pop(key, None)
            task["hint_count"] = len(task.pop("hints", []))
    return data


def progress_state(row: sqlite3.Row | None) -> dict:
    values = dict(row) if row else {}
    attempts = int(values.get("attempts", 0) or 0)
    return {
        "concept_id": values.get("concept_id"),
        "status": "practiced" if attempts else "not_started",
        "attempts": attempts,
        "last_result": values.get("last_result"),
        "last_activity_type": values.get("last_activity_type"),
        "last_attempt_at": values.get("last_attempt_at"),
    }


@app.get("/api/progress")
def get_progress() -> dict:
    course_data = get_course()
    with connect_db() as db:
        rows = {row["concept_id"]: row for row in db.execute("SELECT * FROM concept_progress")}
    concepts = []
    for concept in course_data["concepts"]:
        item = progress_state(rows.get(concept["id"]))
        item["title"] = concept.get("title", concept["id"])
        item["module_id"] = concept["module_id"]
        concepts.append(item)
    practiced_count = sum(1 for item in concepts if item["attempts"] > 0)
    return {
        "concepts": concepts,
        "summary": {
            "total_concepts": len(concepts),
            "practiced_concepts": practiced_count,
            "not_started_concepts": len(concepts) - practiced_count,
            "activity_count": sum(item["attempts"] for item in concepts),
        },
    }


class ProgressSubmission(BaseModel):
    concept_id: str = Field(min_length=1, max_length=100)
    activity_type: str = Field(min_length=1, max_length=60)
    result: str | bool | dict[str, object] | None = None
    score: float | None = Field(default=None, ge=0, le=1)
    correct: bool | None = None
    response: str | None = Field(default=None, max_length=5_000)
    code: str | None = Field(default=None, max_length=MAX_SOURCE_BYTES)


@app.post("/api/progress")
def save_progress(submission: ProgressSubmission) -> dict:
    raise HTTPException(409, "Unchecked progress submissions are retired. Submit a course task instead.")


class ProjectSubmission(BaseModel):
    id: str | None = Field(default=None, max_length=100)
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1_000)
    code: str = Field(default="", max_length=MAX_SOURCE_BYTES)


@app.get("/api/projects")
def list_projects() -> dict:
    with connect_db() as db:
        rows = db.execute(
            "SELECT id, title, description, code, created_at, updated_at FROM projects ORDER BY updated_at DESC"
        ).fetchall()
    return {"projects": [dict(row) for row in rows]}


@app.post("/api/projects")
def save_project(project: ProjectSubmission) -> dict:
    from backend.runner import check_bytes
    check_bytes(project.code)
    if not project.title.strip():
        raise HTTPException(422, "Give the project a nonempty title.")
    if project.id:
        from backend.workspaces import project as lookup_project
        lookup_project(sys.modules[__name__], project.id)
    now = iso_time()
    project_id = project.id or str(uuid.uuid4())
    with connect_db() as db:
        existing = db.execute("SELECT id, created_at FROM projects WHERE id = ?", (project_id,)).fetchone()
        created = existing is None
        if existing:
            db.execute(
                """UPDATE projects SET title = ?, description = ?, code = ?, updated_at = ?
                   WHERE id = ?""",
                (project.title.strip(), project.description, project.code, now, project_id),
            )
        else:
            db.execute(
                """INSERT INTO projects (id, title, description, code, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project_id, project.title.strip(), project.description, project.code, now, now),
            )
        db.commit()
        saved = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return {"project": dict(saved), "created": created}


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str | None = Field(default=None, max_length=64)
    source: str = Field(min_length=1, max_length=MAX_SOURCE_BYTES)
    stdin: str = Field(default="", max_length=MAX_STDIN_BYTES)
    timeout_seconds: float = Field(default=DEFAULT_RUN_TIMEOUT, ge=0.5, le=8.0)


class BoundedCapture:
    def __init__(self, limit: int):
        self.limit = limit
        self.data = bytearray()
        self.truncated = False

    def read_pipe(self, pipe) -> None:
        try:
            while True:
                chunk = pipe.read(4096)
                if not chunk:
                    break
                remaining = self.limit - len(self.data)
                if remaining > 0:
                    self.data.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    self.truncated = True
        finally:
            pipe.close()

    def text(self) -> str:
        output = self.data.decode("utf-8", errors="replace")
        if self.truncated:
            output += "\n[Output truncated at 16 KB.]"
        return output


def run_bounded(command: list[str], cwd: Path, stdin_text: str, timeout_seconds: float) -> dict:
    stdout_capture = BoundedCapture(MAX_OUTPUT_BYTES)
    stderr_capture = BoundedCapture(MAX_OUTPUT_BYTES)
    # Do not hand arbitrary inherited API tokens to learner programs.
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "LANG", "LC_ALL", "HOME"}
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    process = subprocess.Popen(command, cwd=str(cwd), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=False, env=env,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                               start_new_session=os.name != "nt")
    assert process.stdout is not None and process.stderr is not None and process.stdin is not None
    readers = [threading.Thread(target=capture.read_pipe, args=(pipe,), daemon=True)
               for capture, pipe in ((stdout_capture, process.stdout), (stderr_capture, process.stderr))]
    def write_input():
        try:
            process.stdin.write(stdin_text.encode("utf-8"))
            process.stdin.close()
        except (BrokenPipeError, OSError):
            pass
    writer = threading.Thread(target=write_input, daemon=True)
    for thread in [*readers, writer]:
        thread.start()
    timed_out = False
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, capture_output=True,
                           timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            import signal
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
    for thread in [*readers, writer]:
        thread.join(timeout=2)
    return {"exit_code": process.returncode, "timed_out": timed_out,
            "stdout": stdout_capture.text(), "stderr": stderr_capture.text(),
            "output_truncated": stdout_capture.truncated or stderr_capture.truncated}


@app.post("/api/run")
def run_java(request: RunRequest) -> dict:
    from backend.runner import run
    if request.project_id:
        from backend.workspaces import locked, workspace
        folder = workspace(sys.modules[__name__], request.project_id)
        with locked(request.project_id):
            return run(sys.modules[__name__], request.source, request.stdin, request.timeout_seconds, folder)
    return run(sys.modules[__name__], request.source, request.stdin, request.timeout_seconds)


from backend.learning import install as install_learning

install_learning(app, sys.modules[__name__])
from backend.workspaces import install as install_workspaces

install_workspaces(app, sys.modules[__name__])


@app.get("/api/sources/{filename}")
def source_pdf(filename: str):
    from fastapi.responses import FileResponse
    allowed = {Path(ref["file"]).name for c in get_course()["concepts"] for ref in c.get("source_pdfs", [])}
    allowed.update(Path(f).name for f in get_course().get("source_files", []))
    if filename not in allowed or not filename.lower().endswith(".pdf"):
        raise HTTPException(404, "That source PDF is not part of this course.")
    return FileResponse(ROOT_DIR / "notes" / filename, media_type="application/pdf")


# All API routes are registered before the production static mount.
from fastapi.staticfiles import StaticFiles

if (ROOT_DIR / "frontend" / "dist").is_dir():
    app.mount("/", StaticFiles(directory=ROOT_DIR / "frontend" / "dist", html=True), name="studio")
