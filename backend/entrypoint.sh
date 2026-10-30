#!/bin/sh
set -e
python -c "from backend.app.db.session import Base, engine; Base.metadata.create_all(bind=engine)"
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
