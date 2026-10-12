"""Contract tests use real HTTP requests and SQLite; no Java result stubs."""
import json

import pytest
from fastapi.testclient import TestClient

from backend import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DATABASE_PATH", tmp_path / "learning.db")
    corpus = {
        "id": "test-course", "version": 2,
        "modules": [{"id": "first", "concept_ids": ["first", "second"]}],
        "concepts": [
            {"id": "first", "module_id": "first", "prerequisites": [], "tasks": [
                {"id": "first-predict", "kind": "predict", "required": True,
                 "prompt": "Predict 2 + 3", "answer": "5", "accepted_answers": ["5"],
                 "explanation": "Add the two values.", "rubric": [], "hints": ["Add, do not concatenate."]},
                {"id": "first-explain", "kind": "explain", "required": True,
                 "prompt": "Explain the addition.", "answer": "Two values produce one sum.",
                 "rubric": ["Name both inputs.", "Describe adding them."], "hints": []},
            ]},
            {"id": "second", "module_id": "first", "prerequisites": ["first"], "tasks": [
                {"id": "second-build", "kind": "build", "required": True,
                 "prompt": "Print 5", "starter_code": "public class Main { public static void main(String[] a) {} }",
                 "reference_code": "public class Main { public static void main(String[] a) {System.out.println(5);} }",
                 "tests": [{"name": "sum", "stdin": "", "expected_stdout": "5\n"}],
                 "rubric": [], "hints": []},
            ]},
        ],
    }
    p = tmp_path / "course.json"
    p.write_text(json.dumps(corpus), encoding="utf-8")
    monkeypatch.setattr(main, "COURSE_PATH", p)
    with TestClient(main.app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 50000)) as c:
        yield c


def test_prediction_is_server_checked_and_saved(client):
    bad = client.post("/api/tasks/first-predict/submit", json={"response": "9"})
    assert bad.status_code == 200, bad.text
    assert bad.json()["passed"] is False
    good = client.post("/api/tasks/first-predict/submit", json={"response": "5"})
    assert good.json()["passed"] is True
    history = client.get("/api/tasks/first-predict/history").json()["attempts"]
    assert [a["response"] for a in history] == ["5", "9"]
    assert client.get("/api/learning").json()["completed_concept_ids"] == []


def test_core_completion_requires_explanation_and_unassisted_work(client):
    client.post("/api/tasks/first-predict/submit", json={"response": "5", "assisted": True})
    missing = client.post("/api/tasks/first-explain/submit", json={"response": "addition", "rubric_checks": [True]})
    assert missing.status_code == 422
    client.post("/api/tasks/first-explain/submit", json={"response": "two inputs added", "rubric_checks": [True, True]})
    assert client.get("/api/learning").json()["next_concept_id"] == "first"
    client.post("/api/tasks/first-predict/submit", json={"response": "5"})
    state = client.get("/api/learning").json()
    assert state["completed_concept_ids"] == ["first"]
    assert state["next_concept_id"] == "second"
    assert state["task_progress"]["first-explain"]["assessment"] == "self_check"


def test_draft_survives_client_reload(client):
    payload = {"response": "unfinished", "code": "// keep my code", "stdin": "Ada\n", "assisted": True, "rubric_checks": [False, True]}
    assert client.put("/api/tasks/first-explain/draft", json=payload).status_code == 200
    draft = client.get("/api/tasks/first-explain/draft").json()
    assert all(draft[k] == v for k, v in payload.items())


def test_unknown_ids_are_rejected(client):
    assert client.post("/api/tasks/not-a-task/submit", json={"response": "5"}).status_code == 404
    assert client.put("/api/tasks/not-a-task/draft", json={"response": "x"}).status_code == 404


def test_client_score_cannot_establish_mastery(client):
    response = client.post("/api/progress", json={"concept_id": "first", "activity_type": "build", "score": 1})
    assert response.status_code in (409, 422)


def test_foreign_origin_and_rebinding_host_are_blocked(client):
    assert client.post("/api/run", headers={"Origin": "https://evil.example"}, json={"source": "bad"}).status_code == 403
    assert client.get("/api/course", headers={"Host": "evil.example"}).status_code in (400, 403)


def test_no_reference_answers_on_public_course(client):
    public = client.get("/api/course").json()
    task = public["concepts"][0]["tasks"][0]
    assert "answer" not in task
    assert "accepted_answers" not in task
    assert "reference_code" not in public["concepts"][1]["tasks"][0]
    reference = client.get("/api/tasks/first-predict/reference").json()
    assert reference["answer"] == "5"
    assert client.get("/api/tasks/first-predict/draft").json()["assisted"] is True
