from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

FactKey = Literal['company','tagline','sector','headquarters','founded','stage','funding_sought','problem','solution','product','traction','business_model','market','team','competition','risks','use_of_funds']

class Source(BaseModel):
    id: str
    page: int
    text: str

class Fact(BaseModel):
    value: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    status: Literal['supported','missing','conflict'] = 'missing'

class Insight(BaseModel):
    title: str
    description: str
    evidence_ids: list[str] = Field(default_factory=list)
    kind: Literal['positive','caution','neutral'] = 'neutral'

class Question(BaseModel):
    question: str
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)

class Review(BaseModel):
    status: Literal['pending','reviewed'] = 'pending'
    notes: str = ''
    updated_at: datetime | None = None

class TraceStep(BaseModel):
    name: str
    status: Literal['ok','blocked','error']
    duration_ms: float = 0
    details: dict[str, str | int | bool | float] = Field(default_factory=dict)

class Deal(BaseModel):
    id: str
    created_at: datetime
    filename: str
    demo: bool = False
    analysis_mode: Literal['evidence-first','llm-assisted'] = 'evidence-first'
    name: str
    narrative: str
    facts: dict[str, Fact]
    insights: list[Insight]
    questions: list[Question]
    sources: list[Source]
    page_count: int
    evidence_coverage: int
    supported_facts: int
    total_facts: int
    warnings: list[str] = Field(default_factory=list)
    review: Review = Field(default_factory=Review)
    trace: list[TraceStep] = Field(default_factory=list)
    workflow_engine: str = "legacy"
    requires_human_review: bool = True

class ReviewRequest(BaseModel):
    status: Literal['pending','reviewed']
    notes: str = Field(default='', max_length=4000)

class DealListItem(BaseModel):
    id: str
    name: str
    created_at: datetime
    filename: str
    demo: bool
    stage: str | None
    sector: str | None
    review_status: Literal['pending','reviewed']
    evidence_coverage: int
