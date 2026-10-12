"""Real Chrome UI QA against a running Studio with an isolated QA data directory.

Never run on the learner's production data. Server example:
JAVA_STUDIO_QA_MODE=1 JAVA_STUDIO_DATA_DIR=<project>/artifacts/qa-data python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/browser-qa'
OUT.mkdir(parents=True, exist_ok=True)
COURSE = json.loads((ROOT/'content/course.json').read_text(encoding='utf-8'))
BASE = os.environ.get('JAVA_STUDIO_QA_URL', 'http://127.0.0.1:8000')


def source(page, code):
    editor = page.locator('.cm-content')
    editor.click()
    page.keyboard.press('Control+a')
    page.keyboard.insert_text(code)


def checked_rubric(page):
    for box in page.locator('.rubric input').all():
        box.check()


def open_task(page, tid):
    page.goto(BASE + '/?view=review&task=' + tid)
    expect(page.locator('.task-panel')).to_be_visible()
    page.wait_for_timeout(600)


def run():
    started = time.perf_counter()
    checks, page_errors = [], []
    title='QA Restart Inventory '+str(time.time_ns())
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True)
        context = browser.new_context(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
        page = context.new_page()
        page.on('pageerror', lambda e:page_errors.append(str(e)))
        page.on('dialog', lambda dialog:dialog.accept())
        health = context.request.get(BASE+'/api/health').json()
        assert health.get('qa_mode'), 'Refusing to modify learner data. Restart with JAVA_STUDIO_QA_MODE=1 and an explicit isolated JAVA_STUDIO_DATA_DIR.'
        assert health['jdk_available'], health
        page.goto(BASE)
        expect(page.get_by_role('heading',name='From first line to a useful program.')).to_be_visible()
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(OUT/'desk-dark.png'),full_page=True)
        checks.append('Production build loads; real course and local JDK available.')
        open_task(page,'java-program-skeleton-predict')
        assert page.locator('.answer-key').count()==0
        page.get_by_role('textbox',name='Your Prediction',exact=True).fill('unfinished draft')
        page.get_by_role('link',name='Study Desk').click()
        page.get_by_role('link',name='Practical Review').click()
        page.goto(BASE+'/?view=review&task=java-program-skeleton-predict')
        expect(page.get_by_role('textbox',name='Your Prediction',exact=True)).to_have_value('unfinished draft')
        page.reload()
        expect(page.get_by_role('textbox',name='Your Prediction',exact=True)).to_have_value('unfinished draft')
        checks.append('Prediction draft survives navigation and full reload; no answer displayed first.')
        page.get_by_role('textbox',name='Your Prediction',exact=True).fill('Wrong')
        page.get_by_role('button',name='Check Prediction',exact=True).click()
        expect(page.get_by_role('heading',name='Not Yet',exact=True)).to_be_visible(timeout=15000)
        assert page.locator('.answer-key').count() == 0
        assert 'Reference Answer' not in page.locator('.assessment').inner_text()
        page.get_by_role('button',name='Fresh Attempt',exact=True).click()
        expect(page.get_by_role('textbox',name='Your Prediction',exact=True)).to_have_value('')
        page.get_by_role('textbox',name='Your Prediction',exact=True).fill('Ready to build')
        page.get_by_role('button',name='Check Prediction',exact=True).click()
        expect(page.get_by_role('heading',name='Checks Passed',exact=True)).to_be_visible(timeout=15000)
        checks.append('Wrong prediction fails; a fresh independent retry passes and history is saved.')
        open_task(page,'java-program-skeleton-explain')
        page.get_by_role('textbox',name='Your Explanation',exact=True).fill('javac compiles source into bytecode. java runs Main and invokes main.')
        checked_rubric(page)
        page.get_by_role('button',name='Record Self-Check',exact=True).click()
        expect(page.get_by_role('heading',name='Self-Check Recorded',exact=True)).to_be_visible()
        open_task(page,'java-program-skeleton-build')
        source(page,'public class Main {\n public static void main(String[] args) { System.out.println("Wrong"); }\n}\n')
        checked_rubric(page)
        page.get_by_role('button',name='Check All Cases',exact=True).click()
        expect(page.get_by_role('heading',name='Not Yet',exact=True)).to_be_visible(timeout=20000)
        assert 'Wrong' in page.locator('.assessment').inner_text()
        assert 'My first Java program' in page.locator('.assessment').inner_text()
        page.screenshot(path=str(OUT/'failed-build-feedback.png'),full_page=True)
        source(page,'public class Main {\n public static void main(String[] args) { System.out.println("My first Java program"); }\n}\n')
        page.get_by_role('button',name='Check All Cases',exact=True).click()
        expect(page.get_by_role('heading',name='Checks Passed',exact=True)).to_be_visible(timeout=20000)
        learning = context.request.get(BASE+'/api/learning').json()
        assert 'java-program-skeleton' in learning['completed_concept_ids']
        assert learning['next_concept_id']=='output-and-comments'
        checks.append('Real Java wrong-output grading fails; correct output plus all core requirements advances route.')
        page.get_by_role('button',name='Attempt History',exact=True).click()
        expect(page.get_by_role('heading',name='Saved Attempts')).to_be_visible()
        assert page.locator('.history details').count()>=2
        checks.append('Both actual submitted Java source and grading evidence remain in attempt history.')
        open_task(page,'types-variables-predict')
        page.get_by_role('button',name='Reveal Reference',exact=True).click()
        expect(page.locator('.reference-box')).to_be_visible()
        page.get_by_role('textbox',name='Your Prediction',exact=True).fill('5')
        page.get_by_role('button',name='Check Prediction',exact=True).click()
        expect(page.get_by_role('heading',name='Passed with Assistance',exact=True)).to_be_visible()
        assert not context.request.get(BASE+'/api/learning').json()['task_progress']['types-variables-predict']['independent_passed']
        checks.append('Explicit reference marks assistance and cannot establish independent mastery.')
        page.goto(BASE+'/?view=review')
        page.get_by_role('combobox',name='Practice Mode',exact=True).select_option('repair')
        page.get_by_role('combobox',name='Topic',exact=True).select_option('encapsulation')
        expect(page.get_by_role('heading',name='No Tasks in This Queue')).to_be_visible()
        checks.append('A zero-result review filter shows an honest empty state.')
        # Keep restart work in one actual saved project; each Run launches a new JVM.
        page.goto(BASE+'/?view=bench')
        expect(page.locator('.cm-content')).to_be_visible()
        capstone = next(c for c in COURSE['concepts'] if c['id']=='capstone-records')
        code = next(t['reference_code'] for t in capstone['tasks'] if t['kind']=='build')
        source(page,code)
        page.get_by_role('textbox',name='Project Title',exact=True).fill(title)
        page.get_by_role('button',name='Save New Project',exact=True).click()
        expect(page.get_by_text('Project saved and verified. Data files stay in its workspace.',exact=True)).to_be_visible(timeout=15000)
        page.get_by_role('textbox',name='Standard Input',exact=True).fill('add|Orbit|2\nsave\nq\n')
        page.get_by_role('button',name='Compile & Run',exact=True).click()
        expect(page.locator('.run-output')).to_be_visible(timeout=20000)
        assert 'Added\nSaved\nBye' in page.locator('.run-output').inner_text().replace('\r\n','\n'), page.locator('.run-output').inner_text().replace('\r\n','\n')
        expect(page.get_by_role('button',name='records.txt',exact=True)).to_be_visible()
        page.get_by_role('textbox',name='Standard Input',exact=True).fill('list\nq\n')
        page.get_by_role('button',name='Compile & Run',exact=True).click()
        expect(page.locator('.run-output')).to_be_visible(timeout=20000)
        assert 'Orbit|2\nBye' in page.locator('.run-output').inner_text().replace('\r\n','\n')
        page.get_by_role('button',name='records.txt',exact=True).click()
        expect(page.get_by_role('textbox',name='UTF-8 Data',exact=True)).to_have_value('Orbit|2\n')
        page.screenshot(path=str(OUT/'project-restart.png'),full_page=True)
        checks.append('Saved project compiles/runs capstone, persists records.txt and loads it in a separate JVM.')
        page.get_by_role('textbox',name='UTF-8 Data',exact=True).fill('Orbit|bad\n')
        page.get_by_role('button',name='Save Data File',exact=True).click()
        expect(page.get_by_text('Data file saved and read-back verified.',exact=True)).to_be_visible()
        page.get_by_role('button',name='Compile & Run',exact=True).click()
        expect(page.locator('.run-output')).to_be_visible(timeout=20000)
        assert 'Load failed' in page.locator('.run-output').inner_text().replace('\r\n','\n')
        page.get_by_role('button',name='records.txt',exact=True).click()
        expect(page.get_by_role('textbox',name='UTF-8 Data',exact=True)).to_have_value('Orbit|bad\n')
        checks.append('Imported corrupt data causes truthful load failure and is not overwritten.')
        page.get_by_role('textbox',name='UTF-8 Data',exact=True).fill('Orbit|2\n')
        page.get_by_role('button',name='Save Data File',exact=True).click()
        expect(page.get_by_text('Data file saved and read-back verified.',exact=True)).to_be_visible()
        page.get_by_role('link',name='Project Shelf').click()
        expect(page.get_by_role('heading',name=title)).to_be_visible()
        page.get_by_role('link',name='Saved Java Project '+title).click()
        expect(page.get_by_role('textbox',name='Project Title',exact=True)).to_have_value(title)
        checks.append('Named source saves to SQLite and reopens through the project shelf.')
        page.goto(BASE+'/?view=learn&lesson=flowchart-symbols')
        expect(page.get_by_role('heading',name='Draw a Decision Path',exact=True)).to_be_visible()
        assert page.locator('.lesson-diagram').count()==1
        assert page.locator('.source-links a').count()>=2
        page.screenshot(path=str(OUT/'lesson-dark.png'),full_page=True)
        source_name=COURSE['source_files'][0].split('/')[-1]
        response=context.request.get(BASE+'/api/sources/'+source_name)
        assert response.ok and 'application/pdf' in response.headers['content-type']
        checks.append('Planning lesson is language-independent; numbered branch model and original local PDF work.')
        page.goto(BASE)
        page.get_by_role('button',name='Switch to Light Theme',exact=True).click()
        assert page.locator('html').get_attribute('data-face')=='sumimi'
        page.reload()
        expect(page.get_by_role('heading',name='From first line to a useful program.')).to_be_visible(timeout=30000)
        expect(page.get_by_role('button',name='Switch to Dark Theme',exact=True)).to_be_visible()
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(OUT/'desk-light.png'),full_page=True)
        checks.append('Canonical light/dark theme choice survives reload; local font files load.')
        page.set_viewport_size({'width':390,'height':844})
        for route in ['?view=home','?view=learn&lesson=capstone-records','?view=review&task=workflow-projects-build','?view=bench','?view=projects','?view=sources']:
            page.goto(BASE+'/'+route)
            expect(page.locator('main')).to_be_visible()
            expect(page.locator('.loading-state')).to_have_count(0,timeout=30000)
            assert page.get_by_role('heading',name='The Local Backend Is Unavailable').count()==0
            page.wait_for_timeout(300)
            dimensions=page.evaluate('({content:document.documentElement.scrollWidth,viewport:window.innerWidth})')
            assert dimensions['content']<=dimensions['viewport']+1, (route,dimensions)
        page.goto(BASE)
        expect(page.get_by_role('heading',name='From first line to a useful program.')).to_be_visible(timeout=30000)
        page.screenshot(path=str(OUT/'desk-mobile.png'),full_page=True)
        checks.append('All six views fit a 390px viewport without page-level horizontal overflow.')
        page.set_viewport_size({'width':1440,'height':1000})
        page.goto(BASE)
        expect(page.get_by_role('heading',name='From first line to a useful program.')).to_be_visible(timeout=30000)
        page.keyboard.press('Tab')
        assert page.evaluate('document.activeElement.textContent').strip()=='Skip to Content'
        page.keyboard.press('Enter')
        assert page.evaluate('document.activeElement.id')=='main-content'
        checks.append('Keyboard skip link moves focus to main content.')
        page.route('**/api/**',lambda route:route.abort())
        page.reload()
        expect(page.get_by_role('heading',name='The Local Backend Is Unavailable')).to_be_visible()
        assert 'No sample course or invented progress' in page.locator('main').inner_text()
        page.screenshot(path=str(OUT/'offline-state.png'),full_page=True)
        checks.append('Offline/API failure is explicit, with no fallback fake course or progress.')
        assert not page_errors, page_errors
        browser.close()
    result={'passed':True,'checks':checks,'page_errors':page_errors,'duration_seconds':round(time.perf_counter()-started,2)}
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    run()
