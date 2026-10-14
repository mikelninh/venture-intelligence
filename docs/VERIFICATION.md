## Independent CI verification (14 October 2026)

GitHub Actions run [#38544624819](https://github.com/mikelninh/venture-intelligence/actions/runs/38544624819) completed successfully on Ubuntu 24.04, Python 3.12, with `langgraph==1.2.15` installed and `VI_WORKFLOW_ENGINE=langgraph`. Result: **20 pytest tests passed**, including the actual LangGraph execution path. The Node.js frontend syntax step also passed.

These are synthetic regression tests, not production-level confidence measurements. The original isolated sandbox had 19 passes plus 1 skip; the CI run resolves that specific integration gap.

# Release verification — v0.5

## Confirmed in this execution environment

- 19 `pytest` checks passed; 1 `pytest.importorskip('langgraph')` integration test skipped (dependency unavailable).
- Real three-PDF API ingestion validated for HelioGrid, LumaBio and NovaSense; citation presence and exact verbatim containment checked; pending human review established and saved reviewer notes persisted.
- Adversarial verifier checks: fabricated field value rejected, non-existent citation ID rejected.
- Browser smoke verified actual FastAPI responses via ASGI transport + Chromium with the real static UI: PDF-derived briefings, citations, review state persistence, mobile navigation, synthetic eval filtering, NovaSense conflicting statements, and a four-stage displayed trace. No JavaScript page errors.
- 30-deck synthetic evaluation re-run after targeted `Founding crew ·` fix: 510/510 field decisions exact in the same known gold set. This is **NOT** a real-world quality measurement.

## Not verified here

- Real `langgraph` runtime: package installation failed because PyPI could not be reached in the container. Source includes a genuine `StateGraph`, forced engine selection and a conditionally-run integration test. CI on an online machine must pass before claiming LangGraph is tested.
- Langfuse remote spans: opt-in API integration is implemented but not connected, executed or independently verified.
- Docker image build: needs downloading packages. Local FastAPI ASGI tests passed.
- Uploaded real confidential investment PDFs or scanned/image-only PDFs: explicitly out of scope. No authenticated production deployment.

## 60-second engineer walkthrough

1. Load the NovaSense synthetic PDF through the API or choose its demo tile. It is parsed by PyMuPDF, not simulated.
2. Inspect conflicting traction lines on pages 2 and 3. The briefing refuses to accept either as truth.
3. Select **Workflow trace** and see ingest/extract/verify/review stages with execution times and source counts. The actual engine is labelled `langgraph` or `local-sequential`.
4. Inspect **Evaluation Lab**, the 30-case deterministic gold set and compare its results with the archived v0.3 baseline.
5. Mark a review and re-open it. Note that human approval records review, not verified commercial truth.
