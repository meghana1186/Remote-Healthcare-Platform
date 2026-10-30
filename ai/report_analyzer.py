from .groq_client import GroqAI
def analyze_report(text: str) -> str:
    return GroqAI().explain_report(text)
