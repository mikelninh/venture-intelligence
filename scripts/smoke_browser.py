"""End-to-end browser smoke, backed by the real FastAPI ASGI app.

This runner injects local static assets because this execution environment blocks
Chromium network navigation. It verifies the real API, SQLite persistence and UI.
Requires playwright + Chromium to be installed separately.
"""
import asyncio
import json
import sys
from pathlib import Path
import httpx
from playwright.async_api import async_playwright
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app import main
from app.db import Store

async def main_test():
    main.store = Store(str(ROOT / 'backend' / 'data' / 'browser-smoke.db'))
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page = await browser.new_page(viewport={'width':1440,'height':1040}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        client = httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url='http://app', timeout=30)
        async def bridge_fetch(path, method='GET', body=None):
            resp = await client.request(method, path, content=body,
                     headers={'Content-Type':'application/json'} if body else {})
            return {'status':resp.status_code, 'body':resp.text,
                    'contentType':resp.headers.get('content-type','application/json')}
        await page.expose_function('bridgeFetch', bridge_fetch)
        await page.set_content('<div id="mount"></div><input id="file" type="file" hidden/>')
        await page.add_style_tag(content=(ROOT / 'frontend' / 'standalone' / 'style.css').read_text())
        await page.evaluate("""() => {window.fetch=async (p,o={})=>{const r=await window.bridgeFetch(p,o.method||'GET',o.body||null);return new Response(r.body,{status:r.status,headers:{'Content-Type':r.contentType}})};}""")
        await page.add_script_tag(content=(ROOT / 'frontend' / 'standalone' / 'app.js').read_text())
        await page.wait_for_selector('.upload-card')
        await page.screenshot(path=str(ROOT / 'preview-empty.png'), full_page=True)
        await page.get_by_text('HelioGrid AI').first.click()
        await page.wait_for_selector('.analysis-heading h2')
        assert await page.locator('.analysis-heading h2').inner_text() == 'HelioGrid AI'
        await page.wait_for_timeout(3200)
        await page.screenshot(path=str(ROOT / 'preview-analysis.png'), full_page=True)
        await page.locator('.evidence-pill').first.click()
        assert await page.locator('.inspector-document').count() == 1
        await page.screenshot(path=str(ROOT / 'preview-evidence.png'), full_page=True)
        await page.locator('[data-tab="trace"]').first.click()
        assert await page.locator('.trace-step').count() == 4
        assert 'local-sequential' in await page.locator('.engine-tag').inner_text()
        assert 'Verify every citation' in await page.locator('.trace-grid').inner_text()
        await page.screenshot(path=str(ROOT / 'preview-workflow.png'), full_page=True)
        await page.locator('[data-tab="review"]').first.click()
        await page.locator('#notes').fill('Check enterprise contract evidence before further diligence.')
        await page.locator('[data-status="reviewed"]').click()
        await page.wait_for_function("document.querySelector('.review-chip')?.textContent?.includes('Reviewed')")
        assert 'Reviewed' in await page.locator('.review-chip').inner_text()
        await page.locator('[data-nav="dealflow"]').first.click()
        assert 'HelioGrid AI' in await page.locator('.table-panel').inner_text()
        await page.locator('.deal-row').first.click()
        await page.locator('[data-tab="review"]').first.click()
        assert await page.locator('#notes').input_value() == 'Check enterprise contract evidence before further diligence.'
        await page.screenshot(path=str(ROOT / 'preview-review.png'), full_page=True)
        await page.set_viewport_size({'width':390,'height':844})
        assert await page.locator('.mobile-hamburger').is_visible()
        await page.locator('.mobile-hamburger').click()
        assert await page.locator('.sidebar').is_visible()
        await page.locator('.mobile-close').click()
        await page.screenshot(path=str(ROOT / 'preview-mobile.png'), full_page=True)
        await page.set_viewport_size({'width':1440,'height':1040})
        # Interactive engineering lab: 30 real synthetic evaluations, filter and inspect a failure.
        await page.locator('[data-nav="eval"]').first.click()
        await page.wait_for_selector('.lab-metrics')
        assert '30' in await page.locator('.lab-stamp').inner_text()
        await page.locator('[data-scenario="unlabelled"]').click()
        assert await page.locator('.lab-case').count() == 5
        await page.locator('.lab-case button').first.click()
        assert await page.locator('.case-details').count() == 1
        await page.wait_for_timeout(200)
        await page.screenshot(path=str(ROOT / 'preview-evaluation.png'), full_page=True)
        # The narrative's deliberate contradiction must be visible and linked to source lines.
        await page.locator('[data-nav="workbench"]').first.click()
        await page.locator('[data-slug="novasense"]').click()
        await page.wait_for_selector('.claim-duel')
        assert '8 paid pilot customers' in await page.locator('.claim-duel').inner_text()
        assert '80 paying customers' in await page.locator('.claim-duel').inner_text()
        assert 'Conflicting claims' in await page.locator('.fact-conflict').inner_text()
        await page.wait_for_timeout(3200)
        await page.screenshot(path=str(ROOT / 'preview-contradiction.png'), full_page=True)
        await page.locator('.claim-card').first.click()
        await page.wait_for_selector('.inspector-document')
        assert await page.locator('.evidence-record.focused').count() == 1
        await page.screenshot(path=str(ROOT / 'preview-conflict-evidence.png'), full_page=True)
        await page.set_viewport_size({'width':390,'height':844})
        await page.screenshot(path=str(ROOT / 'preview-v03-mobile.png'), full_page=True)
        assert not errors, f'Unexpected JS exceptions: {errors}' 
        print(json.dumps({'browser_smoke':'passed', 'verified':['sample analysis','citation inspector','SQLite review persistence','dealflow navigation','mobile nav','30-deck evaluation lab','filter and failure inspection','conflicting traction and cited evidence','actual pipeline trace rendered with four stages'], 'errors':errors}, indent=2))
        await client.aclose()
        await browser.close()

if __name__=='__main__':
    asyncio.run(main_test())
