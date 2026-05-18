"""
Các data model cốt lõi của hệ thống Koro Kaiwa AI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class Message:
    """Một tin nhắn trong cuộc hội thoại."""
    role: str     # "user" | "assistant" | "system"
    content: str


@dataclass
class NLPResult:
    """Kết quả xử lý ngôn ngữ phụ trợ cho Text B."""
    furigana: str    # Kanji được chú thích cách đọc
    romaji: str      # Phiên âm Latin toàn câu
    translation: str # Bản dịch tiếng Việt


@dataclass
class Session:
    """Trạng thái một phiên hội thoại."""
    session_id: str
    history: List[Message] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        """Thêm tin nhắn vào lịch sử."""
        self.history.append(Message(role=role, content=content))

    def get_context(self) -> List[Message]:
        """Trả về toàn bộ lịch sử để đưa vào LLM."""
        return self.history

    def clear(self) -> None:
        """Xoá toàn bộ lịch sử hội thoại."""
        self.history.clear()


@dataclass
class InteractionResult:
    """Kết quả trả về từ KaiwaEngine.interact()."""
    text_input: str    # Text A — lời người dùng đã transcribe
    text_output: str   # Text B — phản hồi AI
    audio_output: bytes
    nlp: NLPResult


@dataclass
class StreamEvent:
    """Một sự kiện trong luồng stream_interact()."""
    type: str   # "text_input" | "audio_chunk" | "text_output" | "nlp_result"
    data: Any = None
    text: str = ""  # Văn bản tương ứng với audio_chunk
