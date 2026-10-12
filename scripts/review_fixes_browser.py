"""Real Chrome regressions for hidden feedback and delayed autosaves after retry."""
import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('JAVA_STUDIO_QA_URL', 'http://127.0.0.1:4173')
TASK = 'java-program-skeleton-predict'
PATH = '/api/tasks/' + TASK


async def run():
    checks, errors = [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True)
        context = await browser.new_context()
        health = await (await context.request.get(BASE + '/api/health')).json()
        assert health.get('qa_mode'), 'Refusing to mutate normal learner data.'
        page = await context.new_page()
        page.on('dialog', lambda dialog: dialog.accept())
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.goto(BASE + '/?view=review&task=' + TASK)
        field = page.get_by_role('textbox', name='Your Prediction', exact=True)
        check = page.get_by_role('button', name='Check Prediction', exact=True)
        await expect(check).to_be_enabled()
        await field.fill('Wrong')
        await check.click()
        await expect(page.get_by_role('heading', name='Not Yet', exact=True)).to_be_visible()
        assert 'Reference Answer' not in await page.locator('.assessment').inner_text()
        history = await (await context.request.get(BASE + PATH + '/history')).json()
        assert all('answer' not in item and 'explanation' not in item for item in history['attempts'])
        checks.append('Wrong prediction and history do not expose the reference answer.')

        for phase in ['before_request', 'after_response']:
            await page.get_by_role('button', name='Reveal Reference', exact=True).click()
            await expect(page.locator('.reference-box')).to_be_visible()
            before = await (await context.request.get(BASE + PATH + '/draft')).json()
            assert before['assisted']
            captured, release, finished = asyncio.Event(), asyncio.Event(), asyncio.Event()
            held = False
            returned = {}
            sentinel = 'stale assisted draft ' + phase

            async def intercept(route, request, sentinel=sentinel, before=before, phase=phase,
                                captured=captured, release=release, returned=returned, finished=finished):
                nonlocal held
                body = request.post_data_json if request.method == 'PUT' else None
                if held or not body or body.get('response') != sentinel:
                    await route.continue_()
                    return
                held = True
                assert body['generation'] == before['generation']
                assert body['assisted']
                response = None
                if phase == 'after_response':
                    response = await route.fetch()
                captured.set()
                await release.wait()
                if response is None:
                    response = await route.fetch()
                returned['status'] = response.status
                await route.fulfill(response=response)
                finished.set()

            await page.route('**' + PATH + '/draft', intercept)
            await field.fill(sentinel)
            await asyncio.wait_for(captured.wait(), timeout=10)
            await page.get_by_role('button', name='Fresh Attempt', exact=True).click()
            await expect(field).to_have_value('')
            fresh = await (await context.request.get(BASE + PATH + '/draft')).json()
            assert fresh['generation'] == before['generation'] + 1
            release.set()
            await asyncio.wait_for(finished.wait(), timeout=10)
            assert returned['status'] == (409 if phase == 'before_request' else 200)
            await page.wait_for_timeout(700)
            await expect(field).to_have_value('')
            assert 'Independent attempt' in await page.locator('.task-panel > .section-row').inner_text()
            assert await page.locator('.inline-error').count() == 0
            stored = await (await context.request.get(BASE + PATH + '/draft')).json()
            assert stored['generation'] == fresh['generation']
            assert stored['response'] == '' and stored['assisted'] is False
            await page.unroute('**' + PATH + '/draft', intercept)
            await page.reload()
            await expect(check).to_be_enabled()
            await expect(field).to_have_value('')
            checks.append('Fresh retry survives delayed autosave ' + phase + ', keeps independent state, and survives reload.')

        await field.fill('Ready to build')
        await check.click()
        await expect(page.get_by_role('heading', name='Checks Passed', exact=True)).to_be_visible()
        checked = await (await context.request.get(BASE + PATH + '/history')).json()
        assert checked['attempts'][0]['passed'] and not checked['attempts'][0]['assisted']
        checks.append('New-generation submission records an actual independent pass.')
        assert not errors, errors
        await page.screenshot(path=str(ROOT / 'artifacts/review-fixes-browser.png'), full_page=True)
        await browser.close()
    result = {'passed': True, 'checks': checks, 'page_errors': errors}
    (ROOT / 'artifacts/review-fixes-browser.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    asyncio.run(run())
