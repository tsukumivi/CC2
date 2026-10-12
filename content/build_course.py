"""Build the shipped corpus from explicitly authored lessons.

Run: python -m content.build_course
The archive is read only for original PDF reference metadata, never Java credentials.
"""
from __future__ import annotations

import importlib
import json
import zipfile
from copy import deepcopy
from pathlib import Path

from content.transfer import TRANSFER

ROOT = Path(__file__).resolve().parents[1]
UNITS = [
    ('first-success', '01 / First Success', 'From one running program to a precise language-independent plan.', 'first_success'),
    ('values', '02 / Values & Calculations', 'Make names, types, arithmetic and output mean what you intend.', 'values'),
    ('input-text', '03 / Input & Text', 'Accept full lines, understand tokens and treat empty text deliberately.', 'input_text'),
    ('decisions', '04 / Decisions & Recovery', 'Choose branches and reject invalid paths before doing work.', 'decisions'),
    ('repetition', '05 / Repetition & a Usable Workflow', 'Repeat, recover and terminate; build a ticket counter.', 'repetition'),
    ('structure', '06 / Methods & Evidence', 'Refactor responsibilities, handle specific failures and test boundaries.', 'structure'),
    ('records', '07 / Collections & Objects', 'Represent and manage records without losing their relationships.', 'records'),
    ('persistence', '08 / Persistence & Independence', 'Save/load data, survive restart and run the finished program outside the Studio.', 'persistence'),
]


def original_metadata():
    archive = ROOT.parent / 'Java-Fieldnotes-Learning-Studio.zip'
    if archive.exists():
        with zipfile.ZipFile(archive) as bundle:
            names = [name for name in bundle.namelist() if name.endswith('/content/course.json') or name == 'content/course.json']
            return json.loads(bundle.read(names[0]).decode('utf-8-sig'))
    # A moved checkout can build without the original private archive.
    return json.loads((ROOT / 'content/source-metadata.json').read_text(encoding='utf-8'))


def build():
    old = original_metadata()
    source_metadata = {c['id']: c.get('source_pdfs', []) for c in old['concepts']}
    modules, concepts = [], []
    previous_core = None
    for mid, title, summary, filename in UNITS:
        lessons = deepcopy(importlib.import_module('content.units.' + filename).LESSONS)
        next(c for c in reversed(lessons) if not c.get('optional'))['tasks'].append(deepcopy(TRANSFER[mid]))
        modules.append({'id': mid, 'title': title, 'summary': summary, 'concept_ids': [c['id'] for c in lessons]})
        for concept in lessons:
            concept['module_id'] = mid
            concept['prerequisites'] = [previous_core] if previous_core else []
            concept['provenance'] = 'Authored course material. Original PDF links are background/outline references, not a claim that the expanded explanation or task was present in that lecture.'
            refs = []
            for ref in source_metadata.get(concept['id'], []):
                refs.append({**ref, 'basis': 'syllabus_outline' if ref.get('basis') == 'syllabus_preview' else 'background_lecture'})
            concept['source_pdfs'] = refs
            concept['technical_reference'] = 'https://dev.java/learn/api/io/' if mid == 'persistence' else 'https://dev.java/learn/language/oop/' if mid in ('structure', 'records') else 'https://dev.java/learn/language/constructs/'
            concepts.append(concept)
            if not concept.get('optional'):
                previous_core = concept['id']
    course = {
        'id': old.get('id', 'java-fieldnotes'), 'version': 2,
        'title': 'Java Fieldnotes',
        'description': 'A local-first route from your first program to a tested, persistent console record manager.',
        'source_files': [s for s in old.get('source_files', []) if s.lower().endswith('.pdf')],
        'learning_cycle': ['Understand', 'Explain', 'Predict', 'Repair / Modify', 'Build', 'Revisit'],
        'modules': modules, 'concepts': concepts,
        'reviewer': {'title':'Practice That Transfers', 'purpose':'Exact predictions, honest explanation self-checks, and Java repair/modify/build tasks. Answers are not shown before an attempt.',
                     'questions': [{'id': t['id'], 'concept_id': c['id'], 'kind': t['kind']} for c in concepts for t in c['tasks']]},
        'curriculum_note': 'Authored expansion through methods, collections, objects and UTF-8 file persistence. Optional ternary is not a core prerequisite. A learner trial, not a content count, must establish learning effectiveness.',
        'assessment_note': 'Exact and executable checks are server evaluated. Explanations and design criteria are learner self-assessments. Reference/hint-assisted passes are practice. Declared tests do not prove every possible input correct.',
    }
    (ROOT / 'content/course.json').write_text(json.dumps(course, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Shipping the metadata makes rebuild independent of the parent archive.
    metadata = {'concepts': [{'id': cid, 'source_pdfs': refs} for cid, refs in source_metadata.items()], 'source_files': old.get('source_files', []), 'id': old.get('id', 'java-fieldnotes')}
    (ROOT / 'content/source-metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'modules':len(modules), 'concepts':len(concepts), 'core_concepts':sum(not c.get('optional') for c in concepts), 'tasks':sum(len(c['tasks']) for c in concepts)}))


if __name__ == '__main__':
    build()
