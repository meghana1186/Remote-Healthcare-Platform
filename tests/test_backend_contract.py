from backend.app.schemas.triage import TriageRequest

def test_triage_request_validation():
    req = TriageRequest(message="persistent cough for three days")
    assert req.language == "English"
