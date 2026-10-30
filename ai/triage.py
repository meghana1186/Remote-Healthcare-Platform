import json
from .groq_client import GroqAI
from .safety import assess_emergency

def _normalize(raw: dict, safety: dict | None = None) -> dict:
    safety = safety or {}
    return {
        "urgency": raw.get("urgency", "routine"),
        "emergency": raw.get("urgency") == "emergency",
        "safety_decided_by": safety.get("decided_by", "none"),
        "summary": raw.get("summary") or raw.get("patient_explanation", ""),
        "follow_up_questions": raw.get("follow_up_questions") or raw.get("missing_questions") or [],
        "clinician_handoff": raw.get("clinician_handoff") or raw.get("safe_next_step", ""),
        "risk_flags": raw.get("risk_flags") or [],
    }

def triage_text(message: str, language: str = "English") -> dict:
    safety = assess_emergency(message)
    if safety["emergency"]:
        return _normalize({
            "urgency": "emergency",
            "risk_flags": safety["flags"],
            "missing_questions": [],
            "safe_next_step": safety["message"],
            "patient_explanation": "A potential emergency warning sign was detected."
        }, safety)

    raw = GroqAI().triage({
        "message": message,
        "language": language,
        "instruction": "Provide triage support and clinician handoff only. Do not diagnose or prescribe."
    })
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {
            "urgency": "same_day",
            "risk_flags": ["AI response needs clinician review"],
            "missing_questions": [],
            "safe_next_step": raw,
            "patient_explanation": "Please arrange professional assessment."
        }
    return _normalize(parsed, safety)

def run_triage(case: dict) -> dict:
    text = " ".join(str(v) for v in case.values())
    return triage_text(text)
