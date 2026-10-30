import json
from pathlib import Path
from ai.safety import run_safety_checks

def evaluate():
    cases = json.loads((Path(__file__).parent / "cases.json").read_text())
    correct = 0
    for case in cases:
        result = run_safety_checks(case["input"])
        actual = "emergency" if result.get("emergency") else "routine"
        correct += actual == case["expected"]
    return {"cases": len(cases), "deterministic_safety_accuracy": correct / len(cases)}

if __name__ == "__main__":
    print(evaluate())
