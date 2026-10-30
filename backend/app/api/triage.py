from fastapi import APIRouter
from backend.app.schemas.triage import TriageRequest, TriageResponse
from backend.app.services.triage_service import run_triage

router = APIRouter()

@router.post("", response_model=TriageResponse)
def triage(req: TriageRequest):
    return run_triage(req)
