

def save(client, title='My inventory'):
    r = client.post('/api/projects', json={'title':title, 'code':'public class Main {public static void main(String[] a){}}'})
    assert r.status_code == 200, r.text
    return r.json().get('project', r.json())


def test_saved_project_workspace_persists_across_java_runs(client):
    project = save(client)
    writer = 'import java.nio.file.*; public class Main {public static void main(String[] a) throws Exception {Files.writeString(Path.of("records.txt"), "Orbit|2\\n");System.out.println("Saved");}}'
    reader = 'import java.nio.file.*; public class Main {public static void main(String[] a) throws Exception {System.out.print(Files.readString(Path.of("records.txt")));}}'
    a = client.post('/api/run', json={'source':writer, 'project_id':project['id']})
    assert a.status_code == 200, a.text
    b = client.post('/api/run', json={'source':reader, 'project_id':project['id']})
    assert b.json()['stdout'] == 'Orbit|2\n', b.text
    files = client.get(f"/api/projects/{project['id']}/files").json()['files']
    assert files[0]['name'] == 'records.txt'
    assert client.get(f"/api/projects/{project['id']}/files/records.txt").json()['content'] == 'Orbit|2\n'


def test_project_data_import_export_and_traversal(client):
    project = save(client)
    base = f"/api/projects/{project['id']}/files"
    assert client.put(base+'/records.txt', json={'content':'星|2\n'}).status_code == 200
    assert client.get(base+'/records.txt').json()['content'] == '星|2\n'
    assert client.put(base+'/Main.java', json={'content':'bad'}).status_code == 422
    assert client.put(base+'/attack.exe', json={'content':'bad'}).status_code == 422
    assert client.put(base+'/../outside.txt', json={'content':'bad'}).status_code in (404,405,422)
    assert client.delete(base+'/records.txt').status_code == 200
    assert client.get(base+'/records.txt').status_code == 404


def test_workspaces_do_not_leak_between_projects(client):
    first, second = save(client,'First'), save(client,'Second')
    client.put(f"/api/projects/{first['id']}/files/records.txt", json={'content':'Only first\n'})
    assert client.get(f"/api/projects/{second['id']}/files").json()['files'] == []
    assert client.get('/api/projects/not-real/files').status_code in (404,422)


def test_project_unknown_update_id_rejected(client):
    assert client.post('/api/projects', json={'id':'../other','title':'Oops','code':'bad'}).status_code in (404,422)


def test_unchecked_legacy_progress_does_not_become_new_mastery(client):
    from backend import main
    with main.connect_db() as db:
        db.execute("INSERT INTO concept_progress(concept_id,attempts,build_best,explain_best,trace_best) VALUES ('first',4,1,1,1)")
    assert client.get('/api/learning').json()['completed_concept_ids'] == []
    assert client.get('/api/progress').json()['concepts'][0]['attempts'] == 4
