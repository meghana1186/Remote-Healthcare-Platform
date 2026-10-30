"""Dashboard numbers computed from the seed data in data/.

Every figure shown on a dashboard comes from here, so nothing on screen is
typed in by hand. The seed data is synthetic, and the numbers say so.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def compute_metrics(data_dir: Path = DATA) -> dict:
    patients = pd.read_csv(data_dir / "patients.csv")
    consultations = pd.read_csv(data_dir / "consultations.csv")
    workers = pd.read_csv(data_dir / "health_workers.csv")
    campaigns = json.loads((data_dir / "campaigns.json").read_text(encoding="utf-8"))

    status = consultations["status"].value_counts()
    return {
        "synthetic": True,
        "patients": int(len(patients)),
        "villages": int(patients["village"].nunique()),
        "high_risk_patients": int((patients["risk"] == "High").sum()),
        "consultations": int(len(consultations)),
        "consultations_completed": int(status.get("Completed", 0)),
        "consultations_waiting": int(status.get("Waiting", 0)),
        "escalations": int(status.get("Escalated", 0)),
        "avg_wait_minutes": round(float(consultations["minutes_wait"].mean()), 1),
        "health_workers": int(len(workers)),
        "home_visits_today": int(workers["visits_today"].sum()),
        "households_visited": int(sum(c["visited"] for c in campaigns)),
        "households_targeted": int(sum(c["households"] for c in campaigns)),
        "consultations_by_urgency": {k: int(v) for k, v in consultations["urgency"].value_counts().items()},
        "patients_by_condition": {k: int(v) for k, v in patients["condition"].value_counts().items()},
    }
