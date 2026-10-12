"""Export an allowlisted, data-free release after the executed fix gates pass."""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def run():
    suites = list(ET.parse(ROOT / 'artifacts/pytest-results.xml').getroot().iter('testsuite'))
    assert suites and all(int(s.attrib['failures']) == 0 and int(s.attrib['errors']) == 0 for s in suites)
    for name in ['review-fixes-browser.json', 'browser-qa/results.json', 'portability-verification.json', 'final-review.json']:
        assert json.loads((ROOT / 'artifacts' / name).read_text(encoding='utf-8'))['passed'], name
    audit = json.loads((ROOT / 'artifacts/release-audit.json').read_text(encoding='utf-8'))
    assert audit['all_original_notes_unchanged'] and not audit['findings']
    files = {}

    def add(path):
        assert path.is_file() and not path.is_symlink(), str(path)
        rel = path.relative_to(ROOT).as_posix()
        assert not any(part in {'..', '.env', '.git', 'node_modules', '.venv', '.tools', '__pycache__', 'data'} for part in PurePosixPath(rel).parts)
        assert path.suffix.lower() not in {'.db', '.sqlite', '.pyc', '.exe', '.zip', '.log'}
        assert not path.name.lower().startswith('.env')
        files[rel] = path.read_bytes()

    for name in ['README.md', 'START-HERE.md', 'VERIFICATION.md', 'IMPLEMENTATION-STATUS.md', 'LEARNER-TRIAL.md',
                 'requirements.txt', 'requirements-lock.txt', 'runtime-lock.txt']:
        add(ROOT / name)
    for directory, suffixes in [('backend', {'.py'}), ('content', {'.py', '.json'}), ('tests', {'.py'}),
                                ('frontend/src', {'.ts', '.tsx', '.css'}), ('frontend/tests', {'.ts'})]:
        for path in sorted((ROOT / directory).rglob('*')):
            if path.is_file() and path.suffix in suffixes and '__pycache__' not in path.parts:
                add(path)
    for path in sorted((ROOT / 'scripts').glob('*.py')):
        if path.name != 'build_review_packet.py':
            add(path)
    for name in ['package.json', 'pnpm-lock.yaml', 'pnpm-workspace.yaml', 'index.html', 'vite.config.ts', 'tsconfig.json']:
        add(ROOT / 'frontend' / name)
    for directory in ['frontend/public', 'frontend/dist', 'uika-design']:
        for path in sorted((ROOT / directory).rglob('*')):
            if path.is_file():
                add(path)
    course = json.loads((ROOT / 'content/course.json').read_text(encoding='utf-8'))
    for name in course['source_files']:
        assert PurePosixPath(name).parts[0] == 'notes' and name.lower().endswith('.pdf')
        add(ROOT / name)
    for name in ['pytest-results.xml', 'corpus-verification.json', 'portability-verification.json',
                 'browser-qa/results.json', 'review-fixes-browser.json', 'luna-review-packet.json',
                 'final-review.json', 'release-audit.json', 'delivery-verification.json']:
        path = ROOT / 'artifacts' / name
        if path.exists():
            add(path)
    assert 'frontend/dist/index.html' in files
    assert len([p for p in files if p.startswith('notes/')]) == len(course['source_files'])
    assert not any(p.endswith('.java') for p in files)  # Do not redistribute legacy demonstrations.
    for name, data in files.items():
        if name.endswith(('.ts', '.tsx', '.css', '.json', '.md', '.txt', '.html', '.yaml')):
            # Split the marker so the static audit does not flag this guard itself.
            assert (b'[' + b'truncated]') not in data, name
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    files['RELEASE-MANIFEST.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    output = ROOT.parent / (ROOT.name + '-Updated-' + datetime.now().strftime('%Y-%m-%d') + '.zip')
    assert output != ROOT.with_suffix('.zip')
    if output.exists() and '--replace' not in sys.argv:
        raise FileExistsError('New release already exists; use --replace only for this task-owned updated release.')
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in sorted(files.items()):
            z.writestr(ROOT.name + '/' + name, data)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(files)
        for name, digest in manifest.items():
            assert hashlib.sha256(z.read(ROOT.name + '/' + name)).hexdigest() == digest
    result = {'path': str(output), 'files': len(files), 'bytes': output.stat().st_size,
              'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'crc_and_manifest_verified': True,
              'excluded': ['learner data', 'QA data/logs', 'local environments', 'node_modules', 'JDK binaries', 'legacy Java demos', 'raw reviewer packets']}
    (ROOT / 'artifacts/package-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    run()
