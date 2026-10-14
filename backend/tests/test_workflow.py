"""Tests for a real PDF-to-citations-to-human-review workflow."""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import app.main as main
from app.db import Store
from app.workflow import execute, actual_engine, WorkflowError, verify, langgraph_available
from app.models import Source, Fact

DEMO=Path(__file__).resolve().parents[1]/'demo'

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('VI_WORKFLOW_ENGINE','local')
    monkeypatch.setattr(main, 'store', Store(str(tmp_path/'test.db')))
    return TestClient(main.app)

@pytest.mark.parametrize('slug', ['heliogrid','lumabio','novasense'])
def test_actual_pdf_through_api_and_provenance(client, slug):
    payload=(DEMO/f'{slug}.pdf').read_bytes()
    resp=client.post('/api/deals/upload',files={'file':(f'{slug}.pdf',payload,'application/pdf')})
    assert resp.status_code==201, resp.text
    d=resp.json()
    assert d['workflow_engine']=='local-sequential'
    assert [x['name'] for x in d['trace']]==['ingest','extract','verify','review_checkpoint']
    assert d['requires_human_review'] is True
    assert d['review']['status']=='pending'
    sources={x['id']:x for x in d['sources']}
    for field in d['facts'].values():
        if field['status']=='supported':
            assert field['evidence_ids']
            assert field['value'].casefold() in ' '.join(sources[i]['text'] for i in field['evidence_ids']).casefold()
    trace=client.get(f"/api/deals/{d['id']}/trace").json()
    assert trace['human_review_required'] is True
    assert trace['no_autonomous_investment_decisions'] is True
    assert trace['steps'][2]['details']['citations_rejected']==0
    if slug=='novasense':
        assert d['facts']['traction']['status']=='conflict'
        assert d['facts']['traction']['value'] is None
        assert len(d['facts']['traction']['evidence_ids']) >= 2
        assert any('correct' in q['question'] for q in d['questions'])
    elif slug=='lumabio':
        assert d['facts']['competition']['status']=='missing'
    else:
        assert d['facts']['traction']['status']=='supported'
    human=client.patch(f"/api/deals/{d['id']}/review",json={'status':'reviewed','notes':'Check source evidence manually.'})
    assert human.status_code==200 and human.json()['review']['status']=='reviewed'
    assert client.get(f"/api/deals/{d['id']}").json()['trace']==d['trace']


def test_verifier_rejects_fabricated_value():
    d=execute((DEMO/'heliogrid.pdf').read_bytes(),'heliogrid.pdf',preference='local')
    d.facts['traction'].value='500 billion ARR — invented'
    with pytest.raises(WorkflowError,match='absent from source'):
        verify({'deal':d,'trace':[]})


def test_verifier_rejects_fake_citation():
    d=execute((DEMO/'heliogrid.pdf').read_bytes(),'heliogrid.pdf',preference='local')
    d.facts['team'].evidence_ids=['p999-l999']
    with pytest.raises(WorkflowError,match='unknown citation'):
        verify({'deal':d,'trace':[]})


def test_bad_engine_fails_loudly(monkeypatch):
    monkeypatch.setenv('VI_WORKFLOW_ENGINE','anything')
    with pytest.raises(WorkflowError,match='must be auto'):
        actual_engine()


def test_actual_langgraph_pipeline_when_available():
    pytest.importorskip('langgraph')
    assert langgraph_available()
    d=execute((DEMO/'novasense.pdf').read_bytes(),'novasense.pdf',preference='langgraph')
    assert d.workflow_engine=='langgraph'
    assert [t.name for t in d.trace]==['ingest','extract','verify','review_checkpoint']
    assert d.facts['traction'].status=='conflict'
