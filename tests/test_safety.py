import pytest

from ai.safety import normalize, safety_gate, screen


@pytest.mark.parametrize("text", [
    "patient has chest pain and sweating",
    "I can't breathe properly",
    "I cant breathe properly",
    "my child is breathless and her lips are turning blue",
    "I fainted and cannot stay awake",
    "his face is drooping on one side",
    "my husband swallowed pesticide",
    "she took too many sleeping pills",
    "heavy bleeding from the leg and it won't stop",
    "a snake bit my son in the field",
])
def test_english_emergencies_are_flagged(text):
    assert screen(text).emergency


@pytest.mark.parametrize("text", [
    "I have no chest pain, just a mild cold",
    "No difficulty breathing, only a runny nose",
    "He denies chest pain but has a sore throat",
    "I am not suicidal, just stressed about exams",
])
def test_negated_symptoms_are_not_flagged(text):
    result = screen(text)
    assert not result.emergency
    assert result.negated


def test_negation_does_not_cross_clause_boundary():
    assert screen("no fever, but chest pain since morning").emergency


def test_pseudo_negation_still_flags():
    assert screen("no improvement in the chest pain since last night").emergency


@pytest.mark.parametrize("text", [
    "मेरे पिताजी के सीने में तेज़ दर्द है",
    "बच्चे को सांस लेने में बहुत तकलीफ हो रही है",
    "Papa ke seene mein dard ho raha hai",
    "ನನ್ನ ತಂದೆಗೆ ಎದೆ ನೋವು ಇದೆ",
    "ಮಗುವಿಗೆ ಉಸಿರಾಟದ ತೊಂದರೆ ಆಗುತ್ತಿದೆ",
    "Haavu kacchide",
])
def test_hindi_and_kannada_emergencies_are_flagged(text):
    assert screen(text).emergency


@pytest.mark.parametrize("text", [
    "सीने में दर्द नहीं है, बस खांसी है",
    "Seene mein dard nahi hai, sirf gas hai",
    "ಎದೆ ನೋವು ಇಲ್ಲ, ಕೆಮ್ಮು ಮಾತ್ರ ಇದೆ",
    "Swalpa jvara ide, ede novu illa",
])
def test_hindi_and_kannada_negation(text):
    assert not screen(text).emergency


def test_kannada_poison_word_does_not_match_vishaya():
    # ವಿಷ (poison) is a prefix of ವಿಷಯ (topic); the second must not trigger.
    assert not screen("ಈ ವಿಷಯದ ಬಗ್ಗೆ ವೈದ್ಯರನ್ನು ಕೇಳಬೇಕು").emergency


def test_context_rules_need_their_context():
    assert not screen("not drinking much water today").emergency
    assert screen("my baby is not breastfeeding at all").emergency
    assert not screen("some bleeding from a small cut").emergency
    assert screen("I am pregnant and bleeding").emergency


def test_normalize_handles_apostrophes_and_nukta():
    assert normalize("Can’t") == "cant"
    assert normalize("ज़हर") == normalize("जहर")


def test_safety_gate_keeps_old_shape():
    r = safety_gate("patient has chest pain and sweating")
    assert r["is_emergency"] is True
    assert "chest pain" in r["flags"]
    assert "112" in r["message"]


def test_self_harm_gets_helpline_message():
    r = safety_gate("he keeps saying he wants to kill himself")
    assert "14416" in r["message"]


# LLM second check. The LLM is injected so these run offline.
from ai.groq_client import parse_emergency_verdict
from ai.safety import assess_emergency


def test_llm_not_called_when_rules_already_flag():
    calls = []
    r = assess_emergency("crushing chest pain", llm_check=lambda t: calls.append(t))
    assert r["emergency"] and r["decided_by"] == "rules"
    assert calls == []


def test_llm_can_escalate_a_rules_miss():
    r = assess_emergency("my mother looks grey, cold and clammy",
                         llm_check=lambda t: {"emergency": True, "reason": "possible shock"})
    assert r["emergency"] and r["decided_by"] == "llm"
    assert r["llm_reason"] == "possible shock"


def test_llm_cannot_clear_a_rules_flag():
    r = assess_emergency("I can't breathe", llm_check=lambda t: {"emergency": False, "reason": "fine"})
    assert r["emergency"]


def test_llm_failure_falls_back_to_rules():
    def boom(_):
        raise TimeoutError
    r = assess_emergency("mild headache", llm_check=boom)
    assert r["emergency"] is False and r["llm_checked"] is False


def test_llm_disabled_returns_rules_result():
    r = assess_emergency("mild headache", llm_check=lambda t: None)
    assert r["emergency"] is False and r["llm_checked"] is False


@pytest.mark.parametrize("raw,expected", [
    ('{"emergency": true, "reason": "stroke signs"}', True),
    ('{"emergency": false, "reason": "minor"}', False),
    ('{"emergency": "yes"}', None),
    ("not json", None),
])
def test_parse_emergency_verdict(raw, expected):
    v = parse_emergency_verdict(raw)
    assert (v["emergency"] if v else None) == expected
