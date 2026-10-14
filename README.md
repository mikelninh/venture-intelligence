# Venture Intelligence · Evidence-first AI Engineering

**From early ideas to better questions.** An independent application project for an AI-engineering role in venture capital, built with Python, FastAPI, Pydantic and LangGraph. Not affiliated with HTGF.

### Start here — 2 minutes for a reviewer

| Experience | What to inspect |
|---|---|
| **[90-second interactive investigation ↗](https://mikelninh.github.io/venture-intelligence/?demo=investigation)** | NovaSense fictional case: two conflicting customer claims, clickable sources, human decision |
| **[Complete PDF workflow in this repository ↗](backend/app/workflow.py)** | Real local PDF upload → extraction → citation verifier → explicit human review checkpoint |
| **[Independent-ish synthetic layout test ↗](docs/UNSEEN_EVALUATION.md)** | Why the first 30 synthetic decks gave 100%, but 12 differently written decks reveal only **75%** exact-field accuracy |
| **[Venture Pulse live daily brief ↗](https://mikelninh.github.io/venture-pulse/)** | Scheduled HTGF + EU-Startups RSS change detection; reported news, not confirmed startup events |
| **[Automated CI checks ↗](https://github.com/mikelninh/venture-intelligence/actions/workflows/ci.yml)** | Real LangGraph in CI, regression suite, frozen new-layout benchmark, JavaScript syntax |

### Engineering decisions that matter

- **Evidence is not truth.** All accepted values link to exact extracted PDF text; cited founder claims can still be wrong.
- **Abstain on contradictions.** If one PDF says 8 customers and another line says 80, neither figure is silently accepted.
- **Keep authority with people.** A human must review. No funding decisions or external outreach are automated.
- **Measure failure honestly.** Previous in-sample test set: 510/510 after a targeted fix; varied-layout stress test: **54/72**, with 18 misses on prose-first decks. Both sets are synthetic, not a production accuracy claim.
- **Separate systems.** Venture Intelligence processes PDFs locally; the public website is a safe static guided case study. Venture Pulse is deterministic daily RSS processing, **not** an LLM research agent.

### What I would improve next

Context-aware candidate extraction for natural-language slides **with a deterministic citation verifier**, measured on a new human-labelled set. Then real user feedback from investment analysts and accountable deployment controls. I would rather explain one real failure clearly than market a prototype as production-ready.

---

## New in v0.6: Venture Pulse

**[Open the live daily brief →](https://mikelninh.github.io/venture-pulse/)**

A quiet, source-linked public startup research assistant: HTGF + EU-Startups RSS, daily scheduled change detection, topic filtering, three highest-priority signals, a human verification step, and browser-local feedback.

**[Engineering note & measured limitations](docs/VENTURE_PULSE.md)** · **[Live GitHub Actions](https://github.com/mikelninh/venture-intelligence/actions/workflows/venture-pulse.yml)** · **[Read the snapshot](data/pulse/latest.json)**

The first collection records a reference **baseline**, not new news. The collector identifies article updates—not verified business events—and uses deterministic heuristics, not autonomous LLM analysis.

---

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

## The Venture Pulse extension

[Venture Pulse is implemented as a public daily RSS collector](docs/VENTURE_PULSE.md). It remains deterministic and does not yet validate human usefulness or operate as an autonomous agent.
