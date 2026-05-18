"""
Tests cho Dummy component implementations.
Chạy: pytest tests/test_components/test_dummies.py -v
"""
import pytest

from src.components.dummies import DummyASR, DummyLLM, DummyNLP, DummyTTS
from src.core.schemas import Message, NLPResult


class TestDummyASR:
    def test_returns_string(self):
        assert isinstance(DummyASR().transcribe(b"any"), str)

    def test_returns_japanese(self):
        assert DummyASR().transcribe(b"audio") == "こんにちは"

    def test_accepts_any_bytes(self):
        DummyASR().transcribe(b"")
        DummyASR().transcribe(b"\x00\xff\xab")


class TestDummyLLM:
    def test_returns_string(self):
        assert isinstance(DummyLLM().generate_response([]), str)

    def test_empty_context(self):
        result = DummyLLM().generate_response([])
        assert len(result) > 0

    def test_greeting_response(self):
        ctx = [Message(role="user", content="こんにちは")]
        result = DummyLLM().generate_response(ctx)
        assert "こんにちは" in result

    def test_stream_response_yields_strings(self):
        ctx = [Message(role="user", content="こんにちは")]
        chunks = list(DummyLLM().stream_response(ctx))
        assert all(isinstance(c, str) for c in chunks)
        assert "".join(chunks) == DummyLLM().generate_response(ctx)


class TestDummyTTS:
    def test_returns_bytes(self):
        assert isinstance(DummyTTS().synthesize("テスト"), bytes)

    def test_non_empty_output(self):
        assert len(DummyTTS().synthesize("テスト")) > 0


class TestDummyNLP:
    def test_returns_nlp_result(self):
        assert isinstance(DummyNLP().process("テスト"), NLPResult)

    def test_known_text_has_real_data(self):
        result = DummyNLP().process("こんにちは！お元気ですか？")
        assert "Konnichiwa" in result.romaji
        assert "Xin chào" in result.translation

    def test_unknown_text_returns_placeholder(self):
        result = DummyNLP().process("unknown text xyz")
        assert result.furigana == "unknown text xyz"

    def test_all_fields_present(self):
        result = DummyNLP().process("テスト")
        assert result.furigana is not None
        assert result.romaji is not None
        assert result.translation is not None
