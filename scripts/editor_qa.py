"""Actual browser regression for editor history, theme changes and keyboard escape."""
import os

from playwright.sync_api import expect, sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    page = browser.new_page()
    page.goto(os.environ.get('JAVA_STUDIO_QA_URL', 'http://127.0.0.1:8000') + '/?view=bench')
    editor = page.locator('.cm-content')
    editor.click()
    page.keyboard.press('Control+End')
    page.keyboard.insert_text('\n// history probe')
    expect(page.get_by_role('button',name='Undo last change')).to_be_enabled()
    page.get_by_role('button',name='Switch to Light Theme').click()
    expect(page.get_by_role('button',name='Undo last change')).to_be_enabled()
    page.get_by_role('button',name='Undo last change').click()
    assert '// history probe' not in editor.inner_text()
    page.get_by_role('button',name='Redo last undone change').click()
    assert '// history probe' in editor.inner_text()
    editor.click()
    page.keyboard.press('Tab')
    assert page.evaluate('document.activeElement.classList.contains("cm-content")'), 'Tab must indent as documented.'
    page.keyboard.press('Escape')
    page.keyboard.press('Tab')
    assert not page.evaluate('document.activeElement.classList.contains("cm-content")'), 'Escape then Tab must release focus.'
    browser.close()
print('PASS: theme retains undo/redo; Tab indents; Escape then Tab releases focus.')
