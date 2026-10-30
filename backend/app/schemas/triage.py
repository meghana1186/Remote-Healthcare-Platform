from pydantic import BaseModel, Field

class TriageRequest(BaseModel):
    patient_id: int | None = None
    message: str = Field(min_length=2, max_length=10000)
    language: str = "English"

class TriageResponse(BaseModel):
    urgency: str
    emergency: bool
    summary: str
    next_questions: list[str]
    clinician_handoff: str
    safety_flags: list[str]
    source_count: int = 0
