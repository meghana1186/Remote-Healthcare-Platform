from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="patient")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(40))
    language: Mapped[str] = mapped_column(String(40), default="English")
    location: Mapped[str | None] = mapped_column(String(160))
    emergency_contact: Mapped[str | None] = mapped_column(String(160))

class TriageSession(Base):
    __tablename__ = "triage_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"))
    transcript: Mapped[str] = mapped_column(Text, default="")
    urgency: Mapped[str] = mapped_column(String(32), default="routine")
    summary: Mapped[str] = mapped_column(Text, default="")
    safety_flags: Mapped[list] = mapped_column(JSON, default=list)
    clinician_review_required: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    clinician_name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(32), default="scheduled")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    channel: Mapped[str] = mapped_column(String(32), default="video")

class AIInteraction(Base):
    __tablename__ = "ai_interactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("triage_sessions.id"))
    model: Mapped[str] = mapped_column(String(120))
    input_text: Mapped[str] = mapped_column(Text)
    output_text: Mapped[str] = mapped_column(Text)
    safety_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(120))
    resource: Mapped[str] = mapped_column(String(160))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
