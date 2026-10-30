"""Retrieval over the knowledge base using multilingual embeddings and ChromaDB.

Documents are the entries in knowledge/*.json. They are embedded with
intfloat/multilingual-e5-small, which covers English, Hindi and Kannada, and
stored in a persistent Chroma collection under data/vectorstore/. The index is
rebuilt automatically when the knowledge files or the model change.

Build or inspect the index from the project root:
    python -m ai.rag "chest pain and sweating"
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional, Protocol

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "knowledge"
STORE_DIR = ROOT / "data" / "vectorstore"
COLLECTION = "knowledge"
EMBED_MODEL = os.getenv("REMOTECARE_EMBED_MODEL", "intfloat/multilingual-e5-small")

log = logging.getLogger(__name__)


def load_documents(knowledge_dir: Path = KNOWLEDGE_DIR) -> list[dict]:
    """Flatten every knowledge entry into {id, topic, kind, text, source}."""
    docs = []
    for path in sorted(knowledge_dir.glob("*.json")):
        kind = "emergency" if "emergency" in path.stem else "education"
        for i, item in enumerate(json.loads(path.read_text(encoding="utf-8"))):
            body = item.get("summary") or " ".join(item.get("steps", []))
            docs.append({
                "id": item.get("id") or f"{path.stem}-{i}",
                "topic": item["topic"],
                "kind": kind,
                "text": f"{item['topic']}. {body}",
                "source": item.get("source", ""),
            })
    return docs


class Embedder(Protocol):
    name: str
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class SentenceTransformerEmbedder:
    """E5 models expect "passage: " and "query: " prefixes; other models get none."""

    def __init__(self, model_name: str = EMBED_MODEL):
        from sentence_transformers import SentenceTransformer
        self.name = model_name
        self._model = SentenceTransformer(model_name)
        self._e5 = "e5" in model_name.lower()

    def _encode(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode([f"passage: {t}" if self._e5 else t for t in texts])

    def embed_query(self, text: str) -> list[float]:
        return self._encode([f"query: {text}" if self._e5 else text])[0]


class KnowledgeIndex:
    def __init__(self, embedder: Embedder, store_dir: Path = STORE_DIR,
                 knowledge_dir: Path = KNOWLEDGE_DIR):
        import chromadb
        from chromadb.config import Settings

        self.embedder = embedder
        self.knowledge_dir = knowledge_dir
        store_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(store_dir),
                                                settings=Settings(anonymized_telemetry=False))
        self.collection = None

    def _fingerprint(self, docs: list[dict]) -> str:
        payload = json.dumps([docs, self.embedder.name], sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def ensure_built(self) -> int:
        """Build the collection if it is missing or out of date. Returns the document count."""
        docs = load_documents(self.knowledge_dir)
        fingerprint = self._fingerprint(docs)
        existing = {c.name if hasattr(c, "name") else c for c in self.client.list_collections()}
        if COLLECTION in existing:
            col = self.client.get_collection(COLLECTION)
            if (col.metadata or {}).get("fingerprint") == fingerprint and col.count() == len(docs):
                self.collection = col
                return len(docs)
            self.client.delete_collection(COLLECTION)

        col = self.client.create_collection(
            COLLECTION, metadata={"hnsw:space": "cosine", "fingerprint": fingerprint})
        col.add(
            ids=[d["id"] for d in docs],
            documents=[d["text"] for d in docs],
            embeddings=self.embedder.embed_documents([d["text"] for d in docs]),
            metadatas=[{"topic": d["topic"], "kind": d["kind"], "source": d["source"]} for d in docs],
        )
        self.collection = col
        log.info("Built knowledge index: %d documents, model %s", len(docs), self.embedder.name)
        return len(docs)

    def search(self, query: str, k: int = 3, kind: Optional[str] = None) -> list[dict]:
        if self.collection is None:
            self.ensure_built()
        res = self.collection.query(
            query_embeddings=[self.embedder.embed_query(query)],
            n_results=k,
            where={"kind": kind} if kind else None,
        )
        hits = []
        for doc_id, text, meta, dist in zip(res["ids"][0], res["documents"][0],
                                             res["metadatas"][0], res["distances"][0]):
            hits.append({"id": doc_id, "topic": meta["topic"], "kind": meta["kind"],
                         "source": meta["source"], "text": text,
                         "score": round(1 - float(dist), 4)})
        return hits


@lru_cache(maxsize=1)
def _default_index() -> KnowledgeIndex:
    index = KnowledgeIndex(SentenceTransformerEmbedder())
    index.ensure_built()
    return index


def retrieve(query: str, k: int = 3) -> tuple[list[dict], str]:
    """Return (hits, status). Status is "ok" or "unavailable: <reason>".

    Retrieval failing (package missing, model not downloaded) must not stop
    triage, so errors are reported in the status instead of raised.
    """
    try:
        return _default_index().search(query, k=k), "ok"
    except Exception as exc:  # noqa: BLE001 - reported to the caller, not swallowed
        log.warning("Knowledge retrieval unavailable: %s", exc)
        return [], f"unavailable: {type(exc).__name__}: {exc}"[:200]


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "fever and vomiting in a child"
    hits, status = retrieve(query)
    print(f"status: {status}")
    for h in hits:
        print(f"{h['score']:.3f}  {h['id']:22} {h['topic']}")
