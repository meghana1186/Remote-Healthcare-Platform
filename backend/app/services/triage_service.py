import time
from ai.safety import run_safety_checks
from ai.triage import triage_text
from backend.app.schemas.triage import TriageRequest, TriageResponse

def run_triage(req: TriageRequest) -> TriageResponse:
    started = time.perf_counter()
    safety = run_safety_checks(req.message)
    if safety.get("emergency"):
        return TriageResponse(
            urgency="emergency",
            emergency=True,
            summary="Potential emergency signal detected. Immediate in-person emergency assessment is recommended.",
            next_questions=[],
            clinician_handoff="Emergency escalation triggered by deterministic safety rules.",
            safety_flags=safety.get("flags", []),
        )
    result = triage_text(req.message, language=req.language)
    return TriageResponse(
        urgency=result.get("urgency", "routine"),
        emergency=False,
        summary=result.get("summary", ""),
        next_questions=result.get("follow_up_questions", []),
        clinician_handoff=result.get("clinician_handoff", ""),
        safety_flags=safety.get("flags", []),
    )
