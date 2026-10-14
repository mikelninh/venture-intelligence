"""Auditable varied-layout synthetic benchmark.

Run from repository root:
    python scripts/evaluate_unseen.py

The 12-case manifest is frozen and separate from the original 30 training fixtures.
This script does not modify the production extractor or the gold labels.
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.analysis import analyze_pdf  # noqa: E402

MANIFEST = ROOT / "backend/evals/holdout/manifest.json"
FIELDS = ("company", "stage", "funding_sought", "traction", "team", "problem")

def make_pdf(case: dict) -> bytes:
    """Create a searchable fictional PDF. Nothing external is downloaded."""
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=(595, 842), pageCompression=0)
    pdf.setFillColor(HexColor("#F7F8F1"))
    pdf.rect(0, 0, 595, 842, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#163C32"))
    pdf.rect(0, 789, 595, 53, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#C3E1BA"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(43, 808, "SYNTHETIC PITCH — " + case["id"])
    pdf.setFillColor(HexColor("#163C32"))
    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawString(43, 744, case["name"])
    pdf.setStrokeColor(HexColor("#C9D8CD"))
    pdf.line(43, 722, 552, 722)
    y = 680
    if case["layout"] in ("prose", "incomplete"):
        pdf.setFont("Helvetica-Bold", 11)
        pdf.setFillColor(HexColor("#B06846"))
        pdf.drawString(45, 690, "OPPORTUNITY / CONTEXT")
        y = 657
    for line in case["lines"]:
        is_heading = case["layout"] == "prose" and line.isupper() and len(line) > 9
        is_label = case["layout"] == "two-line" and line.lower() in {
            "company", "stage", "funding sought", "traction", "team", "problem"
        }
        font, size = ("Helvetica-Bold", 18) if is_heading else (
            ("Helvetica-Bold", 12) if is_label else ("Helvetica", 12)
        )
        pdf.setFillColor(HexColor("#23453A"))
        pdf.setFont(font, size)
        for segment in simpleSplit(line, font, size, 480):
            pdf.drawString(47, y, segment)
            y -= 27 if is_heading else 23
        y -= 14 if case["layout"] in ("prose", "conflicting") else 6
        if y < 120:
            pdf.showPage()
            y = 725
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(HexColor("#82968A"))
    pdf.drawString(43, 60, "FICTIONAL DATA — for engineering evaluation only")
    pdf.save()
    return buf.getvalue()

def evaluate() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    totals = dict(total=0, correct_status=0, correct_value=0,
                  supported_gold=0, supported_recovered=0,
                  missing_gold=0, safe_abstentions=0,
                  conflict_gold=0, conflicts_detected=0,
                  evidence_checks=0, unsupported_citations=0)
    cases = []
    for entry in manifest["cases"]:
        deal = analyze_pdf(make_pdf(entry), entry["id"] + ".pdf")
        source_text = {s.id: s.text for s in deal.sources}
        errors = []
        for field in FIELDS:
            desired_status, desired_value = entry["expected"][field]
            observed = deal.facts[field]
            totals["total"] += 1
            totals["correct_status"] += observed.status == desired_status
            is_match = observed.status == desired_status and observed.value == desired_value
            totals["correct_value"] += is_match
            if desired_status == "supported":
                totals["supported_gold"] += 1
                totals["supported_recovered"] += is_match
            elif desired_status == "missing":
                totals["missing_gold"] += 1
                totals["safe_abstentions"] += observed.status == "missing"
            elif desired_status == "conflict":
                totals["conflict_gold"] += 1
                totals["conflicts_detected"] += (
                    observed.status == "conflict" and observed.value is None
                )
            if observed.status == "supported":
                totals["evidence_checks"] += 1
                quote = " ".join(source_text.get(i, "") for i in observed.evidence_ids)
                if not observed.evidence_ids or observed.value not in quote:
                    totals["unsupported_citations"] += 1
            if not is_match:
                errors.append(dict(field=field,
                                   expected=dict(status=desired_status, value=desired_value),
                                   actual=dict(status=observed.status, value=observed.value)))
        cases.append(dict(id=entry["id"], layout=entry["layout"],
                          mismatches=len(errors), errors=errors))
    percent = lambda n,d: round(n/d * 100, 1) if d else None
    summary = {**totals,
        "status_accuracy_pct": percent(totals["correct_status"], totals["total"]),
        "value_and_status_accuracy_pct": percent(totals["correct_value"], totals["total"]),
        "supported_field_recall_pct": percent(totals["supported_recovered"], totals["supported_gold"])}
    return {
        "benchmark": "varied-layout-synthetic-v1",
        "dataset_kind": "synthetic; deliberately new layouts; not real investment decks",
        "cases": len(cases), "fields": FIELDS, "metrics": summary, "case_details": cases,
        "caution": "Exploratory holdout. We did not tune the parser on these cases. Source containment verifies only that a statement appeared in the PDF, not that it is factually true."
    }

if __name__ == "__main__":
    report = evaluate()
    target = ROOT / "docs/unseen_evaluation.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["metrics"], indent=2))
