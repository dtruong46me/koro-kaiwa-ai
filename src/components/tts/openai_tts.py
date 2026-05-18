"""
TTS implementation dùng OpenAI Text-to-Speech API.
"""
from __future__ import annotations

from ...core.interfaces import BaseTTS

VALID_VOICES = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}


class OpenAITTS(BaseTTS):
    """
    TTS dùng OpenAI API.
    Yêu cầu: pip install openai, biến môi trường OPENAI_API_KEY.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "tts-1",
        voice: str = "nova",
    ):
        """
        Args:
            api_key: OpenAI API key.
            model: "tts-1" (nhanh) hoặc "tts-1-hd" (chất lượng cao hơn).
            voice: alloy | echo | fable | onyx | nova | shimmer.
                   "nova" phát âm tiếng Nhật tốt nhất trong số các giọng có sẵn.
        """
        from openai import OpenAI  # type: ignore

        if voice not in VALID_VOICES:
            raise ValueError(f"Voice không hợp lệ: '{voice}'. Chọn: {VALID_VOICES}")

        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._voice = voice

    def synthesize(self, text: str) -> bytes:
        response = self._client.audio.speech.create(
            model=self._model,
            voice=self._voice,
            input=text,
            response_format="mp3",
        )
        return response.content
