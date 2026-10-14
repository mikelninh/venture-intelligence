# Venture Pulse v0.6 — daily public startup intelligence

**Product hypothesis:** A morning brief should help a researcher quickly answer *what changed, what is the original source, and what is worth checking next?*

**Live public dashboard:** https://mikelninh.github.io/venture-pulse/

## What is actually working

- Daily GitHub Actions pipeline at 07:30 UTC (08:30 CET / 09:30 CEST).
- Fetches public RSS feeds from HTGF News and EU-Startups.
- Parses RSS and Atom, normalises linked article URLs, and fingerprints title + excerpt.
- Preserves a persistent seen-article state in `data/pulse/state.json`.
- First successful collection is a **baseline**, never falsely presented as today's new discoveries.
- Subsequent collections report new or edited publisher articles; unchanged articles are not repeated.
- Prioritises watchlisted AI, climate, healthcare and early-stage funding signals.
- Shows **up to three** article changes, an original source link, and a useful next *human* verification step.
- When no relevant change exists, the brief is intentionally quiet.
- Public UI lets visitors filter topics and store their own review and relevance feedback **locally in their browser**.
- Source outages are indicated as partial failures. On total outage, the collector fails without overwriting previous state.

## Inspect

- Workflow: [daily GitHub Actions](https://github.com/mikelninh/venture-intelligence/actions/workflows/venture-pulse.yml)
- Detector: [backend/app/pulse.py](../backend/app/pulse.py)
- Tests: [backend/tests/test_pulse.py](../backend/tests/test_pulse.py)
- Published feed report: [latest.json](../data/pulse/latest.json)
- Original pitch-deck analyst: [Venture Intelligence](https://mikelninh.github.io/venture-intelligence/?demo=investigation)

## Run locally

```bash
python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
python -m pytest -q backend/tests/test_pulse.py
python -m backend.app.pulse --state data/pulse/state.json --output data/pulse/latest.json
uvicorn backend.app.main:app --reload
# http://127.0.0.1:8000/pulse
```

The CLI needs internet access to retrieve live feeds; offline tests use synthetic RSS fixtures.

## Truth and limits

This is scheduled deterministic retrieval and ranking, **not** an autonomous LLM researcher or a verification service for company claims. Article updates are **feed changes**, not proven changes in startups themselves.

Keyword ranking is intentionally transparent, not RAG or semantic company matching. It does not integrate private CRM, email, or investments, and does not automatically contact founders. The initial 3 articles come from a **baseline** of public source feeds. Changing or updating a feed item does not independently substantiate its content.

The first independent GitHub Actions collection on 14 October 2026 succeeded on both sources and stored 20 linked articles as baseline. Claims about improved analyst productivity or return usage remain *unvalidated hypotheses*.

## Next measurable milestone

Recruit five opt-in pilot users. Over seven days, record: percent of useful signals, time to reach one verified next action, false positives, user-requested missing signals and whether people return *because the information was useful*. Make no production reliability claims before independent validation.
