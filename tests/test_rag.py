"""RAG tests run offline with a tiny deterministic embedder.

They check the plumbing (indexing, rebuilds, search, wiring into triage),
not retrieval quality. Quality is measured with the real model by
python -m ai.evaluation.retrieval.
"""
import hashlib
import math

import pytest

chromadb = pytest.importorskip("chromadb")

from ai import rag, triage
from ai.evaluation.retrieval import evaluate as evaluate_retrieval


class HashEmbedder:
    """Bag of character trigrams hashed into 128 dimensions."""
    name = "test-hash-embedder"

    def _vec(self, text):
        v = [0.0] * 128
        t = f"  {text.lower()}  "
        for i in range(len(t) - 2):
            v[int(hashlib.md5(t[i:i + 3].encode()).hexdigest(), 16) % 128] += 1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


@pytest.fixture
def index(tmp_path):
    return rag.KnowledgeIndex(HashEmbedder(), store_dir=tmp_path / "store")


def test_load_documents_covers_both_files():
    docs = rag.load_documents()
    kinds = {d["kind"] for d in docs}
    assert kinds == {"emergency", "education"}
    assert len({d["id"] for d in docs}) == len(docs)
    assert all(d["source"] for d in docs)


def test_index_builds_once_and_reuses(index, tmp_path):
    n = index.ensure_built()
    assert n == len(rag.load_documents())
    again = rag.KnowledgeIndex(HashEmbedder(), store_dir=tmp_path / "store")
    assert again.ensure_built() == n
    assert again.collection.metadata["fingerprint"] == index.collection.metadata["fingerprint"]


def test_index_rebuilds_when_knowledge_changes(tmp_path):
    kdir = tmp_path / "knowledge"
    kdir.mkdir()
    (kdir / "health_education.json").write_text(
        '[{"id":"a","topic":"fever","summary":"drink water","source":"x"}]', encoding="utf-8")
    idx = rag.KnowledgeIndex(HashEmbedder(), store_dir=tmp_path / "s", knowledge_dir=kdir)
    assert idx.ensure_built() == 1
    (kdir / "health_education.json").write_text(
        '[{"id":"a","topic":"fever","summary":"drink water","source":"x"},'
        '{"id":"b","topic":"cough","summary":"see a doctor","source":"x"}]', encoding="utf-8")
    idx2 = rag.KnowledgeIndex(HashEmbedder(), store_dir=tmp_path / "s", knowledge_dir=kdir)
    assert idx2.ensure_built() == 2


def test_search_returns_scored_hits(index):
    hits = index.search("burns from a kitchen fire", k=3)
    assert len(hits) == 3
    assert {"id", "topic", "kind", "source", "text", "score"} <= hits[0].keys()
    assert hits[0]["score"] >= hits[-1]["score"]


def test_search_can_filter_by_kind(index):
    assert all(h["kind"] == "education" for h in index.search("fever", k=3, kind="education"))


def test_retrieval_eval_runs(index):
    report = evaluate_retrieval(index)
    assert report["overall"]["cases"] == 24


def test_triage_passes_retrieved_material_to_llm(monkeypatch):
    seen = {}

    class FakeGroq:
        def triage(self, case):
            seen.update(case)
            return ('{"urgency": "same_day", "risk_flags": [], "missing_questions": [], '
                    '"safe_next_step": "see a clinician", "patient_explanation": "ok", '
                    '"sources": ["fever", "not retrieved"]}')

    monkeypatch.setattr(triage, "GroqAI", FakeGroq)
    monkeypatch.setattr(triage, "assess_emergency", lambda m: {"emergency": False, "decided_by": "none"})
    monkeypatch.setattr(triage, "retrieve", lambda q, k=3: ([
        {"id": "ed-fever", "topic": "fever", "text": "fever. rest", "source": "s", "score": 0.9}], "ok"))

    r = triage.triage_text("fever for two days")
    assert seen["reference_material"] == [{"topic": "fever", "text": "fever. rest"}]
    assert r["sources"] == ["fever"]          # citations not in the retrieved set are dropped
    assert r["retrieval_status"] == "ok"


def test_emergency_skips_retrieval(monkeypatch):
    monkeypatch.setattr(triage, "retrieve", lambda *a, **k: pytest.fail("retrieval should not run"))
    r = triage.triage_text("crushing chest pain")
    assert r["emergency"] and r["retrieved"] == []


def test_triage_survives_retrieval_failure(monkeypatch):
    def broken_index():
        raise ImportError("sentence_transformers not installed")
    monkeypatch.setattr(rag, "_default_index", broken_index)
    hits, status = rag.retrieve("fever")
    assert hits == [] and status.startswith("unavailable")
