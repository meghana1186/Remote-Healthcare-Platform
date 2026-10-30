from pathlib import Path
import json
from typing import List

KNOWLEDGE = Path(__file__).resolve().parents[1] / "knowledge"

def retrieve(query: str, k: int = 4) -> List[dict]:
    terms = {w.lower() for w in query.split() if len(w) > 3}
    docs = []
    for path in KNOWN_JSON_FILES:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            text = json.dumps(item, ensure_ascii=False)
            score = sum(1 for term in terms if term in text.lower())
            if score:
                docs.append({"score": score, "source": path.name, "content": item})
    return sorted(docs, key=lambda x: x["score"], reverse=True)[:k]

KNOWN_JSON_FILES = list(KNOWLEDGE.glob("*.json"))
