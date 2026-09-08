# RemoteCare AI 3.0 Demo Runbook

## Fastest local demo

### Backend
cd backend
python -m pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000

### Frontend
cd frontend
npm install
npm run dev

Open http://localhost:3000.

## Full Docker demo

From repository root:

docker compose up --build

Open:
- http://localhost:3000
- http://localhost:8000/docs

## Demo sequence

1. Open Overview.
2. Start AI Triage.
3. Use the respiratory case example.
4. Show structured clinician handoff.
5. Show Appointments.
6. Show Health Record.
7. Show Care Team.
8. Show Referrals.
9. Show Impact Analytics.
10. Explain that the backend is FastAPI + PostgreSQL and AI is isolated behind a safety boundary.

## Important

The included data is synthetic. The system is a portfolio/hackathon prototype and must not be used for real clinical decisions.
