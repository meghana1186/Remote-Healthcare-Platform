from fastapi import APIRouter
router = APIRouter()

@router.get("/status")
def status():
    return {"database": "configured", "ai": "groq-compatible", "safety": "enabled"}
