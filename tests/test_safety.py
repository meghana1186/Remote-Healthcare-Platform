from ai.safety import safety_gate

def test_chest_pain_is_emergency():
    r = safety_gate("patient has chest pain and sweating")
    assert r["is_emergency"] is True
