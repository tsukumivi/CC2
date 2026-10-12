"""Static corpus integrity contract. Runtime corpus checks live in scripts/verify_course.py."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    return json.loads((ROOT / 'content/course.json').read_text(encoding='utf-8'))


def test_real_source_lines_and_correct_escapes():
    for c in load()['concepts']:
        example = c.get('worked_example', {}).get('code', '')
        if example:
            assert '\n' in example, c['id']
        for task in c.get('tasks', []):
            for key in ('starter_code', 'reference_code'):
                code = task.get(key, '')
                if code:
                    assert '\n' in code, (c['id'], key)
    escapes = next(c for c in load()['concepts'] if c['id'] == 'escape-sequences')
    assert '\\\\t' not in escapes['worked_example']['code']


def test_full_prerequisite_route_and_real_tasks():
    d = load()
    ordered = [cid for m in d['modules'] for cid in m['concept_ids']]
    assert len(ordered) == len(set(ordered)) == len(d['concepts'])
    by_id = {c['id']: c for c in d['concepts']}
    seen = set()
    for module in d['modules']:
        for cid in module['concept_ids']:
            c = by_id[cid]
            assert c['module_id'] == module['id']
            assert 'prerequisites' in c
            assert set(c['prerequisites']) <= seen, cid
            assert all(not by_id[p].get('optional') for p in c['prerequisites'])
            assert len(c['explanation']) >= 2
            assert len(c['outcomes']) >= 2
            assert {t['kind'] for t in c['tasks']} >= {'predict', 'explain'}
            assert any(t.get('required') for t in c['tasks'])
            assert not any(ref.get('basis') == 'syllabus_preview' for ref in c.get('source_pdfs', []))
            seen.add(cid)
    assert {'classes-objects', 'encapsulation', 'file-write', 'file-read', 'capstone-records', 'external-run'} <= seen
    assert len(seen) >= 36
    tasks = [t for c in d['concepts'] for t in c['tasks']]
    assert len({t['id'] for t in tasks}) == len(tasks)
    assert {'predict', 'explain', 'repair', 'modify', 'build'} <= {t['kind'] for t in tasks}
    for t in tasks:
        if t['kind'] in ('build', 'repair', 'modify'):
            assert t['tests'] and t['reference_code']
            assert len(t['tests']) >= 2, t['id']
        assert t['hints']
        assert t.get('answer') or t.get('reference_code')


def test_planning_activities_require_no_java():
    for c in load()['concepts']:
        if c['id'] in ('problem-decomposition', 'flowchart-symbols', 'pseudocode'):
            assert all(t['kind'] in ('predict', 'explain') for t in c['tasks'])


def test_all_legacy_ids_remain_addressable():
    expected = {'problem-decomposition', 'flowchart-symbols', 'pseudocode', 'types-variables', 'java-program-skeleton',
                'identifiers-and-naming', 'output-and-comments', 'read-input', 'arithmetic-integer-division',
                'escape-sequences', 'compound-assignment', 'comparisons-strings', 'if-else-branches', 'validation-methods',
                'logical-operators', 'ternary-operator', 'switch-selection', 'workflow-projects', 'iteration-loops',
                'strings-and-characters', 'arrays-and-search', 'methods-and-parameters', 'arraylist-collections', 'exception-handling'}
    assert expected <= {c['id'] for c in load()['concepts']}
