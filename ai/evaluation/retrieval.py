"""Evaluate knowledge retrieval: does the right entry come back for a query?

Usage, from the project root (downloads the embedding model on first run):
    python -m ai.evaluation.retrieval

Reports hit@1, hit@3 and mean reciprocal rank, overall and per language.
A case counts as a hit if any of its "expected" ids is returned.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent


def evaluate(index=None, k: int = 3) -> dict:
    if index is None:
        from ai.rag import _default_index
        index = _default_index()
    cases = json.loads((HERE / "retrieval_cases.json").read_text(encoding="utf-8"))
    rows = []
    for case in cases:
        ids = [h["id"] for h in index.search(case["query"], k=k)]
        rank = next((i + 1 for i, doc_id in enumerate(ids) if doc_id in case["expected"]), None)
        rows.append({"id": case["id"], "lang": case["lang"], "query": case["query"],
                     "expected": case["expected"], "returned": ids, "rank": rank})

    def summary(rs):
        n = len(rs)
        return {"cases": n,
                "hit@1": round(sum(r["rank"] == 1 for r in rs) / n, 3),
                f"hit@{k}": round(sum(r["rank"] is not None for r in rs) / n, 3),
                "mrr": round(sum(1 / r["rank"] for r in rs if r["rank"]) / n, 3)}

    by_lang = defaultdict(list)
    for r in rows:
        by_lang[r["lang"]].append(r)
    return {"model": index.embedder.name, "overall": summary(rows),
            "by_language": {lang: summary(rs) for lang, rs in sorted(by_lang.items())},
            "misses": [r for r in rows if r["rank"] is None]}


def main() -> None:
    report = evaluate()
    out = HERE / "results" / "retrieval.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Model: {report['model']}")
    print("Overall:", report["overall"])
    for lang, s in report["by_language"].items():
        print(f"  {lang}: {s}")
    for m in report["misses"]:
        print(f"  missed {m['id']}: {m['query']} -> {m['returned']}")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
