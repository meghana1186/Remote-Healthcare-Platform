from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.db.session import Base, engine
from backend.app.db import models

app = FastAPI(title="RemoteCare AI API", version="3.0.0",
              description="AI-assisted telemedicine backend with clinician-in-the-loop safety.")

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
def startup():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        # Demo containers can start before Postgres is ready; health checks remain available.
        pass

@app.get("/health")
def health():
    return {"status":"ok","service":"remotecare-api","version":"3.0.0"}
