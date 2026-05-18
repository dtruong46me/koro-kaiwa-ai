"""
Cấu hình hệ thống — đọc từ biến môi trường hoặc file .env.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- LLM ---
    llm_provider: str = "openai"  # openai | gemini | anthropic
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-20241022"

    # --- ASR ---
    asr_provider: str = "openai_whisper"  # openai_whisper | whisper
    whisper_model_size: str = "base"

    # --- TTS ---
    tts_provider: str = "openai"  # openai | voicevox
    tts_model: str = "tts-1"
    tts_voice: str = "nova"
    voicevox_url: str = "http://localhost:50021"
    voicevox_speaker_id: int = 1

    # --- NLP ---
    google_translate_key: str = ""  # Để trống → bỏ qua dịch thuật

    # --- Session ---
    session_backend: str = "memory"  # memory | redis
    redis_url: str = "redis://localhost:6379"
    session_ttl: int = 3600

    # --- API Server ---
    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
