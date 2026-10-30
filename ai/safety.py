EMERGENCY_TERMS = [
    "chest pain", "chest pressure", "difficulty breathing", "trouble breathing",
    "cannot breathe", "can't breathe", "unconscious", "severe bleeding",
    "heavy bleeding", "seizure", "stroke", "poisoning", "overdose",
    "suicide", "not waking", "blue lips", "severe burn"
]

def emergency_flags(text: str) -> list[str]:
    t = text.lower()
    return [term for term in EMERGENCY_TERMS if term in t]

def safety_gate(text: str) -> dict:
    flags = emergency_flags(text)
    return {
        "is_emergency": bool(flags),
        "flags": flags,
        "message": "Seek emergency medical care immediately." if flags else ""
    }

# Backend-compatible public API.
def run_safety_checks(text: str) -> dict:
    gate = safety_gate(text)
    return {
        "emergency": gate["is_emergency"],
        "flags": gate["flags"],
        "message": gate["message"],
    }
