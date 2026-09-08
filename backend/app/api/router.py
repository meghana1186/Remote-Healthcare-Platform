from fastapi import APIRouter
from backend.app.api import health, triage, demo

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(triage.router, prefix="/triage", tags=["triage"])
api_router.include_router(demo.router, prefix="/demo", tags=["demo"])
