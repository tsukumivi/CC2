from datetime import datetime

import pytest


def test_assisted_failure_is_due_immediately(client):
    client.get('/api/tasks/first-predict/reference')
    result = client.post('/api/tasks/first-predict/submit',json={'response':'wrong'}).json()
    assert result['passed'] is False and result['assisted'] is True
    assert datetime.fromisoformat(result['next_review_at'])<=datetime.fromisoformat(result['created_at'])
    assert 'first-predict' in client.get('/api/learning').json()['due_task_ids']


@pytest.mark.parametrize('name',['CON.txt','nul.log','COM1.txt','record.'])
def test_invalid_platform_filename_is_rejected_before_io(client,name):
    p=client.post('/api/projects',json={'title':'Filename test','code':'public class Main {}'}).json()['project']
    response=client.put(f"/api/projects/{p['id']}/files/{name}",json={'content':'data'})
    assert response.status_code==422,response.text


def test_malformed_origin_is_rejected_not_an_internal_error(client):
    response=client.get('/api/course',headers={'origin':'http://[invalid'})
    assert response.status_code==403


@pytest.mark.parametrize('host',['[2001:db8::1]:8000','[::1]evil:8000','127.0.0.1:bad'])
def test_host_parser_rejects_non_loopback_and_malformed_hosts(client,host):
    assert client.get('/api/course',headers={'host':host}).status_code==403


def test_current_capstone_uses_the_real_assessment_contract(client,monkeypatch):
    import json
    from pathlib import Path

    from backend import main

    course=json.loads((Path(__file__).resolve().parents[1]/'content/course.json').read_text(encoding='utf-8'))
    monkeypatch.setattr(main,'get_course',lambda:course)
    task=next(t for c in course['concepts'] for t in c['tasks'] if t['id']=='capstone-records-build')
    result=client.post('/api/tasks/'+task['id']+'/submit',json={'code':task['reference_code'],'rubric_checks':[True]*len(task['rubric'])})
    assert result.status_code==200,result.text
    evidence=result.json()
    assert evidence['passed'],evidence
    assert all(case['passed'] for case in evidence['cases'])
    assert any('run 2' in case['name'] for case in evidence['cases'])
