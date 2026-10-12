from contextlib import ExitStack
from uuid import uuid4

from fastapi.testclient import TestClient

from backend import main, runner


def test_utf8_source_input_and_output(client):
    code='import java.util.Scanner; public class Main {public static void main(String[] a){Scanner s=new Scanner(System.in);System.out.println("Hello "+s.nextLine());}}'
    r=client.post('/api/run',json={'source':code,'stdin':'星\n'}).json()
    assert r['status']=='completed',r
    assert runner.normalized(r['stdout'])=='Hello 星'


def test_output_flood_is_captured_without_unbounded_response(client):
    code='public class Main {public static void main(String[] a){for(int i=0;i<20000;i++)System.out.print("x");}}'
    r=client.post('/api/run',json={'source':code}).json()
    assert r['output_truncated'] is True
    assert len(r['stdout'].encode('utf-8'))<=main.MAX_OUTPUT_BYTES+80


def test_runner_rejects_requests_when_both_job_slots_are_occupied(client):
    with ExitStack() as stack:
        for _ in range(2):
            assert runner.CAPACITY.acquire(blocking=False)
            stack.callback(runner.CAPACITY.release)
        r=client.post('/api/run',json={'source':'public class Main {}'})
        assert r.status_code==429,r.text


def test_real_startup_preserves_legacy_projects_and_activity_without_awarding_mastery(client,tmp_path,monkeypatch):
    data=tmp_path/'old-installation'
    monkeypatch.setattr(main,'DATA_DIR',data)
    monkeypatch.setattr(main,'DATABASE_PATH',data/'learning.db')
    main.initialize_db()  # Only the original legacy tables, before the new lifespan runs.
    pid=str(uuid4())
    code='public class Main {public static void main(String[] a){System.out.println("Kept");}}'
    with main.connect_db() as db:
        db.execute('INSERT INTO projects VALUES (?,?,?,?,?,?)',(pid,'Original project','Keep me',code,'2026-01-01','2026-01-01'))
        db.execute("INSERT INTO concept_progress(concept_id,attempts,build_best,mastered_at) VALUES ('first',7,1,'2026-01-01')")
    with TestClient(main.app,base_url='http://127.0.0.1:8000',client=('127.0.0.1',50000)) as reopened:
        projects=reopened.get('/api/projects').json()['projects']
        assert projects[0]['id']==pid and projects[0]['code']==code
        assert reopened.get('/api/learning').json()['completed_concept_ids']==[]
        assert reopened.get('/api/progress').json()['concepts'][0]['attempts']==7
