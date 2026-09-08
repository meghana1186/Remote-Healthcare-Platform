import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = lambda *_args, **_kwargs: None

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "openai/gpt-oss-120b")
GROQ_STT_MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
DEMO_MODE = os.getenv("REMOTECARE_DEMO_MODE", "true").lower() == "true"
DB_PATH = ROOT / os.getenv("REMOTECARE_DB_PATH", "data/remotecare.db")
DEFAULT_LANGUAGE = os.getenv("REMOTECARE_LANGUAGE", "en")
APP_NAME = "RemoteCare AI"
APP_VERSION = "3.0.0"
