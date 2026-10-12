"""Small, explicit saved-project data workspaces. No arbitrary path API."""
from __future__ import annotations

import re
import threading
from contextlib import contextmanager

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from backend.runner import safe_file

LOCKS: dict[str, threading.Lock] = {}
LOCKS_GUARD = threading.Lock()
EXTENSIONS = {'.txt', '.csv', '.json', '.md', '.log', '.dat'}
MAX_FILE_BYTES = 64_000


def project(repo, project_id):
    if not re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', project_id):
        raise HTTPException(422, 'Use the exact saved project ID returned by the Studio.')
    with repo.connect_db() as db:
        row = db.execute('SELECT * FROM projects WHERE id=?', (project_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Save or open this project before accessing its data workspace.')
    return dict(row)


def workspace(repo, project_id):
    project(repo, project_id)
    path = repo.DATA_DIR / 'workspaces' / project_id
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.resolve().parent != (repo.DATA_DIR / 'workspaces').resolve():
        raise HTTPException(422, 'Project workspace must stay in its local data directory.')
    return path


@contextmanager
def locked(project_id):
    with LOCKS_GUARD:
        lock = LOCKS.setdefault(project_id, threading.Lock())
    if not lock.acquire(blocking=False):
        raise HTTPException(409, 'This project is running or its files are being edited. Wait, then retry.')
    try:
        yield
    finally:
        lock.release()


def data_file(folder, name):
    path = safe_file(folder, name)
    if path.suffix.lower() not in EXTENSIONS:
        raise HTTPException(422, 'Import/export supports text data files: .txt, .csv, .json, .md, .log or .dat.')
    return path


class FileSubmission(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: str = Field(max_length=MAX_FILE_BYTES)


def install(app, repo):
    @app.get('/api/projects/{project_id}')
    def get_project(project_id: str):
        return project(repo, project_id)

    @app.get('/api/projects/{project_id}/files')
    def list_files(project_id: str):
        folder = workspace(repo, project_id)
        files = []
        for index, path in enumerate(folder.iterdir()):
            if index >= 200:
                return {'files': files, 'truncated': True}
            if path.suffix.lower() in EXTENSIONS and path.is_file() and not path.is_symlink():
                files.append({'name':path.name, 'bytes':path.stat().st_size, 'readable':path.stat().st_size <= MAX_FILE_BYTES})
        return {'files': sorted(files, key=lambda f:f['name']), 'truncated': False}

    @app.get('/api/projects/{project_id}/files/{name}')
    def read_file(project_id: str, name: str):
        path = data_file(workspace(repo, project_id), name)
        with locked(project_id):
            if not path.is_file():
                raise HTTPException(404, 'That data file does not exist.')
            if path.stat().st_size > MAX_FILE_BYTES:
                raise HTTPException(413, 'This file exceeds the 64 KB text inspection limit. Inspect it locally instead.')
            try:
                return {'name':name, 'content':path.read_text(encoding='utf-8')}
            except (OSError, UnicodeDecodeError):
                raise HTTPException(422, 'Cannot read this file as UTF-8 text.')

    @app.put('/api/projects/{project_id}/files/{name}')
    def write_file(project_id: str, name: str, submission: FileSubmission):
        folder = workspace(repo, project_id)
        path = data_file(folder, name)
        encoded = submission.content.encode('utf-8')
        if len(encoded) > MAX_FILE_BYTES:
            raise HTTPException(413, 'Imported text must be at most 64 KB of UTF-8 bytes.')
        with locked(project_id):
            listed = list_files(project_id)
            if listed['truncated'] or len(listed['files']) >= 50 and not path.exists():
                raise HTTPException(413, 'Workspace has too many files. Remove an unused data file first.')
            temporary = folder / (name + '.importing')
            try:
                temporary.write_bytes(encoded)
                temporary.replace(path)
            except OSError:
                raise HTTPException(422, 'Cannot replace this data file. Check permissions or a running program.')
            finally:
                temporary.unlink(missing_ok=True)
        return {'name':name, 'bytes':len(encoded)}

    @app.delete('/api/projects/{project_id}/files/{name}')
    def delete_file(project_id: str, name: str):
        path = data_file(workspace(repo, project_id), name)
        with locked(project_id):
            if not path.is_file():
                raise HTTPException(404, 'That data file does not exist.')
            path.unlink()
        return {'deleted':name}
