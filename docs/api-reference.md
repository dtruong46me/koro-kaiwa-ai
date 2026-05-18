# API Reference

Tài liệu tham chiếu đầy đủ cho tất cả các class, interface và data model của Koro Kaiwa AI.

---

## Schemas (`src/core/schemas.py`)

### `Message`

Đại diện cho một tin nhắn trong cuộc hội thoại.

```python
@dataclass
class Message:
    role: str     # "user" hoặc "assistant"
    content: str  # nội dung tin nhắn
```

**Ví dụ:**
```python
msg = Message(role="user", content="こんにちは")
```

---

### `NLPResult`

Kết quả từ module xử lý ngôn ngữ phụ trợ.

```python
@dataclass
class NLPResult:
    furigana: str    # Text với Kanji được chú thích cách đọc
    romaji: str      # Phiên âm Latin toàn bộ câu
    translation: str # Bản dịch (tiếng Việt)
```

**Ví dụ:**
```python
result = NLPResult(
    furigana="お 元気(げんき) ですか？",
    romaji="Ogenki desu ka?",
    translation="Bạn có khỏe không?"
)
```

---

### `Session`

Quản lý trạng thái và lịch sử của một cuộc hội thoại.

```python
@dataclass
class Session:
    session_id: str
    history: List[Message] = field(default_factory=list)
```

#### Methods

**`add_message(role: str, content: str) -> None`**

Thêm một tin nhắn mới vào lịch sử.

```python
session = Session(session_id="abc-123")
session.add_message(role="user", content="こんにちは")
session.add_message(role="assistant", content="こんにちは！")
```

**`get_context() -> List[Message]`**

Trả về toàn bộ lịch sử hội thoại để đưa vào LLM.

```python
context = session.get_context()
# [Message(role="user", content="こんにちは"),
#  Message(role="assistant", content="こんにちは！")]
```

> **Lưu ý:** Phiên bản hiện tại trả về toàn bộ lịch sử. Phase 1 sẽ thêm cơ chế sliding window để tránh vượt context window của LLM.

---

## Interfaces (`src/core/interfaces.py`)

Tất cả interfaces đều là Abstract Base Classes (ABC). Mọi implementation đều phải kế thừa và implement đầy đủ các abstract method.

### `BaseASR`

Interface cho module Automatic Speech Recognition.

```python
class BaseASR(ABC):
    @abstractmethod
    def transcribe(self, audio_data: bytes) -> str: ...
```

#### `transcribe(audio_data: bytes) -> str`

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `audio_data` | `bytes` | Dữ liệu âm thanh thô (PCM, WAV, WebM...) |

| Trả về | Kiểu | Mô tả |
|--------|------|-------|
| Text A | `str` | Văn bản đã nhận dạng (tiếng Nhật hoặc tiếng Việt) |

**Ví dụ implementation tối giản:**
```python
class MyASR(BaseASR):
    def transcribe(self, audio_data: bytes) -> str:
        # Gọi API hoặc model local
        return recognized_text
```

---

### `BaseLLM`

Interface cho module Large Language Model.

```python
class BaseLLM(ABC):
    @abstractmethod
    def generate_response(self, context: List[Message]) -> str: ...
```

#### `generate_response(context: List[Message]) -> str`

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `context` | `List[Message]` | Toàn bộ lịch sử hội thoại, kết quả của `session.get_context()` |

| Trả về | Kiểu | Mô tả |
|--------|------|-------|
| Text B | `str` | Phản hồi AI hoàn chỉnh |

**Lưu ý về context:**
- Phần tử đầu tiên thường là system message (nếu cần).
- Thứ tự: `[system?, user, assistant, user, assistant, ...]` — xen kẽ user/assistant.
- Implementation cần tự xử lý giới hạn token (cắt ngắn lịch sử nếu cần).

**Ví dụ implementation tối giản:**
```python
class MyLLM(BaseLLM):
    def generate_response(self, context: List[Message]) -> str:
        messages = [{"role": m.role, "content": m.content} for m in context]
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return response.choices[0].message.content
```

---

### `BaseTTS`

Interface cho module Text-to-Speech.

```python
class BaseTTS(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> bytes: ...
```

#### `synthesize(text: str) -> bytes`

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `text` | `str` | Văn bản tiếng Nhật cần đọc (Text B hoặc từng câu khi streaming) |

| Trả về | Kiểu | Mô tả |
|--------|------|-------|
| Audio | `bytes` | Dữ liệu âm thanh (MP3, WAV, OGG...) |

**Ví dụ implementation tối giản:**
```python
class MyTTS(BaseTTS):
    def synthesize(self, text: str) -> bytes:
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )
        return response.content
```

---

### `BaseNLP`

Interface cho module xử lý ngôn ngữ phụ trợ (furigana, romaji, translation).

```python
class BaseNLP(ABC):
    @abstractmethod
    def process(self, text: str) -> NLPResult: ...
```

#### `process(text: str) -> NLPResult`

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `text` | `str` | Text B (phản hồi AI cần phân tích) |

| Trả về | Kiểu | Mô tả |
|--------|------|-------|
| `NLPResult` | `NLPResult` | furigana, romaji, translation |

**Ví dụ implementation tối giản:**
```python
class MyNLP(BaseNLP):
    def process(self, text: str) -> NLPResult:
        converter = pykakasi.kakasi()
        result = converter.convert(text)
        furigana = build_furigana(result)
        romaji = build_romaji(result)
        translation = translate_to_vietnamese(text)
        return NLPResult(furigana=furigana, romaji=romaji, translation=translation)
```

---

## Engine (`src/engine.py`)

### `KaiwaEngine`

Bộ điều phối trung tâm, orchestrate toàn bộ pipeline.

```python
class KaiwaEngine:
    def __init__(
        self,
        asr: BaseASR,
        llm: BaseLLM,
        tts: BaseTTS,
        nlp: BaseNLP
    ) -> None: ...
```

#### Constructor

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `asr` | `BaseASR` | Component nhận dạng giọng nói |
| `llm` | `BaseLLM` | Component sinh phản hồi |
| `tts` | `BaseTTS` | Component tổng hợp giọng nói |
| `nlp` | `BaseNLP` | Component xử lý ngôn ngữ phụ trợ |

---

#### `interact(session: Session, audio_input: bytes) -> Dict[str, Any]`

Chạy một lượt hội thoại hoàn chỉnh.

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `session` | `Session` | Session hiện tại (trạng thái được cập nhật in-place) |
| `audio_input` | `bytes` | Giọng nói người dùng |

**Trả về `Dict[str, Any]`:**

| Key | Kiểu | Mô tả |
|-----|------|-------|
| `"text_input"` | `str` | Text A — lời người dùng đã transcribe |
| `"text_output"` | `str` | Text B — phản hồi AI |
| `"audio_output"` | `bytes` | Âm thanh phản hồi từ TTS |
| `"nlp"` | `NLPResult` | Furigana, Romaji, Translation |

> **Lưu ý side effect:** `interact()` tự động gọi `session.add_message()` cho cả user và assistant. Sau khi gọi, `session.history` đã được cập nhật.

**Ví dụ đầy đủ:**
```python
from src.core.schemas import Session
from src.engine import KaiwaEngine
from src.components.dummies import DummyASR, DummyLLM, DummyTTS, DummyNLP

engine = KaiwaEngine(
    asr=DummyASR(),
    llm=DummyLLM(),
    tts=DummyTTS(),
    nlp=DummyNLP()
)

session = Session(session_id="my-session")
result = engine.interact(session=session, audio_input=b"audio_bytes_here")

print(result["text_input"])        # Text A
print(result["text_output"])       # Text B
print(result["nlp"].translation)   # Bản dịch tiếng Việt
print(len(result["audio_output"])) # Kích thước audio bytes
```

---

## Dummy Implementations (`src/components/dummies.py`)

Dùng để kiểm tra data flow mà không cần API keys hay external services.

| Class | Kế thừa | Hành vi |
|-------|---------|---------|
| `DummyASR` | `BaseASR` | Luôn trả về `"こんにちは"` |
| `DummyLLM` | `BaseLLM` | Trả về `"こんにちは！お元気ですか？"` nếu context chứa `"こんにちは"` |
| `DummyTTS` | `BaseTTS` | Trả về `b"fake_audio_stream_data_based_on_input_text"` |
| `DummyNLP` | `BaseNLP` | Trả về `NLPResult` cứng nếu text khớp, otherwise placeholder |
