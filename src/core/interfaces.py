"""
Abstract Base Classes định nghĩa contract cho mọi component.
"""
from abc import ABC, abstractmethod
from typing import Iterator, List

from .schemas import Message, NLPResult


class BaseASR(ABC):
    """Interface cho Automatic Speech Recognition."""

    @abstractmethod
    def transcribe(self, audio_data: bytes) -> str:
        """
        Chuyển đổi audio thành văn bản.

        Args:
            audio_data: Dữ liệu âm thanh thô (WAV, WebM, MP3...).

        Returns:
            Văn bản đã nhận dạng (Text A).
        """


class BaseLLM(ABC):
    """Interface cho Large Language Model."""

    @abstractmethod
    def generate_response(self, context: List[Message]) -> str:
        """
        Sinh phản hồi đồng bộ từ lịch sử hội thoại.

        Args:
            context: Danh sách Message từ session.get_context().

        Returns:
            Phản hồi hoàn chỉnh (Text B).
        """

    def stream_response(self, context: List[Message]) -> Iterator[str]:
        """
        Sinh phản hồi theo dạng stream (từng token).
        Mặc định fallback về generate_response() — override để hỗ trợ streaming thực.

        Args:
            context: Danh sách Message từ session.get_context().

        Yields:
            Từng token/chunk văn bản.
        """
        yield self.generate_response(context)


class BaseTTS(ABC):
    """Interface cho Text-to-Speech."""

    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """
        Chuyển đổi văn bản thành âm thanh.

        Args:
            text: Văn bản tiếng Nhật cần đọc (Text B hoặc từng câu khi streaming).

        Returns:
            Dữ liệu âm thanh (MP3, WAV...).
        """


class BaseNLP(ABC):
    """Interface cho module xử lý ngôn ngữ phụ trợ (chạy bất đồng bộ)."""

    @abstractmethod
    def process(self, text: str) -> NLPResult:
        """
        Phân tích văn bản để lấy furigana, romaji và bản dịch.

        Args:
            text: Text B — phản hồi AI cần phân tích.

        Returns:
            NLPResult chứa furigana, romaji, translation.
        """
