"""Opaque original-note hash comparison and scoped source safety audit.

Never prints source matches or demonstration credential values.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def audit():
    archive=ROOT.with_suffix('.zip')
    original={}
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            parts=entry.filename.replace('\\','/').split('/')
            if 'notes' not in parts or entry.is_dir():
                continue
            name='/'.join(parts[parts.index('notes')+1:])
            current=ROOT/'notes'/name
            assert current.is_file(),f'Original note missing: {name}'
            wanted=hashlib.sha256(bundle.read(entry)).hexdigest()
            actual=hashlib.sha256(current.read_bytes()).hexdigest()
            original[name]={'sha256':actual,'matches_original':actual==wanted}
    assert original,'Archive note discovery found no originals.'
    assert all(x['matches_original'] for x in original.values()),'An original note changed.'
    assert {str(p.relative_to(ROOT/'notes')).replace('\\','/') for p in (ROOT/'notes').rglob('*') if p.is_file()}==set(original),'The notes inventory differs from the archive.'
    canonical=ROOT/'frontend/src/styles/uika-canonical.css'
    estate=Path('C:/Users/iuniq/Desktop/Uika/design/uika-canonical.css')
    assert canonical.read_bytes()==estate.read_bytes(),'Canonical design CSS differs.'
    checks={
        'literal_secret_assignment':r'''(?i)(?:api_key|secret|password|token|passwd)\s*=\s*['"][^'"]{6,}['"]''',
        'shell_execution':r'os\.system\(|subprocess[^\n]*shell\s*=\s*True',
        'dynamic_execution':r'\beval\(|\bexec\(',
        'unsafe_pickle':r'pickle\.loads?\(',
        'formatted_sql':r'''\.execute\(f['"]''',
        'truncated_source_sentinel':r'\[truncated\]',
    }
    findings=[]
    files={}
    for folder in ['backend','frontend/src','content','scripts','tests']:
        for p in (ROOT/folder).rglob('*'):
            if not p.is_file() or p.suffix not in ('.py','.ts','.tsx','.css','.json') or '__pycache__' in p.parts or p.name=='audit_release.py':
                continue
            text=p.read_text(encoding='utf-8')
            files[str(p.relative_to(ROOT)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
            for category,pattern in checks.items():
                for match in re.finditer(pattern,text):
                    findings.append({'category':category,'file':str(p.relative_to(ROOT)).replace('\\','/'),'line':text.count('\n',0,match.start())+1})
    report={'checked_at':datetime.now().astimezone().isoformat(),'original_notes_checked':len(original),'all_original_notes_unchanged':True,'canonical_css_matches_estate':True,'source_files_scanned':len(files),'findings':findings,'note_hashes':original,'source_hashes':files}
    target=ROOT/'artifacts/release-audit.json'
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('note_hashes','source_hashes')},indent=2))
    assert not findings,'Static scan requires manual review; no matched values were printed.'


if __name__=='__main__':
    audit()
