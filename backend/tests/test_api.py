from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import app.main as main
from app.db import Store

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main, 'store', Store(str(tmp_path/'test.db')))
    return TestClient(main.app)

def test_api_e2e_synthetic_and_review(client):
    assert client.get('/api/health').json()['status'] == 'ok'
    created = client.post('/api/deals/demo?slug=heliogrid')
    assert created.status_code == 201, created.text
    deal = created.json()
    id = deal['id']
    assert deal['name'] == 'HelioGrid AI'
    assert client.get('/api/deals').json()[0]['id'] == id
    assert client.get(f'/api/deals/{id}').json()['supported_facts'] == 17
    reviewed = client.patch(f'/api/deals/{id}/review',json={'status':'reviewed','notes':'Validate claimed recurring revenue.'})
    assert reviewed.status_code == 200
    assert client.get(f'/api/deals/{id}').json()['review']['notes'] == 'Validate claimed recurring revenue.'
    memo = client.get(f'/api/deals/{id}/memo.md')
    assert memo.status_code == 200
    assert 'Validate claimed recurring revenue' in memo.text
    assert 'filename=' in memo.headers['content-disposition']

def test_upload_and_validation(client):
    file = (Path(__file__).resolve().parents[1]/'demo'/'lumabio.pdf').read_bytes()
    res=client.post('/api/deals/upload', files={'file':('lumabio.pdf',file,'application/pdf')})
    assert res.status_code == 201
    assert res.json()['demo'] is False
    assert res.json()['facts']['competition']['status']=='missing'
    for name,body,expected in [('fake.txt',b'hello',415),('fake.pdf',b'hello',422)]:
        bad=client.post('/api/deals/upload',files={'file':(name,body,'application/pdf')})
        assert bad.status_code == expected
    assert client.get('/api/deals/not-a-real-id').status_code==404
    assert client.post('/api/deals/demo?slug=unknown').status_code==404
    pdf=client.get('/api/demo/heliogrid.pdf')
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF-')

def test_user_supplied_filename_is_normalised(client):
    file=(Path(__file__).resolve().parents[1]/'demo'/'lumabio.pdf').read_bytes()
    res=client.post('/api/deals/upload',files={'file':('../private/lumabio.pdf',file,'application/pdf')})
    assert res.status_code==201
    assert res.json()['filename']=='lumabio.pdf'
