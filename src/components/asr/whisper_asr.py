"""
ASR implementations dùng OpenAI Whisper.
- WhisperASR: chạy model local (cần ffmpeg).
- OpenAIWhisperASR: gọi OpenAI API (cloud).
"""
from __future__ import annotations

import io
import os
import tempfile

from ...core.interfaces import BaseASR


class WhisperASR(BaseASR):
    """
    ASR dùng Whisper local.
    Yêu cầu: pip install openai-whisper, và ffmpeg trong PATH.
    """

    def __init__(self, model_name: str = "base"):
        """
        Args:
            model_name: Kích thước model — tiny | base | small | medium | large-v3.
                        Lớn hơn = chính xác hơn nhưng chậm hơn và tốn RAM hơn.
        """
        import whisper  # type: ignore
        print(f"[WhisperASR] Đang tải model '{model_name}'...")
        self._model = whisper.load_model(model_name)

    def transcribe(self, audio_data: bytes) -> str:
        # Ghi ra file tạm vì Whisper cần đường dẫn file hoặc numpy array
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            tmp_path = f.name
        try:
            result = self._model.transcribe(tmp_path, language=None)
            return result["text"].strip()
        finally:
            os.unlink(tmp_path)


class OpenAIWhisperASR(BaseASR):
    """
    ASR dùng OpenAI Whisper API (cloud).
    Yêu cầu: pip install openai, biến môi trường OPENAI_API_KEY.
    """

    def __init__(self, api_key: str, model: str = "whisper-1"):
        """
        Args:
            api_key: OpenAI API key.
            model: Tên model Whisper trên OpenAI API.
        """
        from openai import OpenAI  # type: ignore
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def transcribe(self, audio_data: bytes) -> str:
        # OpenAI API cần file-like object có thuộc tính .name để xác định format
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.wav"
        result = self._client.audio.transcriptions.create(
            model=self._model,
            file=audio_file,
            language="ja",
        )
        return result.text.strip()
