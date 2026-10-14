# Venture Intelligence · Evaluation beyond the original gold set

**14 October 2026 · Independent synthetic layout stress test · Not production accuracy**

## Why we built this

The first 30 synthetic pitch decks reached 510/510 field matches **after fixing a known test-set error**. That number was misleading without an untouched, differently designed test set. We therefore authored 12 new fictional decks with 6 evaluated fields each (72 decisions). The production parser was **not adjusted** after evaluating them.

## Results

| Metric | Result |
|---|---:|
| Fields with correct status AND value | **54 / 72 = 75.0%** |
| Present fields recovered exactly | **50 / 68 = 73.5%** |
| Contradiction cases safely left unresolved | **2 / 2** |
| Deliberately missing fields left empty | **2 / 2** |
| Accepted values without textual evidence | **0** |

**The failure mode matters more than the headline:** all 18 missed values occurred in three prose-first cases (H07, H08 and H09). A rule-based parser that expects explicit headings can be precise on structured documents but fails badly on natural language, even when the facts are plainly written.

| Cases | Presentation | Correct field decisions |
|---|---|---:|
| H01–H03 | Explicitly labelled fields | 18 / 18 |
| H04–H05 | Label/value on consecutive lines | 12 / 12 |
| H06 | Alternate labels | 6 / 6 |
| H07–H09 | Prose narrative | **0 / 18** |
| H10–H11 | Contradictory traction claims | 12 / 12 |
| H12 | Legitimately missing facts | 6 / 6 |

## What we'd change

A narrowly bounded **LLM-assisted candidate extractor**, capable of proposing source spans for prose, followed by deterministic verification of verbatim citations. We should measure precision, recall, hallucinations, latency and token cost on a **new unseen** set—not use this one repeatedly to tune prompts and report a perfect score.

## Reproduce it

```bash
python -m pip install -r backend/requirements-agent.txt -r backend/requirements-dev.txt
python scripts/evaluate_unseen.py
```

The script generates readable synthetic PDFs in memory from the frozen [12-case manifest](../backend/evals/holdout/manifest.json), executes the existing deterministic pipeline, and writes a detailed per-case JSON report. No external accounts or LLM keys are required.

- [Evaluation script](../scripts/evaluate_unseen.py)
- [Frozen test cases](../backend/evals/holdout/manifest.json)
- [GitHub CI](../.github/workflows/ci.yml)
- [Existing 30-deck regression suite](../backend/evals/gold.json)

**Important limits:** These cases are authored synthetic documents, not an independent real-world sample of founders' decks. Text presence is not factual verification. A generated PDF with a text layer is easier than image-only scans and some complex layouts.
