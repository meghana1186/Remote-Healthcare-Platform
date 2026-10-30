"""Triage pipeline: emergency screen, then retrieval, then the LLM.

1. assess_emergency: deterministic rules, then an LLM check that can only escalate.
   Emergencies return immediately with the emergency message. No retrieved text is
   attached, so the patient never sees first-aid steps for the wrong condition.
2. retrieve: top knowledge-base entries for the message (multilingual embeddings).
3. GroqAI.triage: the LLM gets the message plus the retrieved entries and must
   name the topics it used.
"""
import json

from .groq_client import GroqAI
from .rag import retrieve
from .safety import assess_emergency


def _normalize(raw: dict, safety: dict, retrieved: list[dict], retrieval_status: str) -> dict:
    retrieved_topics = {d["topic"] for d in retrieved}
    cited = [s for s in (raw.get("sources") or []) if s in retrieved_topics]
    return {
        "urgency": raw.get("urgency", "routine"),
        "emergency": raw.get("urgency") == "emergency",
        "safety_decided_by": safety.get("decided_by", "none"),
        "summary": raw.get("summary") or raw.get("patient_explanation", ""),
        "follow_up_questions": raw.get("follow_up_questions") or raw.get("missing_questions") or [],
        "clinician_handoff": raw.get("clinician_handoff") or raw.get("safe_next_step", ""),
        "risk_flags": raw.get("risk_flags") or [],
        "sources": cited,
        "retrieved": [{k: d[k] for k in ("id", "topic", "source", "score")} for d in retrieved],
        "retrieval_status": retrieval_status,
    }


def triage_text(message: str, language: str = "English") -> dict:
    safety = assess_emergency(message)
    if safety["emergency"]:
        return _normalize({
            "urgency": "emergency",
            "risk_flags": safety["flags"],
            "missing_questions": [],
            "safe_next_step": safety["message"],
            "patient_explanation": "A potential emergency warning sign was detected.",
        }, safety, [], "skipped: emergency")

    retrieved, status = retrieve(message, k=3)
    raw = GroqAI().triage({
        "message": message,
        "language": language,
        "instruction": "Provide triage support and clinician handoff only. Do not diagnose or prescribe.",
        "reference_material": [{"topic": d["topic"], "text": d["text"]} for d in retrieved],
    })
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {
            "urgency": "same_day",
            "risk_flags": ["AI response needs clinician review"],
            "missing_questions": [],
            "safe_next_step": raw,
            "patient_explanation": "Please arrange professional assessment.",
        }
    # The model can also escalate; it is never allowed to downgrade the screen.
    return _normalize(parsed, safety, retrieved, status)


def run_triage(case: dict) -> dict:
    text = " ".join(str(v) for v in case.values())
    return triage_text(text)
