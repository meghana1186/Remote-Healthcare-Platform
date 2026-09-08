from __future__ import annotations
import json
from typing import Optional
from config.settings import GROQ_API_KEY, GROQ_LLM_MODEL, GROQ_STT_MODEL, DEMO_MODE
from .prompts import TRIAGE_PROMPT, SUMMARY_PROMPT, COPILOT_PROMPT, REPORT_PROMPT, TRANSLATE_PROMPT

try:
    from groq import Groq
except Exception:
    Groq = None

class GroqAI:
    def __init__(self):
        self.enabled = bool(GROQ_API_KEY and Groq)
        self.demo_mode = DEMO_MODE or not self.enabled
        self.client = Groq(api_key=GROQ_API_KEY) if self.enabled else None

    def _chat(self, system: str, user: str) -> str:
        if not self.enabled:
            return self._demo(user)
        response = self.client.chat.completions.create(
            model=GROQ_LLM_MODEL,
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
            temperature=0.2
        )
        return response.choices[0].message.content

    def _demo(self, user: str) -> str:
        u = user.lower()
        if any(x in u for x in ["chest pain","difficulty breathing","unconscious","severe bleeding"]):
            return json.dumps({
                "urgency":"emergency",
                "risk_flags":["Potential emergency warning sign"],
                "missing_questions":[],
                "safe_next_step":"Seek emergency medical care immediately.",
                "patient_explanation":"This may be an emergency. Do not delay professional care."
            })
        return json.dumps({
            "urgency":"same_day",
            "risk_flags":["Assessment needed"],
            "missing_questions":["Temperature","Duration","Ability to drink fluids"],
            "safe_next_step":"Arrange a same-day clinical assessment if symptoms persist or worsen.",
            "patient_explanation":"A clinician should review the symptoms, especially if they are worsening."
        })

    def triage(self, case: dict) -> str:
        return self._chat(TRIAGE_PROMPT, json.dumps(case, ensure_ascii=False, indent=2))

    def summarize(self, case: dict) -> str:
        return self._chat(SUMMARY_PROMPT, json.dumps(case, ensure_ascii=False, indent=2))

    def copilot(self, question: str, language: str = "English") -> str:
        return self._chat(COPILOT_PROMPT, f"Language: {language}\nQuestion: {question}")

    def explain_report(self, report_text: str) -> str:
        return self._chat(REPORT_PROMPT, report_text)

    def translate(self, text: str, language: str) -> str:
        return self._chat(TRANSLATE_PROMPT, f"Target language: {language}\nText: {text}")

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        if not self.enabled:
            return "Demo transcription: patient reports fever for three days and reduced appetite."
        with open(audio_path, "rb") as audio:
            result = self.client.audio.transcriptions.create(
                file=audio, model=GROQ_STT_MODEL,
                language=language if language else None, response_format="text"
            )
        return str(result)
