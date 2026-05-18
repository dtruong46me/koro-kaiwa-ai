"""
TTS implementation dùng Voicevox — engine giọng Nhật tự nhiên, chạy local.
Cài đặt Voicevox: https://voicevox.hiroshiba.jp/
Chạy Voicevox Engine trước khi dùng class này.
"""
from __future__ import annotations

import requests

from ...core.interfaces import BaseTTS


class VoicevoxTTS(BaseTTS):
    """
    TTS dùng Voicevox REST API (chạy local).
    Quy trình: Text → audio_query → synthesis → bytes.
    Yêu cầu: Voicevox Engine đang chạy tại base_url.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:50021",
        speaker_id: int = 1,
        timeout: int = 30,
    ):
        """
        Args:
            base_url: URL Voicevox Engine đang chạy.
            speaker_id: ID nhân vật giọng đọc.
                        1 = Shikoku Metan, 3 = Zundamon (giọng phổ biến nhất).
                        Xem danh sách đầy đủ tại /speakers endpoint.
            timeout: Timeout cho HTTP requests (giây).
        """
        self._base_url = base_url.rstrip("/")
        self._speaker_id = speaker_id
        self._timeout = timeout

    def synthesize(self, text: str) -> bytes:
        # Bước 1: Tạo audio query từ văn bản
        query_resp = requests.post(
            f"{self._base_url}/audio_query",
            params={"text": text, "speaker": self._speaker_id},
            timeout=self._timeout,
        )
        query_resp.raise_for_status()

        # Bước 2: Tổng hợp âm thanh từ query
        synthesis_resp = requests.post(
            f"{self._base_url}/synthesis",
            params={"speaker": self._speaker_id},
            json=query_resp.json(),
            timeout=self._timeout,
        )
        synthesis_resp.raise_for_status()
        return synthesis_resp.content

    def list_speakers(self) -> list:
        """Trả về danh sách nhân vật giọng đọc có sẵn."""
        resp = requests.get(f"{self._base_url}/speakers", timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()
