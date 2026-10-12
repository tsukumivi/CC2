"""Compile once, run transparent cases in isolated fresh workspaces.

Isolation preserves test reproducibility. It is not a Java security sandbox.
"""
from __future__ import annotations

import re
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from fastapi import HTTPException

CAPACITY = threading.BoundedSemaphore(2)


@contextmanager
def slot():
    if not CAPACITY.acquire(blocking=False):
        raise HTTPException(429, "Two Java jobs are already running. Wait for one to finish, then retry.")
    try:
        yield
    finally:
        CAPACITY.release()


def check_bytes(source, stdin=""):
    if len(source.encode("utf-8")) > 48_000 or len(stdin.encode("utf-8")) > 8_000:
        raise HTTPException(413, "Source must be at most 48 KB and input at most 8 KB of UTF-8 bytes.")


def safe_file(root: Path, name: str) -> Path:
    reserved = re.match(r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)", name, re.IGNORECASE)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", name) or reserved or name.endswith('.') or name.lower() == "main.java" or name.lower().endswith(".class"):
        raise HTTPException(422, "Use a simple data filename, without folders, traversal, or executable files.")
    target = root / name
    if target.is_symlink() or target.resolve().parent != root.resolve():
        raise HTTPException(422, "Data file must stay inside its workspace.")
    return target


def compile_code(repo, source, folder):
    tools = repo.java_toolchain()
    if not tools["jdk_available"]:
        return {"status": "unavailable", "stdout": "", "stderr": tools["setup_message"],
                "exit_code": None, "compile_success": False, "jdk_available": False}
    check_bytes(source)
    source_file = folder / "Main.java"
    source_file.write_text(source, encoding="utf-8")
    classes = folder / "classes"
    classes.mkdir()
    result = repo.run_bounded([tools["javac_path"], "-J-Xmx256m", "-J-XX:+UseSerialGC", "--release", "21", "-encoding", "UTF-8", "-proc:none", "-d", str(classes), str(source_file)], folder, "", 20)
    status = "compile_timeout" if result["timed_out"] else "compile_error" if result["exit_code"] else "compiled"
    return {**result, "status": status, "compile_success": status == "compiled", "jdk_available": True,
            "classes": str(classes), "java_path": tools["java_path"]}


def execute(repo, compiled, folder, stdin, timeout=4):
    check_bytes("", stdin)
    result = repo.run_bounded([compiled["java_path"], "-Xmx128m", "-XX:+UseSerialGC", "-Dfile.encoding=UTF-8", "-cp", compiled["classes"], "Main"], folder, stdin, timeout)
    status = "runtime_timeout" if result["timed_out"] else "runtime_error" if result["exit_code"] else "completed"
    if result["timed_out"] and not result["stderr"]:
        result["stderr"] = f"Program exceeded {timeout:g} seconds. Check loop exit conditions or missing input."
    return {**result, "status": status, "compile_success": True, "jdk_available": True}


def temporary(repo):
    root = repo.DATA_DIR / "runner"
    root.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="job-", dir=root)


def run(repo, source, stdin="", timeout: float = 4.0, workspace=None):
    check_bytes(source, stdin)
    started = time.perf_counter()
    with slot(), temporary(repo) as folder:
        compiled = compile_code(repo, source, Path(folder))
        result = execute(repo, compiled, workspace or Path(folder), stdin, timeout) if compiled["compile_success"] else compiled
    return {k: v for k, v in {**result, "duration_ms": int((time.perf_counter() - started) * 1000)}.items()
            if k not in ("classes", "java_path")}


def normalized(text):
    # Normalize platform line endings and one terminal newline only. Whitespace inside
    # output is significant; a sloppy answer must not pass by deleting all spaces.
    return text.replace("\r\n", "\n").removesuffix("\n")


def grade(repo, task, source):
    if not source.strip():
        raise HTTPException(422, "Write or load your Java code before running the task checks.")
    cases = []
    with slot(), temporary(repo) as temporary_folder:
        folder = Path(temporary_folder)
        compiled = compile_code(repo, source, folder)
        if not compiled["compile_success"]:
            return {"passed": False, "feedback": "Compilation did not succeed. Read the compiler message and repair the first reported error.",
                    "cases": [], "run": {k: v for k, v in compiled.items() if k not in ("classes", "java_path")}}
        for index, test in enumerate(task.get("tests", [])):
            workspace = folder / f"case-{index}"
            workspace.mkdir()
            for name, content in test.get("files", {}).items():
                safe_file(workspace, name).write_text(content, encoding="utf-8")
            steps = test.get("runs", [test])
            for step_index, step in enumerate(steps):
                result = execute(repo, compiled, workspace, step.get("stdin", ""), step.get("timeout_seconds", 4))
                expected = step.get("expected_stdout", "")
                passed = result["status"] == "completed" and not result.get("output_truncated", False) and normalized(result["stdout"]) == normalized(expected)
                file_checks = []
                for name, wanted in step.get("expected_files", {}).items():
                    path = safe_file(workspace, name)
                    actual = None
                    if path.is_file() and path.stat().st_size <= 64_000:
                        try:
                            actual = path.read_text(encoding="utf-8")
                        except (OSError, UnicodeDecodeError):
                            pass
                    matches = actual is not None and normalized(actual) == normalized(wanted)
                    passed &= matches
                    file_checks.append({"name": name, "passed": matches, "expected": wanted, "actual": actual})
                cases.append({"name": test["name"] + (f" / run {step_index + 1}" if len(steps) > 1 else ""),
                              "passed": bool(passed), "status": result["status"], "stdin": step.get("stdin", ""),
                              "expected_stdout": expected, "actual_stdout": result["stdout"],
                              "stderr": result["stderr"], "exit_code": result["exit_code"], "files": file_checks})
                if result["status"] != "completed":
                    # Later restart steps cannot give evidence if a prerequisite run failed.
                    for remaining in range(step_index + 1, len(steps)):
                        cases.append({"name": test["name"] + f" / run {remaining + 1}", "passed": False, "status": "skipped",
                                      "stdin": steps[remaining].get("stdin", ""), "expected_stdout": steps[remaining].get("expected_stdout", ""),
                                      "actual_stdout": "", "stderr": "Earlier run failed; this restart step was not executed.", "exit_code": None, "files": []})
                    break
    passed = bool(cases) and all(case["passed"] for case in cases)
    return {"passed": passed, "cases": cases,
            "feedback": "All declared checks passed. This is evidence for these cases, not proof for all possible inputs." if passed else "Some checks failed. Compare actual and expected output, repair one cause, and rerun."}
