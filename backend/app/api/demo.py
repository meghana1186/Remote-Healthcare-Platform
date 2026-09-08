from fastapi import APIRouter
from pathlib import Path
import pandas as pd

router = APIRouter()

@router.get("/patients")
def patients():
    path = Path("data/patients.csv")
    if not path.exists():
        return []
    return pd.read_csv(path).fillna("").to_dict(orient="records")

@router.get("/providers")
def providers():
    path = Path("data/providers.csv")
    if not path.exists():
        return []
    return pd.read_csv(path).fillna("").to_dict(orient="records")
