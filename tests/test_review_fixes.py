"""Regression reproductions for the two independent-review findings."""
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from uuid import uuid4

import pytest

from backend import main


@pytest.mark.parametrize('task_id,payload', [
    ('first-predict', {'response': 'wrong'}),
    ('first-explain', {'response': 'incomplete', 'rubric_checks': [False, False]}),
])
def test_failed_feedback_does_not_reveal_reference_answer(client, task_id, payload):
    request_id = str(uuid4())
    payload = {**payload, 'request_id': request_id}
    result = client.post(f'/api/tasks/{task_id}/submit', json=payload)
    assert result.status_code == 200, result.text
    assert result.json()['passed'] is False
    assert 'answer' not in result.json()
    assert 'explanation' not in result.json()
    replay = client.post(f'/api/tasks/{task_id}/submit', json=payload)
    assert replay.json() == result.json()
    history = client.get(f'/api/tasks/{task_id}/history').json()['attempts']
    assert all('answer' not in item and 'explanation' not in item for item in history)
    reference = client.get(f'/api/tasks/{task_id}/reference')
    assert reference.status_code == 200 and reference.json()['answer']
    assert client.get(f'/api/tasks/{task_id}/draft').json()['assisted'] is True


def test_legacy_feedback_cannot_reveal_answer_through_history_or_replay(client):
    payload = {'response': 'wrong', 'request_id': str(uuid4())}
    result = client.post('/api/tasks/first-predict/submit', json=payload).json()
    legacy = {**result, 'answer': '5', 'explanation': 'Add the two values.'}
    with main.connect_db() as db:
        db.execute('UPDATE task_attempts SET result_json=? WHERE id=?',
                   (json.dumps(legacy), payload['request_id']))
    replay = client.post('/api/tasks/first-predict/submit', json=payload).json()
    assert 'answer' not in replay and 'explanation' not in replay
    history = client.get('/api/tasks/first-predict/history').json()['attempts']
    assert 'answer' not in history[0] and 'explanation' not in history[0]


def test_late_autosave_cannot_recreate_cleared_draft(client):
    path = '/api/tasks/first-predict'
    old = client.get(path + '/draft').json()
    old.update(response='old assisted answer', assisted=True)
    entered, release = Event(), Event()

    def delayed_save():
        entered.set()
        assert release.wait(5)
        return client.put(path + '/draft', json=old)

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(delayed_save)
        assert entered.wait(5)
        fresh = client.post(path + '/retry').json()
        release.set()
        result = pending.result(timeout=5)
    assert result.status_code == 409, result.text
    assert client.get(path + '/draft').json() == fresh
    assert fresh['assisted'] is False and fresh['response'] == ''
    fresh.update(response='5')
    assert client.put(path + '/draft', json=fresh).status_code == 200
    assessed = client.post(path + '/submit', json=fresh)
    assert assessed.status_code == 200 and assessed.json()['assisted'] is False


def test_simultaneous_save_and_retry_leave_fresh_draft(client):
    path = '/api/tasks/first-predict'
    for _ in range(8):
        old = client.get(path + '/draft').json()
        old.update(response='stale', assisted=True)
        barrier = Barrier(2)

        def save(barrier=barrier, old=old):
            barrier.wait(timeout=5)
            return client.put(path + '/draft', json=old)

        def retry(barrier=barrier):
            barrier.wait(timeout=5)
            return client.post(path + '/retry')

        with ThreadPoolExecutor(max_workers=2) as pool:
            saving, resetting = pool.submit(save), pool.submit(retry)
            saved, reset = saving.result(timeout=10), resetting.result(timeout=10)
        assert saved.status_code in (200, 409)
        assert reset.status_code == 200
        assert client.get(path + '/draft').json() == reset.json()
        assert reset.json()['response'] == '' and not reset.json()['assisted']


def test_retry_generation_is_durable_and_rejects_stale_submissions(client):
    path = '/api/tasks/first-predict'
    before = client.get(path + '/draft').json()
    fresh = client.post(path + '/retry').json()
    assert fresh.get('generation') == before.get('generation', 0) + 1
    assert client.get(path + '/draft').json()['generation'] == fresh['generation']
    old = {**before, 'response': '5'}
    assert client.post(path + '/submit', json=old).status_code == 409
    fresh.update(response='5')
    result = client.post(path + '/submit', json=fresh)
    assert result.status_code == 200 and result.json()['passed'] is True


def test_assistance_cannot_be_cleared_by_same_generation_autosave(client):
    path = '/api/tasks/first-predict'
    stale = client.get(path + '/draft').json()
    client.get(path + '/reference')
    saved = client.put(path + '/draft', json={**stale, 'response': '5'}).json()
    assert saved['assisted'] is True
    result = client.post(path + '/submit', json={**stale, 'response': '5'}).json()
    assert result['passed'] is True and result['assisted'] is True
