"""
NLP implementation dùng pykakasi (furigana/romaji) + Google Translate API (dịch thuật).
Yêu cầu: pip install pykakasi requests
"""
from __future__ import annotations

from typing import Optional

import requests

from ...core.interfaces import BaseNLP
from ...core.schemas import NLPResult


class KakasiNLP(BaseNLP):
    """
    Xử lý văn bản tiếng Nhật:
    - Furigana: chú thích cách đọc Kanji bằng Hiragana (dùng pykakasi).
    - Romaji: phiên âm Latin theo hệ Hepburn (dùng pykakasi).
    - Translation: dịch sang tiếng Việt (dùng Google Translate API).
      Nếu không có API key, translation trả về chuỗi rỗng.
    """

    def __init__(self, translation_api_key: Optional[str] = None):
        """
        Args:
            translation_api_key: Google Cloud Translation API key.
                                 Để trống sẽ bỏ qua bước dịch thuật.
        """
        import pykakasi  # type: ignore
        self._kakasi = pykakasi.kakasi()
        self._translation_key = translation_api_key

    def process(self, text: str) -> NLPResult:
        items = self._kakasi.convert(text)
        return NLPResult(
            furigana=self._build_furigana(items),
            romaji=self._build_romaji(items),
            translation=self._translate(text) if self._translation_key else "",
        )

    # ---------------------------------------------------------------- #
    # Private helpers
    # ---------------------------------------------------------------- #

    def _build_furigana(self, items: list) -> str:
        """
        Xây dựng chuỗi furigana: từ thuần Kana giữ nguyên,
        từ có Kanji được chú thích dạng 漢字(かんじ).
        """
        parts = []
        for item in items:
            orig: str = item["orig"]
            hira: str = item["hira"]
            # Chỉ thêm furigana nếu original có chứa Kanji
            if orig != hira and any("一" <= c <= "鿿" for c in orig):
                parts.append(f"{orig}({hira})")
            else:
                parts.append(orig)
        return "".join(parts)

    def _build_romaji(self, items: list) -> str:
        """Ghép nối phiên âm Hepburn của từng token, bỏ qua token rỗng."""
        return " ".join(
            item["hepburn"] for item in items if item.get("hepburn")
        )

    def _translate(self, text: str) -> str:
        """Gọi Google Cloud Translation API v2 để dịch sang tiếng Việt."""
        resp = requests.post(
            "https://translation.googleapis.com/language/translate/v2",
            params={"key": self._translation_key},
            json={"q": text, "source": "ja", "target": "vi", "format": "text"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["data"]["translations"][0]["translatedText"]
