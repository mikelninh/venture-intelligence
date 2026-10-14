"""Reproducible 30-deck synthetic baseline evaluation. No investor data or network."""
from __future__ import annotations
import json
import time
from pathlib import Path
from .analysis import analyze_pdf

ROOT=Path(__file__).resolve().parents[1]/'evals'

def run_baseline() -> dict:
    gold=json.loads((ROOT/'gold.json').read_text(encoding='utf-8'))
    total=correct=expected_present=present_matched=unsupported=abstain_total=abstain_correct=conflict_correct=0
    cases=[]
    for case in gold['cases']:
        begin=time.perf_counter()
        deal=analyze_pdf((ROOT/'fixtures'/case['file']).read_bytes(),case['file'],demo=True)
        index={s.id:s for s in deal.sources}
        errors=[]
        for key,wanted in case['expected'].items():
            f=deal.facts[key]
            actual=f.value if f.status=='supported' else None
            total+=1
            correct+= actual==wanted
            expected_present+=wanted is not None
            present_matched+= wanted is not None and actual==wanted
            if wanted is None:
                abstain_total+=1
                abstain_correct+= actual is None
            if f.status=='supported' and (not f.evidence_ids or not all(e in index for e in f.evidence_ids) or not any(actual in index[e].text for e in f.evidence_ids)):
                unsupported+=1
            if actual!=wanted:
                errors.append({'field':key,'expected':wanted,'actual':actual,'type':'missing' if actual is None else 'incorrect'})
        is_conflicting=case['scenario']=='conflicting'
        if is_conflicting and deal.facts['traction'].status=='conflict': conflict_correct+=1
        cases.append({'id':case['id'],'scenario':case['scenario'],'file':case['file'],
            'correct':17-len(errors),'total':17,'errors':errors,
            'conflict_detected': bool(is_conflicting and deal.facts['traction'].status=='conflict'),
            'elapsed_ms':round((time.perf_counter()-begin)*1000,1),
            'narrative':case['why']})
    return {'version':'eval-v1', 'dataset':'30 synthetic labelled decks, 6 scenario types', 'gold_version':gold['version'],
        'note':'Field-level exact-match evaluation against deliberately synthetic labels; NOT model confidence, investment quality or external validation.',
        'metrics':{'cases':len(cases),'fields':total,'exact_match_correct':correct,
            'exact_match_pct':round(100*correct/total,1),
            'expected_present':expected_present,'correct_present':present_matched,
            'retrieval_of_expected_pct':round(100*present_matched/expected_present,1),
            'required_abstentions':abstain_total,'correct_abstentions':abstain_correct,
            'abstention_pct':round(100*abstain_correct/abstain_total,1),
            'unsupported_source_links':unsupported,'contradictions_detected':conflict_correct,'contradiction_cases':5},
        'cases':cases}
