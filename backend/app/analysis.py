"""Conservative v0.3 baseline. No LLM guesses; all positive assertions cite text blocks.

This is intentionally NOT a VC investment scoring algorithm. It indexes explicit labelled
information found in PDF text layers, and abstains when information is missing.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import re
import fitz
from .models import Deal, Fact, Insight, Question, Source

MAX_PAGES = 40
MAX_BYTES = 8 * 1024 * 1024
MAX_CHARS = 120_000

# Explicit labels keep the baseline auditable; arbitrary prose is left for manual review.
ALIASES = {
    'company': ['company', 'startup', 'company name'],
    'tagline': ['tagline', 'one-liner', 'mission'],
    'sector': ['sector', 'industry'],
    'headquarters': ['headquarters', 'hq', 'location', 'based in'],
    'founded': ['founded', 'year founded'],
    'stage': ['stage', 'funding stage'],
    'funding_sought': ['funding sought', 'round size', 'fundraise', 'raising'],
    'problem': ['problem'],
    'solution': ['solution'],
    'product': ['product'],
    'traction': ['traction', 'key metrics'],
    'business_model': ['business model', 'revenue model'],
    'market': ['market', 'market opportunity'],
    'team': ['team', 'founders', 'founding crew'],
    'competition': ['competition', 'competitors'],
    'risks': ['risks', 'known risks', 'challenges'],
    'use_of_funds': ['use of funds', 'capital allocation'],
}
ALL_KEYS = list(ALIASES)
MATCHERS = sorted([(key, alias) for key, aliases in ALIASES.items() for alias in aliases], key=lambda x: -len(x[1]))

class AnalysisError(ValueError):
    pass


def extract_sources(pdf_bytes: bytes) -> tuple[list[Source], int]:
    if len(pdf_bytes) > MAX_BYTES:
        raise AnalysisError('The file exceeds 8 MB. Please upload a smaller PDF.')
    if not pdf_bytes.startswith(b'%PDF-'):
        raise AnalysisError('This is not a valid PDF file.')
    try:
        with fitz.open(stream=pdf_bytes, filetype='pdf') as doc:
            if doc.needs_pass:
                raise AnalysisError('Password-protected PDFs are not supported in v0.3.')
            if doc.page_count < 1 or doc.page_count > MAX_PAGES:
                raise AnalysisError('Please use a PDF with 1–40 pages.')
            page_count = doc.page_count
            sources: list[Source] = []
            char_count = 0
            for i, page in enumerate(doc):
                raw = page.get_text('text', sort=True)
                char_count += len(raw)
                if char_count > MAX_CHARS:
                    raise AnalysisError('This PDF has too much text for v0.3 (120,000 character limit).')
                # Keep each source tied to a real extracted line: no model-invented quotations.
                for line_no, raw_line in enumerate(raw.splitlines(), 1):
                    line = re.sub(r'\s+', ' ', raw_line).strip()
                    if len(line) >= 4:
                        sources.append(Source(id=f'p{i+1}-l{line_no}', page=i+1, text=line[:1000]))
    except (fitz.FileDataError, fitz.FileNotFoundError) as e:
        raise AnalysisError('The PDF could not be read or is damaged.') from e
    if len(sources) < 3:
        raise AnalysisError('No usable text layer found. Scanned/image-only PDFs require OCR, which is not included in v0.3.')
    return sources, page_count


def _field_from_source(src: Source) -> tuple[str, str] | None:
    line = src.text
    for key, alias in MATCHERS:
        m = re.match(r'^\s*' + re.escape(alias) + r'\s*[:：–—·-]\s*(.+)$', line, re.IGNORECASE)
        if m:
            val = m.group(1).strip().strip('•')
            if len(val) > 1:
                return key, val[:500]
    return None


def analyze_pdf(pdf_bytes: bytes, filename: str, demo: bool = False, enrichment: dict[str, Fact] | None = None) -> Deal:
    sources, page_count = extract_sources(pdf_bytes)
    return analyze_sources(sources, page_count, filename, demo=demo, enrichment=enrichment)

def analyze_sources(sources: list[Source], page_count: int, filename: str, demo: bool = False, enrichment: dict[str, Fact] | None = None) -> Deal:
    """Pure extraction from already indexed PDF text. Suitable for a graph node."""
    facts = {key: Fact() for key in ALL_KEYS}
    candidate_values: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)
    for idx, source in enumerate(sources):
        extracted = _field_from_source(source)
        evidence_ids = [source.id]
        if extracted is None:
            # Layouts frequently put a heading on its own line. Only the immediately
            # following source line on the same page can serve as its value.
            matched = next((key for key, aliases in ALIASES.items()
                            if source.text.strip().lower().rstrip(':') in aliases), None)
            if matched and idx + 1 < len(sources) and sources[idx + 1].page == source.page:
                nxt = sources[idx + 1]
                # Never treat a different field heading as a field's value.
                if not any(nxt.text.strip().lower().rstrip(':') in a for a in ALIASES.values()):
                    extracted = (matched, nxt.text[:500])
                    evidence_ids = [source.id, nxt.id]
        if extracted:
            key, value = extracted
            candidate_values[key].append((value, evidence_ids))
    for key, candidates in candidate_values.items():
        # Two non-identical claims under the same explicit field label are ambiguity,
        # not evidence to silently pick whichever line came first.
        unique = {re.sub(r'\s+', ' ', val).strip().casefold() for val, _ in candidates}
        if len(unique) > 1:
            all_ids = list(dict.fromkeys(e for _, ids in candidates for e in ids))
            facts[key] = Fact(value=None, evidence_ids=all_ids, status='conflict')
        else:
            value, evidence_ids = candidates[0]
            facts[key] = Fact(value=value, evidence_ids=evidence_ids, status='supported')
    if enrichment:
        by_id = {src.id: src for src in sources}
        for key, candidate in enrichment.items():
            # Never overwrite an explicit baseline value, and double-check all spans.
            if key in facts and facts[key].status == 'missing' and candidate.evidence_ids and candidate.value:
                src = by_id.get(candidate.evidence_ids[0])
                if src and re.sub(r'\s+', ' ', candidate.value).strip().casefold() in re.sub(r'\s+', ' ', src.text).casefold():
                    facts[key] = candidate
    # Avoid making up the company from a title, filename or label that wasn't parsed.
    name = facts['company'].value or 'Unnamed startup'
    supported = sum(1 for fact in facts.values() if fact.status == 'supported')
    coverage = round(100 * supported / len(ALL_KEYS))
    def mk_insight(key: str, title: str, kind: str = 'neutral'):
        fact = facts[key]
        if fact.status == 'supported':
            return Insight(title=title, description=fact.value or '', evidence_ids=fact.evidence_ids, kind=kind)
        return None
    insights = [
        mk_insight('solution', 'Proposed solution', 'positive'),
        mk_insight('traction', 'Reported traction', 'positive'),
        mk_insight('business_model', 'Business model', 'neutral'),
        mk_insight('risks', 'Risks stated in the deck', 'caution'),
    ]
    insights = [i for i in insights if i is not None]
    questions: list[Question] = []
    if facts['traction'].status == 'conflict':
        questions.append(Question(question='Which traction figure is correct, and what primary evidence reconciles the discrepancy?', reason='The deck reports contradictory traction figures; no value has been accepted.', evidence_ids=facts['traction'].evidence_ids))
    elif facts['traction'].status == 'supported':
        questions.append(Question(question='What primary evidence supports the reported traction?', reason='The deck reports traction, but the figures have not been independently verified.', evidence_ids=facts['traction'].evidence_ids))
    else:
        questions.append(Question(question='What traction and customer validation can the founders document?', reason='No explicitly labelled traction figure was found in the document.'))
    if facts['competition'].status == 'missing':
        questions.append(Question(question='Who are the closest competitors, and what is the defensible advantage?', reason='No explicit competitive analysis was identified.'))
    if facts['risks'].status == 'missing':
        questions.append(Question(question='What are the top commercial, technical and regulatory risks?', reason='The deck does not explicitly identify risks.'))
    if facts['use_of_funds'].status == 'missing':
        questions.append(Question(question='How will the requested capital be allocated across milestones?', reason='No use-of-funds breakdown was identified.'))
    if facts['team'].status == 'missing':
        questions.append(Question(question='Who are the founders, and what is their relevant track record?', reason='No explicitly labelled team information was identified.'))
    if facts['market'].status == 'supported':
        questions.append(Question(question='Which assumptions underpin the market estimate?', reason='Market claims require external corroboration.', evidence_ids=facts['market'].evidence_ids))
    else:
        questions.append(Question(question='How large is the addressable market and how was it estimated?', reason='No explicitly labelled market information was found.'))
    # Keep the narrative verbatim rather than pretending the baseline synthesises like an LLM.
    if facts['tagline'].status == 'supported':
        narrative = facts['tagline'].value or ''
    elif facts['solution'].status == 'supported':
        narrative = facts['solution'].value or ''
    else:
        narrative = 'Not enough labelled evidence to describe the startup. Manual review required.'
    warnings = ['Information is extracted from applicant-supplied documents and has not been independently verified.']
    for key, fact in facts.items():
        if fact.status == 'conflict':
            warnings.append(f'Conflicting statements for {key.replace("_", " ")}; human review required. No value was selected.')
    if supported <= 3:
        warnings.append('Low extraction coverage. This PDF may lack labelled sections; read the source manually.')
    return Deal(
        id=str(uuid4()), created_at=datetime.now(timezone.utc), filename=filename, demo=demo,
        analysis_mode='llm-assisted' if enrichment is not None else 'evidence-first',
        name=name, narrative=narrative, facts=facts, insights=insights,
        questions=questions[:6], sources=sources, page_count=page_count,
        evidence_coverage=coverage, supported_facts=supported, total_facts=len(ALL_KEYS), warnings=warnings,
    )


def deal_to_markdown(deal: Deal) -> str:
    sources = {source.id: source for source in deal.sources}
    def cites(ids: list[str]) -> str:
        return ', '.join(f'p.{sources[i].page} ({i})' for i in ids if i in sources) or 'No source provided'
    lines = [f'# {deal.name} — Evidence-first briefing', '',
             f'> Review status: {deal.review.status}. Document: {deal.filename}. Generated: {deal.created_at.date().isoformat()}.', '',
             '**Not investment advice. Founder-submitted claims are unverified.**', '',
             '## Snapshot', '']
    for key, fact in deal.facts.items():
        lines.append(f'- **{key.replace("_", " ").title()}**: {fact.value or "Not provided"} ({cites(fact.evidence_ids)})')
    lines += ['', '## Signals', '']
    for ins in deal.insights:
        lines.append(f'- **{ins.title}:** {ins.description} ({cites(ins.evidence_ids)})')
    lines += ['', '## Questions for investment team', '']
    for q in deal.questions:
        lines.append(f'- **{q.question}** {q.reason} ({cites(q.evidence_ids)})')
    lines += ['', '## Limitations', '']
    lines += [f'- {warning}' for warning in deal.warnings]
    lines += ['', '## Human review', '', f'- Status: {deal.review.status}', f'- Notes: {deal.review.notes or "None"}', '']
    return '\n'.join(lines)
