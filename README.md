# RemoteCare AI 3.0

RemoteCare AI is a full-stack, AI-assisted telemedicine prototype for rural and underserved communities.

## Product

- Patient-first, low-bandwidth UX
- AI-assisted triage with deterministic emergency safety checks
- Groq LLM integration
- Groq Whisper speech-to-text
- Clinician-ready handoff summaries
- RAG-ready governed knowledge layer
- PostgreSQL data model
- FastAPI backend
- Redis/Celery background-job foundation
- Role-based architecture
- Audit logging and consent model
- AI evaluation suite
- Docker Compose local environment
- Premium glassmorphism frontend with no emoji-based UI

## Run

### Full stack
1. Copy `.env.example` to `.env` and add a Groq key if desired.
2. Run `docker compose up --build`.
3. Web app: http://localhost:3000
4. API: http://localhost:8000
5. API docs: http://localhost:8000/docs

### Existing Streamlit demo
The original Streamlit demo remains available in `app.py`.

## Safety

RemoteCare is a hackathon/portfolio prototype, not a medical device or production clinical system. The AI is designed to assist intake and clinician handoff; it does not autonomously diagnose or prescribe.

Before production use, add clinical validation, formal threat modeling, managed secrets, real identity verification, consent management, encryption/key management, verified provider/facility integrations, observability, backup/restore, governance, and jurisdiction-specific healthcare compliance.
