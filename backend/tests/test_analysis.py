import io
from pathlib import Path
import pytest
import fitz
from reportlab.pdfgen import canvas
from app.analysis import analyze_pdf, extract_sources, AnalysisError, deal_to_markdown

DEMO = Path(__file__).resolve().parents[1] / 'demo'

def test_full_demo_is_grounded():
    d = analyze_pdf((DEMO/'heliogrid.pdf').read_bytes(), 'heliogrid.pdf', True)
    assert d.name == 'HelioGrid AI'
    assert d.supported_facts == d.total_facts == 17
    assert d.evidence_coverage == 100
    assert d.facts['traction'].value.startswith('11 pilots')
    source_index = {s.id: s for s in d.sources}
    for f in d.facts.values():
        if f.status == 'supported':
            assert f.value is not None
            assert f.evidence_ids
            assert f.value in [source_index[e].text for e in f.evidence_ids]
    assert all(any(id in source_index for id in ins.evidence_ids) for ins in d.insights)

def test_missing_details_are_not_fabricated():
    d = analyze_pdf((DEMO/'lumabio.pdf').read_bytes(), 'lumabio.pdf', True)
    assert d.name == 'LumaBio Diagnostics'
    assert d.evidence_coverage < 100
    assert d.facts['competition'].value is None
    assert d.facts['use_of_funds'].status == 'missing'
    assert any('competitors' in q.question.lower() for q in d.questions)

def test_inline_labels_are_recognised():
    buff = io.BytesIO(); c = canvas.Canvas(buff)
    for line in ['Company: Test Labs', 'Sector: Applied Science', 'Headquarters: Munich', 'Problem: Expensive machines']:
        c.drawString(45, 750-30*['Company: Test Labs', 'Sector: Applied Science', 'Headquarters: Munich', 'Problem: Expensive machines'].index(line), line)
    c.save()
    d = analyze_pdf(buff.getvalue(), 'inline.pdf')
    assert d.name == 'Test Labs'
    assert d.facts['sector'].value == 'Applied Science'
    assert d.facts['headquarters'].status == 'supported'

def test_invalid_documents_fail_explicitly():
    with pytest.raises(AnalysisError, match='valid PDF'):
        extract_sources(b'not a PDF')
    with pytest.raises(AnalysisError, match='8 MB'):
        extract_sources(b'%PDF-' + b'a' * (8*1024*1024))

def test_scanned_pdf_rejected():
    pdf = fitz.open(); pdf.new_page(); pdf.new_page(); payload = pdf.tobytes(); pdf.close()
    with pytest.raises(AnalysisError, match='No usable text layer'):
        extract_sources(payload)

def test_markdown_contains_citations_and_explicit_limits():
    d = analyze_pdf((DEMO/'heliogrid.pdf').read_bytes(), 'heliogrid.pdf')
    md = deal_to_markdown(d)
    assert 'p.2 (p2-l' in md
    assert 'not been independently verified' in md
    assert 'What primary evidence' in md

def test_optional_llm_candidates_are_verbatim_and_cited():
    from app.llm import validate_candidates
    from app.models import Source
    sources=[Source(id='p1-l1',page=1,text='Berlin team uses predictive software to reduce peak loads.')]
    candidates=[
        {'key':'headquarters','value':'Berlin','source_id':'p1-l1'},
        {'key':'traction','value':'EUR 700 million ARR','source_id':'p1-l1'},
        {'key':'stage','value':'Seed','source_id':'p9-l1'},
    ]
    f=validate_candidates(candidates,sources)
    assert list(f)==['headquarters']
    assert f['headquarters'].evidence_ids==['p1-l1']
