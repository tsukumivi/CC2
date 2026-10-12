"""Durable task assessment. The client never supplies a mastery score."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import timedelta

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field


class Submission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response: str = Field(default="", max_length=12_000)
    code: str = Field(default="", max_length=48_000)
    stdin: str = Field(default="", max_length=8_000)
    assisted: bool = False
    generation: int = Field(default=0, ge=0)
    rubric_checks: list[bool] = Field(default_factory=list, max_length=20)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), max_length=64)


def initialize(repo):
    with repo.connect_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS task_attempts (
                id TEXT PRIMARY KEY, task_id TEXT NOT NULL, concept_id TEXT NOT NULL,
                response TEXT NOT NULL, code TEXT NOT NULL, stdin TEXT NOT NULL,
                passed INTEGER NOT NULL, assisted INTEGER NOT NULL,
                assessment TEXT NOT NULL, result_json TEXT NOT NULL,
                created_at TEXT NOT NULL, next_review_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_task_attempts ON task_attempts(task_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS task_drafts (
                task_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS task_draft_generations (
                task_id TEXT PRIMARY KEY, generation INTEGER NOT NULL
            );
        """)
        if "request_hash" not in {r["name"] for r in db.execute("PRAGMA table_info(task_attempts)")} :
            db.execute("ALTER TABLE task_attempts ADD COLUMN request_hash TEXT NOT NULL DEFAULT ''")


def find_task(repo, task_id):
    for concept in repo.get_course().get("concepts", []):
        for task in concept.get("tasks", []):
            if task["id"] == task_id:
                return concept, task
    raise HTTPException(404, "That task does not exist in this course.")


def state(repo):
    course = repo.get_course()
    with repo.connect_db() as db:
        rows = db.execute("SELECT * FROM task_attempts ORDER BY created_at, rowid").fetchall()
    progress = {}
    for row in rows:
        item = progress.setdefault(row["task_id"], {"attempts": 0, "passed": False, "independent_passed": False})
        item.update(last_passed=bool(row["passed"]), assisted=bool(row["assisted"]),
                    assessment=row["assessment"], last_attempt_at=row["created_at"], next_review_at=row["next_review_at"])
        item["attempts"] += 1
        item["passed"] |= bool(row["passed"])
        item["independent_passed"] |= bool(row["passed"] and not row["assisted"])
    completed = []
    for concept in course.get("concepts", []):
        required = [t for t in concept.get("tasks", []) if t.get("required", True)]
        if required and all(progress.get(t["id"], {}).get("independent_passed", False) for t in required):
            completed.append(concept["id"])
    next_id = next((c["id"] for c in course.get("concepts", [])
                    if not c.get("optional") and c["id"] not in completed), None)
    now = repo.iso_time()
    active_ids = {t["id"] for c in course.get("concepts", []) for t in c.get("tasks", [])}
    weak = [task_id for task_id, p in progress.items() if task_id in active_ids and not p["last_passed"]]
    due = [task_id for task_id, p in progress.items()
           if task_id in active_ids and p["next_review_at"] <= now]
    return {"task_progress": progress, "completed_concept_ids": completed,
            "next_concept_id": next_id, "weak_task_ids": weak, "due_task_ids": due,
            "course_version": course.get("version", 2)}


def draft_payload(db, task_id):
    row = db.execute("SELECT payload FROM task_drafts WHERE task_id=?", (task_id,)).fetchone()
    epoch = db.execute("SELECT generation FROM task_draft_generations WHERE task_id=?", (task_id,)).fetchone()
    payload = json.loads(row["payload"]) if row else {"response": "", "code": "", "stdin": "", "assisted": False, "rubric_checks": []}
    return {**payload, "generation": epoch["generation"] if epoch else 0}


def require_generation(db, task_id, generation):
    epoch = db.execute("SELECT generation FROM task_draft_generations WHERE task_id=?", (task_id,)).fetchone()
    if generation != (epoch["generation"] if epoch else 0):
        raise HTTPException(409, "A fresh attempt replaced this draft. Reload before editing or submitting it.")


def assessment_feedback(result):
    """References belong only to the explicit, assistance-marking reveal flow."""
    return {key: value for key, value in result.items() if key not in ("answer", "explanation")}


def record(repo, concept, task, submission, result):
    assessment = "self_check" if task["kind"] == "explain" else "tests" if task["kind"] in ("repair", "modify", "build") else "exact"
    now = repo.utc_now()
    passed = bool(result["passed"])
    next_review = now + timedelta(days=0 if not passed else 1 if submission.assisted else 3)
    output = {**result, "task_id": task["id"], "attempt_id": submission.request_id,
              "assisted": submission.assisted, "assessment": assessment,
              "created_at": repo.iso_time(now), "next_review_at": repo.iso_time(next_review)}
    with repo.connect_db() as db:
        db.execute("BEGIN IMMEDIATE")
        old = db.execute("SELECT result_json,request_hash FROM task_attempts WHERE id=?", (submission.request_id,)).fetchone()
        if old:
            if old["request_hash"] != submission._request_hash:
                raise HTTPException(409, "That request ID already belongs to a different submission.")
            return assessment_feedback(json.loads(old["result_json"]))
        require_generation(db, task["id"], submission.generation)
        try:
            db.execute("""INSERT INTO task_attempts
                       (id,task_id,concept_id,response,code,stdin,passed,assisted,assessment,result_json,created_at,next_review_at,request_hash)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                       (submission.request_id, task["id"], concept["id"], submission.response,
                        submission.code, submission.stdin, int(passed), int(submission.assisted),
                        assessment, json.dumps(output), output["created_at"], output["next_review_at"], submission._request_hash))
        except sqlite3.IntegrityError:
            old = db.execute("SELECT result_json,request_hash FROM task_attempts WHERE id=?", (submission.request_id,)).fetchone()
            if not old or old["request_hash"] != submission._request_hash:
                raise HTTPException(409, "That request ID already belongs to a different submission.")
            return assessment_feedback(json.loads(old["result_json"]))
    return output


def install(app, repo):
    @app.post("/api/tasks/{task_id}/submit")
    def submit(task_id: str, submission: Submission):
        concept, task = find_task(repo, task_id)
        payload = submission.model_dump(exclude={"request_id"})
        if submission.generation == 0:
            payload.pop("generation")  # Preserve idempotent replay hashes from pre-generation records.
        payload_hash = hashlib.sha256(json.dumps([task_id, payload], sort_keys=True).encode()).hexdigest()
        with repo.connect_db() as db:
            db.execute("BEGIN")
            old = db.execute("SELECT result_json,request_hash FROM task_attempts WHERE id=?", (submission.request_id,)).fetchone()
            if not old:
                require_generation(db, task_id, submission.generation)
            draft = draft_payload(db, task_id)
        if old:
            if old["request_hash"] != payload_hash:
                raise HTTPException(409, "That request ID already belongs to a different submission.")
            return assessment_feedback(json.loads(old["result_json"]))
        submission._request_hash = payload_hash
        if draft["assisted"]:
            submission.assisted = True
        if task["kind"] == "explain":
            if len(submission.rubric_checks) != len(task["rubric"]) or not submission.response.strip():
                raise HTTPException(422, "Write your explanation and assess every rubric criterion.")
            passed = all(submission.rubric_checks)
            result = {"passed": passed, "feedback": "Self-check recorded, not machine-graded." if passed else "Revise the unchecked criteria and retry.",
                      "cases": []}
        elif task["kind"] == "predict":
            answer = submission.response.strip().replace("\r\n", "\n")
            choices = task.get("accepted_answers", [task["answer"]])
            passed = answer in [a.strip().replace("\r\n", "\n") for a in choices]
            result = {"passed": passed, "feedback": "Correct." if passed else "Not yet. Revise your trace, or reveal the reference for assisted practice.",
                      "cases": []}
        else:
            from backend.runner import grade
            if task.get("rubric") and len(submission.rubric_checks) != len(task["rubric"]):
                raise HTTPException(422, "Assess every design criterion before submitting your program.")
            result = grade(repo, task, submission.code)
            if task.get("rubric") and not all(submission.rubric_checks):
                result["passed"] = False
                result["feedback"] += " Design self-check is not complete."
        return record(repo, concept, task, submission, result)

    @app.get("/api/tasks/{task_id}/draft")
    def get_draft(task_id: str):
        find_task(repo, task_id)
        with repo.connect_db() as db:
            db.execute("BEGIN")
            return draft_payload(db, task_id)

    @app.put("/api/tasks/{task_id}/draft")
    def save_draft(task_id: str, draft: Submission):
        find_task(repo, task_id)
        payload = draft.model_dump(exclude={"request_id"})
        with repo.connect_db() as db:
            db.execute("BEGIN IMMEDIATE")
            require_generation(db, task_id, draft.generation)
            payload["assisted"] = payload["assisted"] or draft_payload(db, task_id)["assisted"]
            db.execute("INSERT INTO task_drafts VALUES (?,?,?) ON CONFLICT(task_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
                       (task_id, json.dumps(payload), repo.iso_time()))
        return payload

    @app.post("/api/tasks/{task_id}/retry")
    def retry(task_id: str):
        find_task(repo, task_id)
        with repo.connect_db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO task_draft_generations VALUES (?,1) ON CONFLICT(task_id) DO UPDATE SET generation=generation+1", (task_id,))
            db.execute("DELETE FROM task_drafts WHERE task_id=?", (task_id,))
            fresh = draft_payload(db, task_id)
        return fresh

    @app.post("/api/tasks/{task_id}/hint/{index}")
    def hint(task_id: str, index: int):
        _, task = find_task(repo, task_id)
        if index < 0 or index >= len(task.get("hints", [])):
            raise HTTPException(404, "That hint does not exist.")
        draft = Submission(**get_draft(task_id))
        draft.assisted = True
        save_draft(task_id, draft)
        return {"hint": task["hints"][index]}

    @app.get("/api/tasks/{task_id}/reference")
    def reference(task_id: str):
        _, task = find_task(repo, task_id)
        draft = Submission(**get_draft(task_id))
        draft.assisted = True
        save_draft(task_id, draft)
        return {"answer": task.get("answer", ""), "code": task.get("reference_code", ""),
                "explanation": task.get("explanation", ""), "walkthrough": task.get("walkthrough", [])}

    @app.get("/api/tasks/{task_id}/history")
    def history(task_id: str):
        find_task(repo, task_id)
        with repo.connect_db() as db:
            rows = db.execute("SELECT * FROM task_attempts WHERE task_id=? ORDER BY created_at DESC, rowid DESC LIMIT 50", (task_id,)).fetchall()
        return {"attempts": [{**assessment_feedback(json.loads(r["result_json"])), "response": r["response"], "code": r["code"], "stdin": r["stdin"]} for r in rows]}

    @app.get("/api/learning")
    def learning_state():
        return state(repo)
