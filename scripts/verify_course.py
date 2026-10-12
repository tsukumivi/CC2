"""Executable corpus audit: compile all sources; run examples/references and restart cases.

Run from project root: .venv/Scripts/python.exe scripts/verify_course.py
No sample result is synthesized: the report contains actual JVM output.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend import main
from backend.runner import normalized, safe_file


def verify():
    started = time.perf_counter()
    course = main.get_course()
    tools = main.java_toolchain()
    assert tools['jdk_available'], tools['setup_message']
    sources, broken, references, examples = {}, [], [], []
    for concept in course['concepts']:
        example = concept['worked_example']
        if example.get('code'):
            sources.setdefault(example['code'], len(sources))
            examples.append((concept['id'], example))
        for task in concept['tasks']:
            if task.get('code'):
                sources.setdefault(task['code'], len(sources))
            if task.get('reference_code'):
                sources.setdefault(task['reference_code'], len(sources))
                references.append((task['id'], task))
            if task.get('starter_code'):
                if task.get('starter_expected_status') == 'compile_error':
                    broken.append(task)
                else:
                    sources.setdefault(task['starter_code'], len(sources))
    reports = []
    base = main.DATA_DIR / 'runner'
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='corpus-', dir=base) as folder_name:
        folder = Path(folder_name)
        classes = folder / 'classes'
        classes.mkdir()
        paths = []
        for source, index in sources.items():
            path = folder / 'sources' / f's{index:03}' / 'Main.java'
            path.parent.mkdir(parents=True)
            path.write_text(f'package audit.s{index:03};\n' + source, encoding='utf-8')
            paths.append(path)
        args = folder / 'sources.txt'
        args.write_text('\n'.join('"' + str(p).replace('\\', '/') + '"' for p in paths), encoding='utf-8')
        result = main.run_bounded([tools['javac_path'], '-J-Xmx256m', '-J-XX:+UseSerialGC', '--release', '21', '-encoding', 'UTF-8', '-proc:none', '-d', str(classes), '@' + str(args)], folder, '', 60)
        if result['exit_code'] != 0:
            print(result['stderr'])
            raise AssertionError('Corpus batch compilation failed.')
        def run_source(source, stdin, workspace):
            index = sources[source]
            return main.run_bounded([tools['java_path'], '-Xmx128m', '-XX:+UseSerialGC', '-Dfile.encoding=UTF-8', '-cp', str(classes), f'audit.s{index:03}.Main'], workspace, stdin, 4)
        def run_case(label, source, test):
            workspace = folder / 'cases' / str(len(reports))
            workspace.mkdir(parents=True)
            for name, value in test.get('files', {}).items():
                safe_file(workspace, name).write_text(value, encoding='utf-8')
            steps = test.get('runs', [test])
            for step_index, step in enumerate(steps):
                actual = run_source(source, step.get('stdin', ''), workspace)
                expected = step.get('expected_stdout', '')
                passed = actual['exit_code'] == 0 and not actual['timed_out'] and not actual['output_truncated'] and normalized(actual['stdout']) == normalized(expected)
                file_checks = []
                for name, value in step.get('expected_files', {}).items():
                    path = safe_file(workspace, name)
                    got = path.read_text(encoding='utf-8') if path.is_file() else None
                    good = got is not None and normalized(got) == normalized(value)
                    passed &= good
                    file_checks.append({'name':name, 'passed':good, 'actual':got, 'expected':value})
                report = {'id':label, 'case':test.get('name','worked example'), 'step':step_index + 1,
                          'passed':bool(passed), 'actual_stdout':actual['stdout'], 'expected_stdout':expected,
                          'stderr':actual['stderr'], 'exit_code':actual['exit_code'], 'files':file_checks}
                reports.append(report)
                if len(reports) % 20 == 0:
                    print(f'Executed {len(reports)} reference/example checks.', flush=True)
                if not passed:
                    print(json.dumps(report, ensure_ascii=False))
        for cid, example in examples:
            run_case(cid + '-example', example['code'], example)
        for tid, task in references:
            for test in task['tests']:
                run_case(tid, task['reference_code'], test)
        for task in broken:
            # Intentional syntax repairs must fail compilation before the learner fixes them.
            from backend.runner import run
            actual = run(main, task['starter_code'])
            reports.append({'id':task['id']+'-intentional-broken-starter', 'passed':actual['status']=='compile_error', 'status':actual['status']})
        # Execute every starter case with fresh fixtures and real restart steps.
        # An incomplete starter may fail checks; its audit passes only if it does
        # NOT already satisfy every declared requirement.
        for tid, task in references:
            if task.get('starter_expected_status') == 'compile_error':
                continue
            evidence = []
            for case_index, test in enumerate(task['tests']):
                workspace = folder / 'starter-cases' / tid / str(case_index)
                workspace.mkdir(parents=True)
                for name, value in test.get('files', {}).items():
                    safe_file(workspace, name).write_text(value, encoding='utf-8')
                for step in test.get('runs', [test]):
                    actual = run_source(task['starter_code'], step.get('stdin', ''), workspace)
                    matches = actual['exit_code'] == 0 and not actual['timed_out'] and not actual['output_truncated'] and normalized(actual['stdout']) == normalized(step.get('expected_stdout', ''))
                    files = []
                    for name, wanted in step.get('expected_files', {}).items():
                        path = safe_file(workspace, name)
                        got = path.read_text(encoding='utf-8') if path.is_file() else None
                        good = got is not None and normalized(got) == normalized(wanted)
                        matches &= good
                        files.append({'name': name, 'actual': got, 'expected': wanted, 'matches': good})
                    evidence.append({'case': test['name'], 'matches_requirement': bool(matches), 'exit_code': actual['exit_code'], 'stdout': actual['stdout'], 'stderr': actual['stderr'], 'files': files})
            reports.append({'id':tid+'-starter-incomplete', 'passed':bool(evidence) and not all(e['matches_requirement'] for e in evidence), 'evidence':evidence})
    result = {'compiler':tools['compiler_version'], 'modules':len(course['modules']), 'concepts':len(course['concepts']),
              'tasks':sum(len(c['tasks']) for c in course['concepts']), 'unique_compilable_sources':len(sources),
              'references':len(references), 'examples':len(examples), 'executed_checks':len(reports),
              'passed':all(r['passed'] for r in reports), 'duration_seconds':round(time.perf_counter()-started,2), 'results':reports}
    target = ROOT / 'artifacts/corpus-verification.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='results'}, ensure_ascii=False))
    assert result['passed'], 'Some executable corpus checks failed. See artifacts/corpus-verification.json.'


if __name__ == '__main__':
    verify()
