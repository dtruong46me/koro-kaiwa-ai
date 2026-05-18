"""
Dummy implementations — dùng để kiểm tra data flow mà không cần API keys.
"""
from typing import Iterator, List

from ..core.interfaces import BaseASR, BaseLLM, BaseNLP, BaseTTS
from ..core.schemas import Message, NLPResult


class DummyASR(BaseASR):
    """Luôn trả về câu cố định để test pipeline."""

    def transcribe(self, audio_data: bytes) -> str:
        print("[DummyASR] Xử lý audio...")
        return "こんにちは"


class DummyLLM(BaseLLM):
    """Trả về phản hồi dựa trên từ khoá trong tin nhắn cuối."""

    def generate_response(self, context: List[Message]) -> str:
        print("[DummyLLM] Sinh phản hồi từ context...")
        if not context:
            return "どうしましたか？"
        last = context[-1].content
        if "こんにちは" in last:
            return "こんにちは！お元気ですか？"
        if "名前" in last or "なまえ" in last:
            return "私はコロちゃんです。よろしくお願いします！"
        return "なるほど、わかります。もっと話しましょう！"

    def stream_response(self, context: List[Message]) -> Iterator[str]:
        """Trả về từng ký tự để giả lập streaming."""
        full = self.generate_response(context)
        for char in full:
            yield char


class DummyTTS(BaseTTS):
    """Trả về bytes giả lập âm thanh."""

    def synthesize(self, text: str) -> bytes:
        print(f"[DummyTTS] Tổng hợp giọng nói: '{text}'")
        return f"<audio:{text}>".encode()


class DummyNLP(BaseNLP):
    """Trả về NLPResult cứng cho câu quen thuộc, placeholder cho câu khác."""

    _KNOWN: dict = {
        "こんにちは！お元気ですか？": NLPResult(
            furigana="こんにちは！お 元気(げんき) ですか？",
            romaji="Konnichiwa! Ogenki desu ka?",
            translation="Xin chào! Bạn có khỏe không?",
        ),
        "私はコロちゃんです。よろしくお願いします！": NLPResult(
            furigana="私(わたし) はコロちゃんです。よろしくお 願(ねが) いします！",
            romaji="Watashi wa Koro-chan desu. Yoroshiku onegaishimasu!",
            translation="Tôi là Koro-chan. Rất vui được gặp bạn!",
        ),
    }

    def process(self, text: str) -> NLPResult:
        print(f"[DummyNLP] Xử lý: '{text}'")
        return self._KNOWN.get(
            text,
            NLPResult(furigana=text, romaji="[romaji]", translation="[bản dịch]"),
        )
