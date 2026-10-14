from pathlib import Path
from fastapi.testclient import TestClient
from app.analysis import analyze_pdf
from app.evaluation import run_baseline
from app.main import app

DEMO=Path(__file__).resolve().parents[1]/'demo'

def test_conflicting_traction_abstains_and_cites_both_claims():
    d=analyze_pdf((DEMO/'novasense.pdf').read_bytes(),'novasense.pdf',True)
    f=d.facts['traction']
    assert f.status=='conflict' and f.value is None
    assert len(f.evidence_ids)>=2
    assert any('contradictory traction' in q.reason.lower() for q in d.questions)
    assert any('Conflicting statements' in warning for warning in d.warnings)

def test_baseline_gold_reproducible_and_grounded():
    r=run_baseline()
    m=r['metrics']
    assert m['cases']==30 and m['fields']==510
    assert m['unsupported_source_links']==0
    assert m['contradictions_detected']==m['contradiction_cases']==5
    assert m['required_abstentions']>0 and m['correct_abstentions']==m['required_abstentions']
    assert sum(c['correct'] for c in r['cases'])==m['exact_match_correct']

def test_new_endpoints_work():
    client=TestClient(app)
    assert client.get('/api/evals').json()['metrics']['cases']==30
    assert client.post('/api/deals/demo?slug=novasense').json()['facts']['traction']['status']=='conflict'
    assert client.get('/api/demo/novasense.pdf').content.startswith(b'%PDF-')
