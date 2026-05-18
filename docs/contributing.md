# Hướng dẫn đóng góp (Contributing)

Tài liệu này mô tả cách thêm implementation mới, quy ước code và quy trình phát triển.

---

## 1. Quy ước code

| Yếu tố | Quy ước |
|--------|---------|
| **Ngôn ngữ biến/hàm/class** | English (`transcribe`, `generate_response`, `KaiwaEngine`) |
| **Docstrings và comment** | Tiếng Việt |
| **Print/log messages** | Tiếng Việt |
| **Tên file** | snake_case (`whisper_asr.py`, `openai_llm.py`) |
| **Class names** | PascalCase (`WhisperASR`, `OpenAILLM`) |

---

## 2. Thêm implementation mới

### Bước 1: Tạo file trong thư mục đúng

```
src/components/
├── asr/        ← Các ASR implementations
├── llm/        ← Các LLM implementations
├── tts/        ← Các TTS implementations
└── nlp/        ← Các NLP implementations
```

### Bước 2: Kế thừa ABC tương ứng

Mọi implementation đều phải:
1. Kế thừa đúng ABC từ `src/core/interfaces.py`
2. Implement đầy đủ abstract method (không được bỏ trống)
3. Constructor nhận config qua tham số (không hardcode)

**Template chuẩn cho ASR:**
```python
# src/components/asr/my_asr.py
"""
Mô tả ngắn gọn về implementation này (dùng API gì, đặc điểm gì).
"""
from src.core.interfaces import BaseASR


class MyASR(BaseASR):
    """Mô tả class bằng tiếng Việt."""

    def __init__(self, api_key: str, model: str = "default"):
        """
        Khởi tạo MyASR.

        Args:
            api_key: API key để xác thực.
            model: Tên model sử dụng.
        """
        self.client = SomeAPIClient(api_key=api_key)
        self.model = model

    def transcribe(self, audio_data: bytes) -> str:
        """
        Nhận dạng giọng nói từ audio_data.

        Args:
            audio_data: Dữ liệu âm thanh thô dưới dạng bytes.

        Returns:
            Văn bản đã nhận dạng.
        """
        result = self.client.transcribe(audio_data, model=self.model)
        return result.text
```

**Template chuẩn cho LLM:**
```python
# src/components/llm/my_llm.py
from typing import List
from src.core.interfaces import BaseLLM
from src.core.schemas import Message

SYSTEM_PROMPT = """Bạn là Koro-chan, người bạn thân thiện giúp luyện tiếng Nhật..."""
MAX_HISTORY = 20


class MyLLM(BaseLLM):
    """Mô tả class bằng tiếng Việt."""

    def __init__(self, api_key: str, model: str = "default-model"):
        self.client = SomeAPIClient(api_key=api_key)
        self.model = model

    def generate_response(self, context: List[Message]) -> str:
        """
        Sinh phản hồi dựa trên lịch sử hội thoại.

        Args:
            context: Danh sách Message từ session.get_context().

        Returns:
            Văn bản phản hồi (Text B).
        """
        # Cắt ngắn lịch sử để tránh vượt context window
        trimmed = context[-MAX_HISTORY:]

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [{"role": m.role, "content": m.content} for m in trimmed]

        response = self.client.chat(model=self.model, messages=messages)
        return response.text
```

### Bước 3: Đăng ký và test

Tạo file test tại `tests/test_components/test_my_component.py`:

```python
from src.components.asr.my_asr import MyASR

def test_transcribe_returns_string():
    asr = MyASR(api_key="test-key")
    result = asr.transcribe(b"audio_bytes")
    assert isinstance(result, str)
    assert len(result) > 0
```

Chạy test:
```bash
pytest tests/test_components/test_my_component.py -v
```

### Bước 4: Dùng trong engine

```python
# main.py hoặc ứng dụng thực tế
from src.components.asr.my_asr import MyASR
from src.components.dummies import DummyLLM, DummyTTS, DummyNLP
from src.engine import KaiwaEngine
from src.core.schemas import Session

engine = KaiwaEngine(
    asr=MyASR(api_key="your-key"),
    llm=DummyLLM(),   # Thay dần từng component
    tts=DummyTTS(),
    nlp=DummyNLP(),
)
session = Session(session_id="test-001")
result = engine.interact(session=session, audio_input=b"real_audio")
```

---

## 3. Mở rộng KaiwaEngine

Khi cần thêm tính năng vào engine (e.g., streaming support, pronunciation assessment), hãy:

1. **Không sửa interfaces** (`src/core/interfaces.py`) trừ khi thực sự cần thiết — các thay đổi ở đây ảnh hưởng đến tất cả implementations.
2. **Mở rộng engine** bằng cách thêm method mới vào `KaiwaEngine`, không overload `interact()`.
3. **Tạo interface mới** nếu cần component hoàn toàn mới (e.g., `BasePronunciationAssessor`).

---

## 4. Checklist trước khi commit

- [ ] Implementation kế thừa đúng ABC và implement đầy đủ abstract method.
- [ ] Constructor nhận config qua tham số, không hardcode API keys.
- [ ] Docstring bằng tiếng Việt, tên biến/hàm bằng tiếng Anh.
- [ ] Chạy `python main.py` vẫn hoạt động bình thường (không phá vỡ Dummy flow).
- [ ] Không commit API keys, credentials, hoặc file `.env` vào git.

---

## 5. Cấu trúc tham chiếu khi phát triển

| Muốn biết | Đọc tài liệu nào |
|-----------|-----------------|
| Hiểu contract của một interface | [docs/api-reference.md](api-reference.md) |
| Hiểu toàn bộ data flow | [docs/architecture.md](architecture.md) |
| Xem ví dụ implementation đầy đủ | [src/components/dummies.py](../src/components/dummies.py) |
| Kế hoạch tích hợp Phase 1 | [docs/phase1/implementation_guide.md](phase1/implementation_guide.md) |
