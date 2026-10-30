import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "RemoteCare AI"
    database_url: str = "postgresql+psycopg://remotecare:remotecare@db:5432/remotecare"
    redis_url: str = "redis://redis:6379/0"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_stt_model: str = "whisper-large-v3-turbo"
    cors_origins: list[str] = ["http://localhost:3000"]
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
