# Kiến trúc hệ thống (System Architecture)

Tài liệu này mô tả toàn bộ luồng dữ liệu, thiết kế thành phần và các quyết định kiến trúc của Koro Kaiwa AI.

---

## 1. Tổng quan kiến trúc

Hệ thống được xây dựng theo kiến trúc **Pipeline có thể hoán đổi thành phần** (Swappable Component Pipeline). Mỗi thành phần chính được định nghĩa qua một Abstract Base Class (ABC), cho phép thay thế bất kỳ implementation cụ thể nào (Whisper, GPT-4, Voicevox...) mà không ảnh hưởng đến logic điều phối trung tâm.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          KaiwaEngine                                │
│                                                                     │
│  Audio Input                                                        │
│      │                                                              │
│      ▼                                                              │
│  ┌────────┐    Text A    ┌────────┐    Text B    ┌────────┐        │
│  │  ASR   │ ──────────► │  LLM   │ ──────────► │  TTS   │        │
│  └────────┘             └────────┘             └────────┘        │
│                              │                      │              │
│                              │ Text B               │ Audio Output │
│                              ▼                      ▼              │
│                         ┌────────┐           Client / UI           │
│                         │  NLP   │  (async)                        │
│                         └────────┘                                 │
│                              │                                     │
│                     Furigana + Romaji                               │
│                        + Translation                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Luồng dữ liệu chính (Main Pipeline)

```
Input (Voice) → ASR → Text A → LLM → Text B → TTS → Output (Voice)
```

| Bước | Thành phần | Input | Output | Ghi chú |
|------|-----------|-------|--------|---------|
| 1 | **ASR** | `bytes` (audio) | `str` (Text A) | Giọng nói → văn bản tiếng Nhật/Việt |
| 2 | **Session** | Text A | — | Lưu tin nhắn user vào lịch sử |
| 3 | **LLM** | `List[Message]` (context) | `str` (Text B) | Sinh phản hồi từ toàn bộ ngữ cảnh |
| 4 | **Session** | Text B | — | Lưu phản hồi AI vào lịch sử |
| 5 | **TTS** | `str` (Text B) | `bytes` (audio) | Văn bản → âm thanh tiếng Nhật |
| 6 | **NLP** | `str` (Text B) | `NLPResult` | Phân tích ngôn ngữ học phụ trợ |

### Ưu tiên phản hồi về Client

Do trải nghiệm người dùng, các kết quả được gửi về theo thứ tự ưu tiên:

1. **Audio** — Trả về ngay lập tức (phản hồi TTS)
2. **Translation** — Bản dịch xuất hiện sau khi NLP hoàn thành
3. **Furigana** — Hướng dẫn đọc Kanji
4. **Romaji** — Phiên âm Latin

---

## 3. Luồng dữ liệu phụ trợ (Async NLP)

Trong khi người dùng đang nghe phản hồi âm thanh, backend chạy ngầm:

```
Text B → NLP Module → { furigana, romaji, translation }
                              │
                              └─► WebSocket push → UI update
```

- NLP chạy **bất đồng bộ** so với luồng chính, không block TTS.
- MVP hiện tại chạy tuần tự (sequential) để đơn giản hoá; Phase 1 sẽ chuyển sang `async/await` và task queue thực sự.

---

## 4. Các thành phần trừu tượng (Abstract Components)

Tất cả interfaces được định nghĩa trong [src/core/interfaces.py](../src/core/interfaces.py).

### 4.1 BaseASR

```python
class BaseASR(ABC):
    def transcribe(self, audio_data: bytes) -> str: ...
```

- Nhận luồng/file âm thanh dưới dạng `bytes`.
- Trả về chuỗi văn bản (tiếng Nhật hoặc tiếng Việt).
- Ví dụ implementation thực: OpenAI Whisper, Google Cloud STT.

### 4.2 BaseLLM

```python
class BaseLLM(ABC):
    def generate_response(self, context: List[Message]) -> str: ...
```

- Nhận toàn bộ lịch sử hội thoại dưới dạng danh sách `Message`.
- Trả về chuỗi phản hồi (Text B).
- Phải xử lý context window: giới hạn số lượng tin nhắn đưa vào để tránh vượt token limit.
- Ví dụ implementation thực: OpenAI GPT-4o, Google Gemini, Anthropic Claude.

### 4.3 BaseTTS

```python
class BaseTTS(ABC):
    def synthesize(self, text: str) -> bytes: ...
```

- Nhận văn bản tiếng Nhật.
- Trả về dữ liệu âm thanh dưới dạng `bytes`.
- Ví dụ implementation thực: Voicevox (giọng Nhật tự nhiên), OpenAI TTS.

### 4.4 BaseNLP

```python
class BaseNLP(ABC):
    def process(self, text: str) -> NLPResult: ...
```

- Nhận Text B.
- Trả về `NLPResult` với furigana, romaji và bản dịch.
- Chạy bất đồng bộ trong kiến trúc đầy đủ.
- Ví dụ implementation thực: pykakasi/Kuroshiro (furigana/romaji), Google Translate API (translation).

---

## 5. Mô hình dữ liệu (Data Models)

Tất cả schemas được định nghĩa trong [src/core/schemas.py](../src/core/schemas.py).

### Message

```python
@dataclass
class Message:
    role: str     # "user" hoặc "assistant"
    content: str  # nội dung tin nhắn
```

Đơn vị cơ bản của lịch sử hội thoại. `role` theo quy ước của OpenAI Chat API để tương thích với hầu hết LLM providers.

### NLPResult

```python
@dataclass
class NLPResult:
    furigana: str    # Text B với Kanji được chú thích cách đọc
    romaji: str      # Phiên âm Latin toàn bộ câu
    translation: str # Bản dịch tiếng Việt
```

### Session

```python
@dataclass
class Session:
    session_id: str
    history: List[Message]

    def add_message(self, role: str, content: str) -> None: ...
    def get_context(self) -> List[Message]: ...
```

Quản lý toàn bộ ngữ cảnh hội thoại. `get_context()` hiện trả về toàn bộ lịch sử — Phase 1 sẽ thêm cơ chế cắt ngắn (truncation/sliding window) để tránh vượt context window của LLM.

---

## 6. KaiwaEngine — Bộ điều phối trung tâm

Định nghĩa tại [src/engine.py](../src/engine.py). Nhận 4 components qua **Dependency Injection** trong constructor:

```python
engine = KaiwaEngine(asr=asr, llm=llm, tts=tts, nlp=nlp)
result = engine.interact(session=session, audio_input=audio_bytes)
```

Phương thức `interact()` trả về:

```python
{
    "text_input":   str,        # Text A - lời người dùng đã transcribe
    "text_output":  str,        # Text B - phản hồi AI
    "audio_output": bytes,      # Âm thanh phản hồi từ TTS
    "nlp":          NLPResult   # Furigana, Romaji, Translation
}
```

---

## 7. Kiến trúc tương lai — Phase 2 (Voice-to-Voice)

Phase 2 thay thế toàn bộ pipeline 3 bước (ASR → LLM → TTS) bằng một mô hình Speech-to-Speech duy nhất:

```
Input (Voice) → S2S End-to-End Model → Output (Voice)
                        │
                        └─► Text Decoder → NLP (async)
```

**Lợi ích:**
- Loại bỏ độ trễ tích lũy từ 3 bước riêng biệt.
- Giữ nguyên đặc tính vật lý của giọng nói (ngữ điệu, cảm xúc, nhịp điệu).
- Phản hồi tự nhiên hơn trong hội thoại thời gian thực.

Chi tiết xem [phase2/research_and_development.md](phase2/research_and_development.md).

---

## 8. Nguyên tắc thiết kế

| Nguyên tắc | Áp dụng |
|------------|---------|
| **Strategy Pattern** | Mỗi ABC (BaseASR, BaseLLM...) là một strategy có thể hoán đổi |
| **Dependency Injection** | KaiwaEngine không tự tạo components, nhận từ bên ngoài |
| **Separation of Concerns** | Main pipeline (ASR→LLM→TTS) tách biệt hoàn toàn với NLP phụ trợ |
| **Session Isolation** | Mỗi cuộc hội thoại có Session riêng, độc lập với nhau |
| **Interface-first** | Định nghĩa contract (ABC) trước, implementation sau |
