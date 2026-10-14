# Venture Intelligence v0.5 — From PDF to a verifiable human-review briefing

> **Great ideas deserve a chance to be understood.** An independent engineering portfolio exercise, not an HTGF application or investment recommendation tool.

**This is the real local full-stack prototype**, distinct from the [static public 90-second case-study showcase](https://mikelninh.github.io/venture-intelligence/?demo=investigation).

[![Python & LangGraph CI](https://github.com/mikelninh/venture-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/mikelninh/venture-intelligence/actions/workflows/ci.yml)

**Independent GitHub Actions verification — 14 October 2026:** [20 Python tests passed](https://github.com/mikelninh/venture-intelligence/actions/runs/38544624819) using the **real LangGraph 1.2.15 package** with `VI_WORKFLOW_ENGINE=langgraph`. Frontend JavaScript syntax checking also passed. This complements the earlier offline verification (19 passed / 1 skipped when LangGraph was unavailable); it does not establish production reliability or real-world extraction accuracy.

## Try it in 2 minutes

**Windows:** download the zip, extract it, run `start_windows.bat` (Python 3.11+; initial dependency install needs internet).

**macOS/Linux:** `./start_macos_linux.sh`

**Docker:** `docker compose up --build` (only binds to 127.0.0.1:8000).

Open **http://localhost:8000**. Choose **NovaSense Robotics**, then **Evidence library**, **Workflow trace** and **Human review**. Open the original synthetic PDF using the trace-panel link. No external AI key is needed.

On an online machine, startup scripts install **the real LangGraph package** via `backend/requirements-agent.txt` and use its compiled `StateGraph` (engine name visible in the UI). This execution environment could not install it due to restricted package network access; the offline fallback used for validation is labelled `local-sequential`, not LangGraph. To force Graph in development:

```bash
cd backend
python -m pip install -r requirements-agent.txt
VI_WORKFLOW_ENGINE=langgraph python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Exactly what works

- **Actual PDF** upload (up to 8MB/40 text-layer pages) or one of three bundled fictional PDFs (HelioGrid, LumaBio, NovaSense).
- **Four executable steps:** ingest PDF → extract explicit claims → verify every accepted source → require human review.
- **Verbatim source citations:** page and line reference and exact quote. No unsupported assertion passes the verifier.
- **Conflict handling:** NovaSense reports *8* and *80* paying customers: `traction.status=conflict`, `value=null`, two source IDs preserved, due-diligence question added.
- **Visible execution trace** inside the app, and via `GET /api/deals/{id}/trace`, including durations, status and counts.
- **Persisted human review** in local SQLite; Markdown memo export, evidence browser, and searchable case list.
- **Evaluation Lab** re-computes all 30 completely synthetic PDFs locally, with source-link validation, missing-field abstention and conflict checks.

## Measured, not guessed

| Synthetic gold set, same 30 decks | v0.3 baseline | v0.5 current |
|---|---:|---:|
| Exact fields | 505 / 510 | 510 / 510 |
| Expected missing → correctly absent | 95 / 95 | 95 / 95 |
| Conflicting traction fields abstained | 5 / 5 | 5 / 5 |
| Unsupported accepted citations | 0 | 0 |

**Critical limit:** the 5-field increase came from seeing the failure mode and adding support for `Founding crew ·` in the *same* constructed fixtures. This is in-sample error correction, not evidence of generalisation to real startup decks. See `docs/evaluation_comparison.json` and `docs/ARCHITECTURE.md`.

## Tests / reproducibility

```bash
cd backend
python -m pip install -r requirements-agent.txt -r requirements-dev.txt
python -m pytest -q
# From repository root:
python scripts/smoke_browser.py  # requires Playwright + Chromium, local only
node --check frontend/standalone/app.js
```

**Note:** `backend/evals/generate_golden.py` is fixture-authoring code; it is deliberately NOT run as part of CI, so a test run cannot quietly rewrite the expected answers. Regenerate gold labels only as a reviewed dataset change.

**Release verification here:** 19 backend tests passed, 1 actual LangGraph test skipped because dependency could not be fetched, and a complete Chromium browser smoke passed including review persistence, contradiction, citation inspector, Evaluation Lab, mobile view and actual trace tab. See `docs/VERIFICATION.md` for exact scope.

## Graph and observability

The graph uses the actual `langgraph.graph.StateGraph` implementation when installed. **We do not claim successful runtime execution of LangGraph in this sandbox.** The GitHub Actions CI file installs and tests the real package on Python 3.12. Optional Langfuse v3 spans are behind two opt-ins (install `requirements-observability.txt`, set `VI_LANGFUSE_ENABLED=1` and provide keys). This integration is not verified locally; remote telemetry is off by default.

## Security and boundaries

All companies and claims in bundled PDFs are **fictional**. Uploaded PDFs should be *non-confidential* only. This demo has no login, multi-tenant controls, malware scanning or secure retention; **never host the upload API publicly**. It never performs autonomous investments, ranks founders, automatically emails anyone, or validates external claims. Parsed text and review notes persist in local SQLite; the original uploaded PDF is not retained. Public GitHub Pages version runs as a separate static showcase with precomputed synthetic cases.

Technologies: **Python · FastAPI · Pydantic · PyMuPDF · LangGraph (optional installed engine) · SQLite · HTML/CSS/JS · pytest · Playwright**.

## Possible next product iteration (not implemented)

[Product hypothesis: Venture Pulse](docs/PRODUCT_ROADMAP.md) explores whether tracking a few public companies/technologies and producing an evidence-linked, actionable change brief provides real user value. We will validate the need before treating daily usage as the goal.
