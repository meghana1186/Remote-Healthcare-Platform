from ai.triage import triage_text
from backend.app.schemas.triage import TriageRequest, TriageResponse


def run_triage(req: TriageRequest) -> TriageResponse:
    # triage_text runs the emergency screen (rules, then LLM) before any generation.
    result = triage_text(req.message, language=req.language)
    return TriageResponse(
        urgency=result.get("urgency", "routine"),
        emergency=result.get("emergency", False),
        summary=result.get("summary", ""),
        next_questions=result.get("follow_up_questions", []),
        clinician_handoff=result.get("clinician_handoff", ""),
        safety_flags=result.get("risk_flags", []),
        source_count=len(result.get("retrieved", [])),
        sources=result.get("sources", []),
    )
