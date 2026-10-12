import json
from pathlib import Path

COURSE=Path(__file__).resolve().parents[1]/'content/course.json'


def test_each_stage_has_a_distinct_optional_transfer_program():
    course=json.loads(COURSE.read_text(encoding='utf-8'))
    for module in course['modules']:
        tasks=[t for c in course['concepts'] if c['module_id']==module['id'] for t in c['tasks'] if t.get('transfer')]
        assert tasks, 'No novel transfer program in '+module['id']
        assert all(not t['required'] and t['tests'] and t['reference_code']!=t['starter_code'] for t in tasks)


def test_capstone_lesson_does_not_display_the_full_reference_as_a_worked_example():
    course=json.loads(COURSE.read_text(encoding='utf-8'))
    capstone=next(c for c in course['concepts'] if c['id']=='capstone-records')
    reference=next(t['reference_code'] for t in capstone['tasks'] if t['kind']=='build')
    assert capstone['worked_example'].get('code','')!=reference
