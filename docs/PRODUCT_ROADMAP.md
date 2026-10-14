# Product direction: from Venture Intelligence to Venture Pulse

**Status: discovery hypothesis, NOT an implemented v0.5 feature.**

## The user problem to validate

An early-stage investor, researcher, or founder may miss a material update about an interesting company or technology because the information is spread across different public sources. We have not interviewed HTGF staff, and do not claim to know their internal workflows.

## Proposed narrow v0.6 experiment

A user chooses 3–5 public organisations or research topics to follow. Once a day, a *user-initiated* or scheduled job reads permitted public sources (observing robots/licensing and API limits), compares snapshots against the previously stored versions, and outputs **at most three meaningful changes**. Each change includes:

- before/after evidence, original URL, publication time when known, retrieval time, source type;
- a concise answer to "Why should I care?" clearly marked as an inference;
- a confidence/verification status that never treats marketing copy as established fact;
- one suggested next action such as "open the source", "add an analyst note", or "dismiss";
- explicit **no material changes today** when appropriate.

No email ingestion, privileged tools, autonomous outreach, private deal data, or unapproved external actions. The proof remains grounded in publicly accessible information and user-controlled follow-up.

## Architecture hypothesis

**Sources → snapshot/diff → relevance filter → evidence verifier → three-item brief → human feedback**. The existing Venture Intelligence review and sources UI is reused for follow-up investigation. The evaluation work is shared infrastructure rather than a separate Agent Lab product.

Useful technical demonstrations: provenance and tool contracts, idempotent runs, uncertainty preservation, change detection, context selection, metric logging, and human approval boundaries. LangGraph is optional when a simple pipeline is sufficient; using an agent where deterministic code suffices is not a goal.

## Criteria to continue after a one-week pilot

- 3–5 willing test users from an appropriate, consenting audience (not represented as HTGF employees)
- At least 80% of showcased "changes" have a verifiable before/after source and no incorrect quote in the inspected sample
- Collect per-item usefulness: relevant / not relevant / already known
- Measure time to triage the three changes and whether a useful next action was actually taken
- Compare with a simple baseline: the same users manually reviewing a saved list of sources

The targets above are **proposed pilot gates**, not observed results. Continue only if the product demonstrates meaningful time savings or decision value. A weekly workflow may be better than daily for some audiences.

## Why this belongs after v0.5, not instead of it

The current release demonstrates the core engineering: parse a source, preserve evidence, inspect uncertainty, and defer consequential judgment. A future Pulse experiment validates whether that engine becomes a tool people willingly return to. We should keep both achievements and limitations unmistakable in the application.
