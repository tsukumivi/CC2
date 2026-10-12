

def test_compiling_wrong_answer_does_not_pass(client):
    bad = 'public class Main {public static void main(String[] a){System.out.println(9);}}'
    response = client.post('/api/tasks/second-build/submit', json={'code': bad})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['passed'] is False
    assert result['cases'][0]['actual_stdout'].strip() == '9'
    assert result['cases'][0]['expected_stdout'].strip() == '5'
    good = 'public class Main {public static void main(String[] a){System.out.println(5);}}'
    result = client.post('/api/tasks/second-build/submit', json={'code': good}).json()
    assert result['passed'] is True
    assert result['cases'][0]['status'] == 'completed'


def test_reference_assistance_cannot_be_hidden_by_client(client):
    client.get('/api/tasks/first-predict/reference')
    result = client.post('/api/tasks/first-predict/submit', json={'response': '5', 'assisted': False}).json()
    assert result['assisted'] is True
    assert client.get('/api/learning').json()['task_progress']['first-predict']['independent_passed'] is False
    fresh = client.post('/api/tasks/first-predict/retry')
    assert fresh.status_code == 200
    assert client.post('/api/tasks/first-predict/submit', json={'response': '5'}).status_code == 409
    result = client.post('/api/tasks/first-predict/submit', json={**fresh.json(), 'response': '5'}).json()
    assert result['assisted'] is False


def test_duplicate_submission_is_idempotent(client):
    payload = {'response': '5', 'request_id': 'repeat-request'}
    a = client.post('/api/tasks/first-predict/submit', json=payload)
    b = client.post('/api/tasks/first-predict/submit', json=payload)
    assert b.status_code == 200, b.text
    assert a.json() == b.json()
    assert len(client.get('/api/tasks/first-predict/history').json()['attempts']) == 1
    changed = client.post('/api/tasks/first-predict/submit', json={**payload, 'response': '9'})
    assert changed.status_code == 409


def test_runtime_errors_and_timeout_are_clear(client):
    error = 'public class Main {public static void main(String[] a){throw new IllegalStateException("demo");}}'
    response = client.post('/api/run', json={'source': error}).json()
    assert response['status'] == 'runtime_error', response
    assert 'IllegalStateException' in response['stderr']
    forever = 'public class Main {public static void main(String[] a){while(true){}}}'
    response = client.post('/api/run', json={'source': forever, 'timeout_seconds': 0.5}).json()
    assert response['status'] == 'runtime_timeout'


def test_multibyte_source_limit_is_enforced(client):
    code = '// ' + '界' * 20000
    assert client.post('/api/run', json={'source': code}).status_code == 413


def test_hint_marks_assistance(client):
    assert client.post('/api/tasks/first-predict/hint/0').json()['hint'] == 'Add, do not concatenate.'
    assert client.get('/api/tasks/first-predict/draft').json()['assisted'] is True
