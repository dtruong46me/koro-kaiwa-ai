"""
KaiwaEngine — bộ điều phối trung tâm toàn bộ pipeline hội thoại.
"""
from __future__ import annotations

from typing import Iterator

from .core.interfaces import BaseASR, BaseLLM, BaseNLP, BaseTTS
from .core.schemas import InteractionResult, NLPResult, Session, StreamEvent

# Ký tự kết thúc câu — dùng để gom token thành câu khi streaming TTS
_SENTENCE_ENDINGS = frozenset("。！？.!?\n…")


class KaiwaEngine:
    """
    Điều phối luồng: ASR → LLM → TTS → NLP.
    Hỗ trợ hai chế độ:
      - interact():        đồng bộ, dùng cho CLI và testing.
      - stream_interact(): streaming, dùng cho WebSocket API.
    """

    def __init__(
        self,
        asr: BaseASR,
        llm: BaseLLM,
        tts: BaseTTS,
        nlp: BaseNLP,
    ) -> None:
        self.asr = asr
        self.llm = llm
        self.tts = tts
        self.nlp = nlp

    # ---------------------------------------------------------------- #
    # Đồng bộ — CLI / testing
    # ---------------------------------------------------------------- #

    def interact(self, session: Session, audio_input: bytes) -> InteractionResult:
        """
        Chạy một lượt hội thoại đầy đủ theo thứ tự tuần tự.
        Session được cập nhật in-place.

        Returns:
            InteractionResult chứa text_input, text_output, audio_output, nlp.
        """
        # Bước 1: ASR
        text_a = self.asr.transcribe(audio_input)
        session.add_message("user", text_a)

        # Bước 2: LLM
        text_b = self.llm.generate_response(session.get_context())
        session.add_message("assistant", text_b)

        # Bước 3: TTS
        audio_output = self.tts.synthesize(text_b)

        # Bước 4: NLP phụ trợ
        nlp_result = self.nlp.process(text_b)

        return InteractionResult(
            text_input=text_a,
            text_output=text_b,
            audio_output=audio_output,
            nlp=nlp_result,
        )

    # ---------------------------------------------------------------- #
    # Streaming — WebSocket API
    # ---------------------------------------------------------------- #

    def stream_interact(
        self,
        session: Session,
        audio_input: bytes,
    ) -> Iterator[StreamEvent]:
        """
        Streaming pipeline: sinh từng StreamEvent theo đúng thứ tự ưu tiên UI.

        Thứ tự sự kiện:
          1. text_input    — ngay sau khi ASR hoàn thành
          2. audio_chunk   — mỗi câu hoàn chỉnh (TTS per-sentence)
          3. text_output   — toàn bộ Text B sau khi LLM xong
          4. nlp_result    — sau khi NLP xử lý xong

        Session được cập nhật in-place (add_message) trước khi yield text_output.
        """
        # Bước 1: ASR
        text_a = self.asr.transcribe(audio_input)
        session.add_message("user", text_a)
        yield StreamEvent(type="text_input", data=text_a)

        # Bước 2 + 3: LLM stream → gom câu → TTS từng câu
        full_text_b, buffer = "", ""

        for token in self.llm.stream_response(session.get_context()):
            full_text_b += token
            buffer += token

            # Khi buffer kết thúc bằng dấu câu → tổng hợp âm thanh ngay
            if buffer and buffer[-1] in _SENTENCE_ENDINGS:
                sentence = buffer.strip()
                if sentence:
                    audio_chunk = self.tts.synthesize(sentence)
                    yield StreamEvent(type="audio_chunk", data=audio_chunk, text=sentence)
                buffer = ""

        # Flush phần còn lại chưa kết thúc bằng dấu câu
        if buffer.strip():
            audio_chunk = self.tts.synthesize(buffer.strip())
            yield StreamEvent(type="audio_chunk", data=audio_chunk, text=buffer.strip())

        # Lưu phản hồi đầy đủ vào session
        session.add_message("assistant", full_text_b)
        yield StreamEvent(type="text_output", data=full_text_b)

        # Bước 4: NLP phụ trợ
        nlp_result: NLPResult = self.nlp.process(full_text_b)
        yield StreamEvent(type="nlp_result", data=nlp_result)
