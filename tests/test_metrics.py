from services.metrics import compute_metrics


def test_metrics_come_from_seed_data():
    m = compute_metrics()
    assert m["synthetic"] is True
    assert m["patients"] == 8
    assert m["consultations"] == 5
    assert m["escalations"] == 1
    assert m["avg_wait_minutes"] == 5.8
    assert sum(m["consultations_by_urgency"].values()) == m["consultations"]


def test_metrics_endpoint():
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from backend.app.api.demo import router

    app = FastAPI()
    app.include_router(router, prefix="/demo")
    r = TestClient(app).get("/demo/metrics")
    assert r.status_code == 200 and r.json()["patients"] == 8
