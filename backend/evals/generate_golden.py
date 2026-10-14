"""Deterministic, wholly fictional evaluation PDFs and independent expected labels.
No investor data or personally identifiable information. Seed and cases are fixed.
"""
from __future__ import annotations
import json
from pathlib import Path
import fitz

ROOT=Path(__file__).parent
FIELDS=['company','tagline','sector','headquarters','founded','stage','funding_sought','problem','solution','product','traction','business_model','market','team','competition','risks','use_of_funds']
LABELS={'company':'Company','tagline':'Tagline','sector':'Sector','headquarters':'Headquarters','founded':'Founded','stage':'Stage','funding_sought':'Funding sought','problem':'Problem','solution':'Solution','product':'Product','traction':'Traction','business_model':'Business model','market':'Market','team':'Team','competition':'Competition','risks':'Risks','use_of_funds':'Use of funds'}
SCENARIOS=['complete','missing','two_line','synonym','conflicting','unlabelled']

def generate():
    folder=ROOT/'fixtures'; folder.mkdir(parents=True,exist_ok=True)
    gold=[]
    for i in range(30):
        scenario=SCENARIOS[i%len(SCENARIOS)]
        values={
            'company':f'Fable Venture {i+1:02d}', 'tagline':f'Useful infrastructure for sector {i%4+1}',
            'sector':['Climate Tech','Digital Health','Industrial AI','Cybersecurity'][i%4],
            'headquarters':['Berlin','Munich','Hamburg'][i%3], 'founded':str(2023+i%3),
            'stage':'Seed' if i%2 else 'Pre-seed', 'funding_sought':f'EUR {1+i%3} million',
            'problem':f'Manual reconciliation takes {7+i} hours each week',
            'solution':f'Workflow automation for specialised operators {i}',
            'product':f'Web platform edition {i+1}',
            'traction':f'{8+i} signed pilot agreements, founder-reported',
            'business_model':'Annual B2B licences',
            'market':f'Estimated EUR {20+i} million segment (unverified)',
            'team':f'Two fictional cofounders from cohort {i}',
            'competition':f'Legacy manual tools in sector {i%4}',
            'risks':'Procurement and data quality',
            'use_of_funds':'50 percent development, 50 percent pilots'
        }
        if scenario=='complete': keys=FIELDS[:]
        elif scenario=='missing': keys=[k for k in FIELDS if k not in ('traction','risks','competition','team')]
        elif scenario=='two_line': keys=[k for k in FIELDS if k not in ('market','product')]
        elif scenario=='synonym': keys=[k for k in FIELDS if k not in ('funding_sought','founded')]
        elif scenario=='conflicting': keys=FIELDS[:]
        else: keys=['company','tagline','sector','solution','stage','problem','team']
        expected={k:values[k] if k in keys else None for k in FIELDS}
        if scenario=='conflicting': expected['traction']=None # ambiguity MUST trigger abstention
        if scenario=='unlabelled': expected['team']=values['team'] # intentionally hard to recover
        doc=fitz.open()
        page=doc.new_page(width=595,height=842)
        page.insert_text((42,50),f'SYNTHETIC PITCH DECK  /  CASE {i+1:02d}',fontsize=14)
        lines=['This is invented evaluation content, not a genuine startup application.','']
        for k in keys:
            if scenario=='unlabelled' and k=='team':
                lines.append(f'Founding crew — {values[k]}') # not a recognised field label
            elif scenario=='two_line' and k in ('company','sector','traction','business_model'):
                lines.extend([LABELS[k],values[k]])
            elif scenario=='synonym' and k in ('company','headquarters','stage'):
                label={'company':'Startup','headquarters':'HQ','stage':'Funding stage'}[k]
                lines.append(f'{label}: {values[k]}')
            else: lines.append(f'{LABELS[k]}: {values[k]}')
            if scenario=='conflicting' and k=='traction': lines.append('Traction: 999 customers, contradictory founder claim')
        lines.extend(['','Numbers shown are claims by fictional founders, not independent facts.'])
        y=85
        for line in lines:
            if line: page.insert_text((42,y),line,fontsize=10.5)
            y+=20
        filename=f'case_{i+1:02d}_{scenario}.pdf'
        doc.save(str(folder/filename),deflate=True);doc.close()
        gold.append({'id':f'CASE-{i+1:02d}','scenario':scenario,'file':filename,'expected':expected,'why':{'conflicting':'Two incompatible traction claims; safe system should abstain','unlabelled':'Human-readable team detail uses a label unseen by strict baseline','missing':'Explicitly omitted fields should remain missing','two_line':'Split labels and values test layout robustness','synonym':'Alias labels test extraction coverage','complete':'Complete structured baseline case'}[scenario]})
    (ROOT/'gold.json').write_text(json.dumps({'version':'gold-v1','origin':'fully synthetic','cases':gold},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Generated {len(gold)} labelled evaluation PDFs.')
if __name__=='__main__':generate()
