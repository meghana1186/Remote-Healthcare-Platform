"""Evaluate the emergency screen on the labelled cases in cases.json.

Usage, from the project root:
    python -m ai.evaluation.run            # rules only, works offline
    python -m ai.evaluation.run --llm      # rules plus the Groq second check (needs GROQ_API_KEY)

"Positive" means emergency. Recall is the share of real emergencies that were
caught, which is the number that matters most for a safety screen.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from ai.safety import assess_emergency

HERE = Path(__file__).parent


def _ratio(a: int, b: int) -> float | None:
    return round(a / b, 3) if b else None


def _metrics(rows: list[dict]) -> dict:
    tp = sum(r["expected"] and r["predicted"] for r in rows)
    fp = sum(not r["expected"] and r["predicted"] for r in rows)
    fn = sum(r["expected"] and not r["predicted"] for r in rows)
    tn = sum(not r["expected"] and not r["predicted"] for r in rows)
    precision, recall = _ratio(tp, tp + fp), _ratio(tp, tp + fn)
    f1 = round(2 * precision * recall / (precision + recall), 3) if precision and recall else None
    return {
        "cases": len(rows), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision, "recall": recall, "f1": f1,
        "specificity": _ratio(tn, tn + fp), "accuracy": _ratio(tp + tn, len(rows)),
    }


def evaluate(use_llm: bool = False) -> dict:
    cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    rows = []
    for case in cases:
        result = assess_emergency(case["input"], use_llm=use_llm)
        rows.append({
            "id": case["id"], "lang": case["lang"], "input": case["input"],
            "expected": case["expected"] == "emergency",
            "predicted": result["emergency"],
            "decided_by": result["decided_by"],
            "flags": result["flags"],
        })

    by_lang = defaultdict(list)
    for r in rows:
        by_lang[r["lang"]].append(r)

    return {
        "mode": "rules+llm" if use_llm else "rules",
        "overall": _metrics(rows),
        "by_language": {lang: _metrics(rs) for lang, rs in sorted(by_lang.items())},
        "llm_escalations": sum(r["decided_by"] == "llm" for r in rows),
        "errors": [
            {k: r[k] for k in ("id", "lang", "input", "flags")} | {"error": "missed" if r["expected"] else "false_alarm"}
            for r in rows if r["expected"] != r["predicted"]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="include the Groq second check")
    args = parser.parse_args()

    report = evaluate(use_llm=args.llm)
    out = HERE / "results" / f"safety_{report['mode'].replace('+', '_')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    m = report["overall"]
    print(f"Mode: {report['mode']}  cases: {m['cases']}")
    print(f"Precision {m['precision']}  Recall {m['recall']}  F1 {m['f1']}  "
          f"Specificity {m['specificity']}  Accuracy {m['accuracy']}")
    print(f"TP {m['tp']}  FP {m['fp']}  FN {m['fn']}  TN {m['tn']}")
    for lang, lm in report["by_language"].items():
        print(f"  {lang:8} n={lm['cases']:3}  recall {lm['recall']}  specificity {lm['specificity']}")
    for e in report["errors"]:
        print(f"  {e['error']:11} {e['id']}: {e['input']}")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
