# RemoteCare AI 3.0 Architecture

This describes the target design. For what is built today and what is still a stub (auth, audit logging, notifications), see "Not built yet" in the README.

## Core flow

Patient voice/text -> safety checks -> triage -> retrieval -> Groq -> structured handoff -> clinician review -> referral/follow-up.

## Why the architecture is split

- Next.js provides a polished responsive patient/clinician experience.
- FastAPI owns authorization, validation, persistence and domain APIs.
- PostgreSQL is the source of truth for users, patients, appointments, triage and audit events.
- Redis/Celery provides a path for notifications and long-running jobs.
- Groq is isolated behind the AI service boundary.
- Deterministic safety checks run before generation.
- RAG supplies governed context rather than relying solely on model memory.

## Production path

Next.js + FastAPI -> managed PostgreSQL -> Redis -> worker fleet -> Groq + governed knowledge store -> observability/security controls.
