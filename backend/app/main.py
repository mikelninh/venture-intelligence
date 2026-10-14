from __future__ import annotations
import os
import re
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from .analysis import analyze_pdf, extract_sources, AnalysisError, MAX_BYTES, deal_to_markdown
from .llm import llm_configured, extract_verbatim_facts, LLMError
from .db import Store
from .models import Deal, DealListItem, ReviewRequest
from .workflow import execute, actual_engine, WorkflowError
from .observability import publish_metadata_only

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv('VI_DATA_DIR', str(ROOT / 'data')))
store = Store(str(DATA_DIR / 'venture.db'))

app = FastAPI(title='Venture Intelligence v0.5', version='0.5.0', description='Evidence-first startup briefings from PDFs; synthetic demos and local persistence.')
app.add_middleware(CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv('VI_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')],
    allow_methods=['GET', 'POST', 'PATCH'], allow_headers=['Content-Type'])

@app.get('/api/health')
def health():
    return {'status': 'ok', 'version': '0.5.0', 'mode': 'evidence-first', 'llm_enabled': llm_configured(), 'workflow_engine': actual_engine(), 'remote_telemetry_enabled': os.getenv('VI_LANGFUSE_ENABLED')=='1'}

@app.get('/api/deals', response_model=list[DealListItem])
def list_deals():
    return store.list()

@app.post('/api/deals/demo', response_model=Deal, status_code=201)
async def demo_deal(slug: str = 'heliogrid', mode: str = 'evidence-first'):
    if slug not in ('heliogrid', 'lumabio', 'novasense'):
        raise HTTPException(status_code=404, detail='Unknown demo scenario.')
    path = ROOT / 'demo' / f'{slug}.pdf'
    if not path.is_file():
        raise HTTPException(status_code=500, detail='Demo PDF unavailable.')
    if mode not in ('evidence-first','llm-assisted'):
        raise HTTPException(status_code=422, detail='Invalid analysis mode.')
    pdf_bytes = path.read_bytes()
    try:
        enrichment = await extract_verbatim_facts(extract_sources(pdf_bytes)[0]) if mode == 'llm-assisted' else None
    except LLMError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    deal = execute(pdf_bytes, path.name, demo=True, enrichment=enrichment)
    publish_metadata_only(deal)
    store.put(deal)
    return deal

@app.post('/api/deals/upload', response_model=Deal, status_code=201)
async def upload_deal(file: UploadFile = File(...), mode: str = 'evidence-first'):
    filename = Path(file.filename or 'document.pdf').name
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=415, detail='Please upload a .pdf file.')
    payload = await file.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise HTTPException(status_code=413, detail='PDF exceeds the 8 MB upload limit.')
    if mode not in ('evidence-first','llm-assisted'):
        raise HTTPException(status_code=422, detail='Invalid analysis mode.')
    try:
        enrichment = await extract_verbatim_facts(extract_sources(payload)[0]) if mode == 'llm-assisted' else None
        deal = execute(payload, filename, enrichment=enrichment)
    except LLMError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except WorkflowError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    except AnalysisError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    publish_metadata_only(deal)
    store.put(deal)
    return deal

@app.get('/api/deals/{deal_id}', response_model=Deal)
def get_deal(deal_id: str):
    deal = store.get(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail='Deal not found.')
    return deal

@app.get('/api/deals/{deal_id}/trace')
def get_trace(deal_id: str):
    deal = store.get(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail='Deal not found.')
    return {'deal_id': deal.id, 'engine': deal.workflow_engine,
            'steps': [t.model_dump() for t in deal.trace],
            'human_review_required': deal.requires_human_review,
            'no_autonomous_investment_decisions': True}

@app.patch('/api/deals/{deal_id}/review', response_model=Deal)
def update_review(deal_id: str, request: ReviewRequest):
    from datetime import datetime, timezone
    deal = store.get(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail='Deal not found.')
    deal.review.status = request.status
    deal.review.notes = request.notes
    deal.review.updated_at = datetime.now(timezone.utc)
    store.put(deal)
    return deal

@app.get('/api/deals/{deal_id}/memo.md', response_class=PlainTextResponse)
def download_memo(deal_id: str):
    deal = store.get(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail='Deal not found.')
    return PlainTextResponse(deal_to_markdown(deal), media_type='text/markdown', headers={
        'Content-Disposition': f'attachment; filename="venture-briefing-{deal.id[:8]}.md"'
    })


@app.get('/api/evals')
def eval_report():
    from .evaluation import run_baseline
    return run_baseline()

@app.get('/api/demo/{slug}.pdf', include_in_schema=False)
def get_demo_pdf(slug: str):
    if slug not in ('heliogrid', 'lumabio', 'novasense'):
        raise HTTPException(status_code=404, detail='Unknown demo PDF.')
    path = ROOT / 'demo' / f'{slug}.pdf'
    return FileResponse(path, media_type='application/pdf', filename=f'{slug}-synthetic.pdf', content_disposition_type='inline')

# Default UI is the browser-tested, dependency-free analyst workspace.
# The old React/Vite proof of concept is archived under experiments/react-v01
# to avoid an out-of-sync compiled frontend silently overriding this release.
UI = ROOT.parent / 'frontend' / 'standalone'
@app.get('/', include_in_schema=False)
def index():
    return FileResponse(UI / 'index.html')
@app.get('/style.css', include_in_schema=False)
def styles():
    return FileResponse(UI / 'style.css', media_type='text/css')
@app.get('/app.js', include_in_schema=False)
def script():
    return FileResponse(UI / 'app.js', media_type='text/javascript')
