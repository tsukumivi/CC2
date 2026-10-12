from backend import main


def test_browser_qa_flag_requires_an_explicit_nonproduction_directory(client,monkeypatch):
    monkeypatch.delenv('JAVA_STUDIO_QA_MODE',raising=False)
    assert client.get('/api/health').json().get('qa_mode') is False
    monkeypatch.setenv('JAVA_STUDIO_QA_MODE','1')
    assert client.get('/api/health').json()['qa_mode'] is True
    monkeypatch.setattr(main,'DATA_DIR',main.ROOT_DIR/'data')
    assert client.get('/api/health').json()['qa_mode'] is False
