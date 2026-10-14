"""Inspectable workflow for evidence-first deal analysis.

``VI_WORKFLOW_ENGINE=langgraph`` forces the real LangGraph StateGraph.
``auto`` explicitly reports a local sequential runner if dependency unavailable.
Both paths call the SAME bounded nodes; no model decisions or pretend agents.

Graph: ingest -> extract -> verify -> review_checkpoint -> END
All uploaded material remains local. Trace metadata never includes source text.
"""
from __future__ import annotations
import os
import time
from typing import Any, TypedDict
from .analysis import analyze_sources, extract_sources, AnalysisError
from .models import Deal, Source, Fact, TraceStep

STAGES = ("ingest", "extract", "verify", "review_checkpoint")

class WorkflowError(RuntimeError):
    pass

class State(TypedDict, total=False):
    pdf_bytes: bytes
    filename: str
    demo: bool
    enrichment: dict[str, Fact] | None
    sources: list[Source]
    page_count: int
    deal: Deal
    trace: list[TraceStep]
    blocked: bool


def _step(name: str, duration_ms: float, **details: str | int | bool | float) -> TraceStep:
    return TraceStep(name=name, status="ok", duration_ms=round(duration_ms, 2), details=details)


def ingest(state: State) -> dict[str, Any]:
    started = time.perf_counter()
    sources, pages = extract_sources(state["pdf_bytes"])
    return {"sources": sources, "page_count": pages,
            "trace": state.get("trace", []) + [_step("ingest", (time.perf_counter()-started)*1000,
                pages=pages, lines=len(sources), bytes=len(state["pdf_bytes"]))]}


def extract(state: State) -> dict[str, Any]:
    started = time.perf_counter()
    deal = analyze_sources(state["sources"], state["page_count"], state["filename"],
                           demo=state.get("demo", False), enrichment=state.get("enrichment"))
    return {"deal": deal, "trace": state.get("trace", []) + [_step("extract", (time.perf_counter()-started)*1000,
                supported=deal.supported_facts,
                conflicts=sum(f.status=="conflict" for f in deal.facts.values()),
                missing=sum(f.status=="missing" for f in deal.facts.values()))]}


def verify(state: State) -> dict[str, Any]:
    started = time.perf_counter()
    deal = state["deal"]
    index = {src.id: src for src in deal.sources}
    checked = 0
    for key, fact in deal.facts.items():
        if fact.status == 'supported':
            if not fact.value or not fact.evidence_ids:
                raise WorkflowError(f"Verification gate rejected field {key}: unsupported assertion")
            if any(id not in index for id in fact.evidence_ids):
                raise WorkflowError(f"Verification gate rejected field {key}: unknown citation")
            # Joined text permits heading/value pairs and deliberately does not allow invented values.
            if fact.value.casefold() not in ' '.join(index[i].text for i in fact.evidence_ids).casefold():
                raise WorkflowError(f"Verification gate rejected field {key}: value absent from source")
            checked += 1
        elif fact.status == 'conflict':
            if fact.value is not None or len(fact.evidence_ids) < 2 or any(i not in index for i in fact.evidence_ids):
                raise WorkflowError(f"Verification gate rejected field {key}: unsafe conflict handling")
        elif fact.status == 'missing' and fact.value is not None:
            raise WorkflowError(f"Verification gate rejected field {key}: invented missing value")
    return {"trace": state.get("trace", []) + [_step("verify", (time.perf_counter()-started)*1000,
                    citations_checked=checked, citations_rejected=0)]}


def review_checkpoint(state: State) -> dict[str, Any]:
    # No autonomous investment recommendations or consequential external actions.
    started = time.perf_counter()
    deal = state["deal"]
    deal.requires_human_review = True
    deal.review.status = "pending"
    return {"deal": deal, "trace": state.get("trace", []) + [_step("review_checkpoint", (time.perf_counter()-started)*1000,
                   human_approval_required=True, investment_action_taken=False)]}

NODES = {"ingest": ingest, "extract": extract, "verify": verify, "review_checkpoint": review_checkpoint}


def langgraph_available() -> bool:
    try:
        import langgraph.graph  # noqa
        return True
    except ImportError:
        return False


def _langgraph_run(state: State) -> State:
    # This is the real package, not a home-grown replacement named "LangGraph".
    from langgraph.graph import StateGraph, START, END
    graph = StateGraph(State)
    for name, fn in NODES.items():
        graph.add_node(name, fn)
    graph.add_edge(START, "ingest")
    for prev, nxt in zip(STAGES, STAGES[1:]):
        graph.add_edge(prev, nxt)
    graph.add_edge("review_checkpoint", END)
    return graph.compile().invoke(state)


def _local_run(state: State) -> State:
    # Explicit fallback for offline demos/tests. Never report it as LangGraph.
    for step in STAGES:
        state.update(NODES[step](state))
    return state


def actual_engine(preference: str | None = None) -> str:
    preference = preference or os.getenv('VI_WORKFLOW_ENGINE', 'auto')
    if preference not in ('auto', 'langgraph', 'local'):
        raise WorkflowError("VI_WORKFLOW_ENGINE must be auto, langgraph or local")
    if preference == 'langgraph':
        if not langgraph_available():
            raise WorkflowError("LangGraph was required but not installed. Install backend/requirements-agent.txt")
        return 'langgraph'
    if preference == 'auto' and langgraph_available():
        return 'langgraph'
    return 'local-sequential'


def execute(pdf_bytes: bytes, filename: str, *, demo: bool = False,
            enrichment: dict[str, Fact] | None = None, preference: str | None = None) -> Deal:
    engine = actual_engine(preference)
    initial: State = {"pdf_bytes": pdf_bytes, "filename": filename, "demo": demo,
                      "enrichment": enrichment, "trace": []}
    final = _langgraph_run(initial) if engine == 'langgraph' else _local_run(initial)
    deal = final['deal']
    deal.trace = final['trace']
    deal.workflow_engine = engine
    return deal
