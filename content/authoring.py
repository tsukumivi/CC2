"""Explicit authoring helpers; lessons live in units/*.py, never an AI grading service."""
from __future__ import annotations

from textwrap import dedent, indent


def J(body: str, imports: str = "", members: str = "") -> str:
    prefix = (imports.strip() + "\n\n") if imports.strip() else ""
    extras = ("\n" + indent(dedent(members).strip(), "    ") + "\n") if members.strip() else ""
    return prefix + "public class Main {\n    public static void main(String[] args)" + (" throws Exception" if "java.nio.file" in imports else "") + " {\n" + indent(dedent(body).strip(), "        ") + "\n    }\n" + extras + "}\n"


def T(name, stdin, output, **extra):
    return {"name": name, "stdin": stdin, "expected_stdout": output, **extra}


def E(code, output, walkthrough, stdin="", **extra):
    return {"code": code, "stdin": stdin, "expected_stdout": output, "walkthrough": walkthrough, **extra}


def Q(prompt, code, answer, explanation):
    return {"prompt": prompt, "code": code, "answer": answer, "explanation": explanation}


def R(prompt, answer, rubric):
    return {"prompt": prompt, "answer": answer, "rubric": rubric}


def P(prompt, reference, tests, starter=None, hints=None, rubric=None, kind="build", **extra):
    return {"kind": kind, "prompt": prompt, "reference_code": reference,
            "starter_code": starter if starter is not None else J("// Write your solution here."),
            "starter_input": tests[0].get("stdin", ""), "tests": tests,
            "hints": hints or ["List the required outputs for each case before writing code.", "Compare one failing case with your variable values, then change one cause."],
            "rubric": rubric or ["I implemented the stated rules, rather than hardcoding the sample outputs.", "I can explain the normal and boundary cases in my own code."],
            "explanation": "Compare the reference with your implementation only after attempting the task. " + prompt,
            **extra}


def L(cid, title, summary, teach, outcomes, example, prediction, reflection, practice=None, diagram=None, extra_practice=None, optional=False):
    explain = {"id": cid + "-explain", "kind": "explain", "required": True,
               **reflection, "hints": [reflection["rubric"][0]], "explanation": reflection["answer"]}
    predict = {"id": cid + "-predict", "kind": "predict", "required": True,
               **prediction, "accepted_answers": [prediction["answer"]], "rubric": [],
               "hints": ["Trace one operation at a time. Record the state before the next operation."]}
    tasks = [explain, predict]
    for index, activity in enumerate([p for p in (extra_practice, practice) if p]):
        tasks.append({"id": cid + "-" + activity["kind"], "required": activity is practice, **activity})
    return {"id": cid, "title": title, "summary": summary, "explanation": teach,
            "outcomes": outcomes, "worked_example": example, "tasks": tasks,
            "optional": optional, "visual": diagram or {"kind": "sequence", "nodes": outcomes, "edges": [[i, i + 1] for i in range(len(outcomes) - 1)]}}
