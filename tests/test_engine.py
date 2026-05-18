"""
Tests cho KaiwaEngine với Dummy components.
Chạy: pytest tests/test_engine.py -v
"""
import pytest

from src.components.dummies import DummyASR, DummyLLM, DummyNLP, DummyTTS
from src.core.schemas import InteractionResult, Session, StreamEvent
from src.engine import KaiwaEngine


@pytest.fixture
def engine() -> KaiwaEngine:
    return KaiwaEngine(DummyASR(), DummyLLM(), DummyTTS(), DummyNLP())


@pytest.fixture
def session() -> Session:
    return Session(session_id="test-001")


# ------------------------------------------------------------------ #
# interact()
# ------------------------------------------------------------------ #

class TestInteract:
    def test_returns_interaction_result(self, engine, session):
        result = engine.interact(session=session, audio_input=b"fake")
        assert isinstance(result, InteractionResult)

    def test_text_input_is_asr_output(self, engine, session):
        result = engine.interact(session=session, audio_input=b"fake")
        assert result.text_input == "こんにちは"

    def test_text_output_is_string(self, engine, session):
        result = engine.interact(session=session, audio_input=b"fake")
        assert isinstance(result.text_output, str)
        assert len(result.text_output) > 0

    def test_audio_output_is_bytes(self, engine, session):
        result = engine.interact(session=session, audio_input=b"fake")
        assert isinstance(result.audio_output, bytes)

    def test_nlp_result_has_all_fields(self, engine, session):
        result = engine.interact(session=session, audio_input=b"fake")
        assert result.nlp is not None
        assert isinstance(result.nlp.furigana, str)
        assert isinstance(result.nlp.romaji, str)
        assert isinstance(result.nlp.translation, str)

    def test_session_updated_after_interact(self, engine, session):
        engine.interact(session=session, audio_input=b"fake")
        assert len(session.history) == 2
        assert session.history[0].role == "user"
        assert session.history[1].role == "assistant"

    def test_multi_turn_accumulates_history(self, engine, session):
        engine.interact(session=session, audio_input=b"fake")
        engine.interact(session=session, audio_input=b"fake")
        assert len(session.history) == 4


# ------------------------------------------------------------------ #
# stream_interact()
# ------------------------------------------------------------------ #

class TestStreamInteract:
    def _collect(self, engine, session) -> list[StreamEvent]:
        return list(engine.stream_interact(session=session, audio_input=b"fake"))

    def test_yields_stream_events(self, engine, session):
        events = self._collect(engine, session)
        assert all(isinstance(e, StreamEvent) for e in events)

    def test_event_types_present(self, engine, session):
        types = {e.type for e in self._collect(engine, session)}
        assert "text_input" in types
        assert "text_output" in types
        assert "nlp_result" in types

    def test_at_least_one_audio_chunk(self, engine, session):
        events = self._collect(engine, session)
        audio_chunks = [e for e in events if e.type == "audio_chunk"]
        assert len(audio_chunks) >= 1

    def test_text_input_event_has_data(self, engine, session):
        events = self._collect(engine, session)
        text_input_events = [e for e in events if e.type == "text_input"]
        assert text_input_events[0].data == "こんにちは"

    def test_session_updated_after_stream(self, engine, session):
        self._collect(engine, session)
        assert len(session.history) == 2

    def test_event_order(self, engine, session):
        events = self._collect(engine, session)
        types = [e.type for e in events]
        # text_input phải xuất hiện trước text_output
        assert types.index("text_input") < types.index("text_output")
        # text_output phải xuất hiện trước nlp_result
        assert types.index("text_output") < types.index("nlp_result")
