"""
LLM implementation dùng LangChain — hỗ trợ nhiều provider qua factory functions.

Cách dùng:
    from src.components.llm import build_openai, build_gemini, build_anthropic

    llm = build_openai(api_key="sk-...", model="gpt-4o-mini")
    llm = build_gemini(api_key="AIza...", model="gemini-2.0-flash")
    llm = build_anthropic(api_key="sk-ant-...", model="claude-3-5-haiku-20241022")

Để thêm provider mới: tạo thêm một hàm build_<provider>() theo đúng pattern.
"""
from __future__ import annotations

from typing import Iterator, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel  # type: ignore
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage  # type: ignore
from langchain_core.output_parsers import StrOutputParser  # type: ignore

from ...core.interfaces import BaseLLM
from ...core.schemas import Message

# ------------------------------------------------------------------ #
# System prompt mặc định — có thể override qua constructor
# ------------------------------------------------------------------ #
DEFAULT_SYSTEM_PROMPT = """Bạn là Koro-chan (コロちゃん), một người bạn thân thiện và kiên nhẫn \
giúp người dùng luyện tiếng Nhật thông qua hội thoại tự nhiên.

Nguyên tắc:
- Luôn trả lời bằng tiếng Nhật tự nhiên, phù hợp với trình độ người dùng.
- Nếu người dùng mắc lỗi ngữ pháp nhỏ, hãy hiểu ý và trả lời bình thường — \
  đừng ngắt mạch hội thoại chỉ để sửa lỗi.
- Giữ câu trả lời ngắn gọn (1–3 câu) để phù hợp với nhịp độ hội thoại.
- Nếu người dùng nhắn tiếng Việt, hãy khuyến khích chuyển sang tiếng Nhật \
  nhưng vẫn trả lời để không làm gián đoạn cuộc trò chuyện."""

MAX_HISTORY = 20  # Số tin nhắn tối đa đưa vào context window


# ------------------------------------------------------------------ #
# Core class
# ------------------------------------------------------------------ #
class LangChainLLM(BaseLLM):
    """
    Wrapper quanh bất kỳ BaseChatModel nào của LangChain.
    Hỗ trợ cả generate_response() đồng bộ và stream_response() streaming.
    """

    def __init__(
        self,
        chat_model: BaseChatModel,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_history: int = MAX_HISTORY,
    ):
        """
        Args:
            chat_model: Bất kỳ LangChain BaseChatModel nào (ChatOpenAI, ChatGoogleGenerativeAI...).
            system_prompt: Prompt định hình vai trò và hành vi của AI.
            max_history: Số tin nhắn cuối cùng được giữ lại để tránh vượt context window.
        """
        self._chain = chat_model | StrOutputParser()
        self._system_prompt = system_prompt
        self._max_history = max_history

    def generate_response(self, context: List[Message]) -> str:
        """Gọi LLM đồng bộ, trả về toàn bộ phản hồi."""
        return self._chain.invoke(self._build_messages(context))

    def stream_response(self, context: List[Message]) -> Iterator[str]:
        """Stream phản hồi từng token — dùng cho WebSocket real-time."""
        for chunk in self._chain.stream(self._build_messages(context)):
            yield chunk

    # ---------------------------------------------------------------- #
    # Private
    # ---------------------------------------------------------------- #
    def _build_messages(self, context: List[Message]) -> List[BaseMessage]:
        """Chuyển đổi List[Message] sang LangChain message format."""
        messages: List[BaseMessage] = [SystemMessage(content=self._system_prompt)]
        for msg in context[-self._max_history:]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        return messages


# ------------------------------------------------------------------ #
# Factory functions — thêm provider mới bằng cách thêm hàm build_*
# ------------------------------------------------------------------ #

def build_openai(
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    **kwargs,
) -> LangChainLLM:
    """
    Tạo LangChainLLM dùng OpenAI.
    Yêu cầu: pip install langchain-openai
    """
    from langchain_openai import ChatOpenAI  # type: ignore
    chat_model = ChatOpenAI(model=model, api_key=api_key, **kwargs)
    return LangChainLLM(chat_model=chat_model, system_prompt=system_prompt)


def build_gemini(
    model: str = "gemini-2.0-flash",
    api_key: Optional[str] = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    **kwargs,
) -> LangChainLLM:
    """
    Tạo LangChainLLM dùng Google Gemini.
    Yêu cầu: pip install langchain-google-genai
    """
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
    chat_model = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        **kwargs,
    )
    return LangChainLLM(chat_model=chat_model, system_prompt=system_prompt)


def build_anthropic(
    model: str = "claude-3-5-haiku-20241022",
    api_key: Optional[str] = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    **kwargs,
) -> LangChainLLM:
    """
    Tạo LangChainLLM dùng Anthropic Claude.
    Yêu cầu: pip install langchain-anthropic
    """
    from langchain_anthropic import ChatAnthropic  # type: ignore
    chat_model = ChatAnthropic(model=model, api_key=api_key, **kwargs)
    return LangChainLLM(chat_model=chat_model, system_prompt=system_prompt)
