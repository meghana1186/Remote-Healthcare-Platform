from celery import Celery
import os

celery_app = Celery("remotecare", broker=os.getenv("REDIS_URL", "redis://redis:6379/0"))

@celery_app.task
def send_followup(patient_id: int, message: str):
    return {"patient_id": patient_id, "queued": True, "message": message}
