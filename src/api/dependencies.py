"""
Khởi tạo engine và session store từ Settings — dùng trong lifespan của FastAPI.
"""
from __future__ import annotations

from ..config import get_settings
from ..engine import KaiwaEngine
from .session_store import BaseSessionStore, InMemorySessionStore, RedisSessionStore


def build_engine() -> KaiwaEngine:
    """Tạo KaiwaEngine với các components được chọn từ biến môi trường."""
    s = get_settings()

    # --- ASR ---
    if s.asr_provider == "whisper":
        from ..components.asr import WhisperASR
        asr = WhisperASR(model_name=s.whisper_model_size)
    elif s.asr_provider == "openai_whisper":
        from ..components.asr import OpenAIWhisperASR
        asr = OpenAIWhisperASR(api_key=s.openai_api_key)
    else:
        raise ValueError(f"ASR provider không hợp lệ: '{s.asr_provider}'")

    # --- LLM ---
    if s.llm_provider == "openai":
        from ..components.llm import build_openai
        llm = build_openai(model=s.openai_model, api_key=s.openai_api_key)
    elif s.llm_provider == "gemini":
        from ..components.llm import build_gemini
        llm = build_gemini(model=s.gemini_model, api_key=s.gemini_api_key)
    elif s.llm_provider == "anthropic":
        from ..components.llm import build_anthropic
        llm = build_anthropic(model=s.anthropic_model, api_key=s.anthropic_api_key)
    else:
        raise ValueError(f"LLM provider không hợp lệ: '{s.llm_provider}'")

    # --- TTS ---
    if s.tts_provider == "openai":
        from ..components.tts import OpenAITTS
        tts = OpenAITTS(api_key=s.openai_api_key, model=s.tts_model, voice=s.tts_voice)
    elif s.tts_provider == "voicevox":
        from ..components.tts import VoicevoxTTS
        tts = VoicevoxTTS(base_url=s.voicevox_url, speaker_id=s.voicevox_speaker_id)
    else:
        raise ValueError(f"TTS provider không hợp lệ: '{s.tts_provider}'")

    # --- NLP ---
    from ..components.nlp import KakasiNLP
    nlp = KakasiNLP(translation_api_key=s.google_translate_key or None)

    return KaiwaEngine(asr=asr, llm=llm, tts=tts, nlp=nlp)


def build_session_store() -> BaseSessionStore:
    """Tạo session store từ biến môi trường SESSION_BACKEND."""
    s = get_settings()
    if s.session_backend == "redis":
        return RedisSessionStore(redis_url=s.redis_url, ttl=s.session_ttl)
    return InMemorySessionStore()
