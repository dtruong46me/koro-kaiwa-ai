# Giai đoạn 1: Hướng dẫn triển khai MVP

Tài liệu mô tả kiến trúc kỹ thuật chi tiết, lựa chọn công nghệ và luồng xử lý cho Phase 1.

---

## 1. Tổng quan thành phần

### 1.1 ASR — Nhận dạng giọng nói

| Tiêu chí | Chi tiết |
|----------|---------|
| **Input** | `bytes` — luồng âm thanh từ microphone (PCM/WAV/WebM) |
| **Output** | `str` — văn bản tiếng Nhật hoặc tiếng Việt (Text A) |
| **Interface** | Kế thừa `BaseASR`, implement `transcribe(audio_data: bytes) -> str` |

**Công nghệ đề xuất:**

- **OpenAI Whisper** (`openai-whisper` local hoặc `openai` API): Hỗ trợ tiếng Nhật và tiếng Việt tốt, model `large-v3` cho độ chính xác cao nhất.
- **Google Cloud Speech-to-Text**: Phù hợp khi cần độ trễ thấp hơn trên cloud.

**Lưu ý triển khai:**
- Cần chuẩn hoá format audio trước khi đưa vào ASR (sample rate 16kHz, mono).
- Trong streaming mode: gom chunk nhỏ (e.g. 100ms) → VAD (Voice Activity Detection) → gửi khi phát hiện khoảng lặng.

```python
# Ví dụ skeleton implementation
class WhisperASR(BaseASR):
    def __init__(self, model_name: str = "large-v3"):
        self.model = whisper.load_model(model_name)

    def transcribe(self, audio_data: bytes) -> str:
        # Chuyển bytes → numpy array → whisper.transcribe()
        ...
```

---

### 1.2 LLM — Xử lý hội thoại

| Tiêu chí | Chi tiết |
|----------|---------|
| **Input** | `List[Message]` — lịch sử hội thoại đầy đủ |
| **Output** | `str` — văn bản phản hồi (Text B) |
| **Interface** | Kế thừa `BaseLLM`, implement `generate_response(context: List[Message]) -> str` |

**Công nghệ đề xuất:**
- **OpenAI GPT-4o / GPT-4o-mini**: Hiệu năng cao, hỗ trợ tiếng Nhật tốt.
- **Google Gemini 2.5 Flash**: Chi phí thấp, tốc độ nhanh.
- **Anthropic Claude 3.5 Haiku**: Cân bằng tốc độ và chất lượng.

**System Prompt mẫu:**
```
Bạn là Koro-chan, người bạn thân thiện giúp người dùng luyện tiếng Nhật.
Luôn trả lời bằng tiếng Nhật tự nhiên, phù hợp với trình độ người dùng.
Nếu người dùng nói tiếng Việt, hãy khuyến khích chuyển sang tiếng Nhật
nhưng vẫn trả lời để duy trì cuộc trò chuyện.
```

**Quản lý Context Window:**
```python
MAX_HISTORY_MESSAGES = 20  # Giữ tối đa N tin nhắn gần nhất

def get_trimmed_context(session: Session) -> List[Message]:
    history = session.get_context()
    return history[-MAX_HISTORY_MESSAGES:]  # Sliding window
```

**Streaming response** (Phase 1 — nên implement):
- Gọi API với `stream=True`, nhận từng token.
- Gom thành câu hoàn chỉnh (dựa trên dấu `。`, `！`, `？`).
- Gửi mỗi câu sang TTS ngay khi hoàn chỉnh thay vì đợi Text B đầy đủ.

---

### 1.3 TTS — Tổng hợp giọng nói

| Tiêu chí | Chi tiết |
|----------|---------|
| **Input** | `str` — văn bản tiếng Nhật (Text B hoặc từng câu trong streaming) |
| **Output** | `bytes` — dữ liệu âm thanh (MP3/WAV) |
| **Interface** | Kế thừa `BaseTTS`, implement `synthesize(text: str) -> bytes` |

**Công nghệ đề xuất:**
- **Voicevox** (local, miễn phí): Giọng Nhật tự nhiên, nhiều nhân vật, phù hợp cho học ngôn ngữ. API REST đơn giản.
- **OpenAI TTS** (`tts-1` / `tts-1-hd`): Chất lượng cao, dễ tích hợp, giọng `nova` phù hợp tiếng Nhật.

**Tối ưu streaming:**
- Với LLM streaming: TTS nhận từng câu và bắt đầu tổng hợp song song với việc LLM vẫn đang sinh tiếp.
- Client phát audio theo queue, đảm bảo liên tục.

---

### 1.4 NLP — Xử lý ngôn ngữ phụ trợ (Async)

| Tiêu chí | Chi tiết |
|----------|---------|
| **Input** | `str` — Text B đầy đủ |
| **Output** | `NLPResult` — furigana, romaji, translation |
| **Interface** | Kế thừa `BaseNLP`, implement `process(text: str) -> NLPResult` |

**Công nghệ đề xuất:**
- **pykakasi**: Chuyển đổi Kanji → Hiragana/Romaji, thuần Python, không cần external service.
- **Kuroshiro + kuromoji**: Furigana chất lượng cao hơn (Node.js).
- **Google Translate API / DeepL API**: Bản dịch tiếng Việt.

**Ví dụ kết quả NLP:**
```
Input:  "こんにちは！お元気ですか？"
Output:
  furigana:    "こんにちは！お 元気(げんき) ですか？"
  romaji:      "Konnichiwa! Ogenki desu ka?"
  translation: "Xin chào! Bạn có khỏe không?"
```

---

## 2. Luồng xử lý chi tiết

### 2.1 Luồng chính (Real-time, có streaming)

```
Client (Browser)
    │ WebSocket: audio chunk (bytes)
    ▼
Backend (FastAPI)
    │
    ├─► ASR.transcribe(audio_data) → Text A
    │
    ├─► session.add_message("user", text_a)
    │
    ├─► LLM.generate_response(context) → stream of tokens
    │       │
    │       └─► Gom token → câu hoàn chỉnh
    │               │
    │               └─► TTS.synthesize(sentence) → audio_chunk
    │                           │
    │                           └─► WebSocket push: audio_chunk → Client
    │
    └─► session.add_message("assistant", full_text_b)
```

### 2.2 Luồng phụ trợ NLP (Bất đồng bộ)

```
Backend nhận full Text B
    │
    └─► BackgroundTask: NLP.process(text_b)
            │
            └─► NLPResult { furigana, romaji, translation }
                    │
                    └─► WebSocket push: nlp_data → Client UI update
```

---

## 3. Backend Architecture

### Công nghệ đề xuất: FastAPI (Python)

FastAPI phù hợp vì:
- Native async/await support.
- WebSocket built-in.
- Tương thích hoàn toàn với codebase Python hiện tại.
- `BackgroundTasks` cho NLP async đơn giản.

### Cấu trúc endpoint

```
POST   /sessions              → Tạo Session mới, trả về session_id
DELETE /sessions/{session_id} → Kết thúc và xoá Session
WS     /ws/{session_id}       → WebSocket hội thoại chính
```

### WebSocket message format

**Client → Server:**
```json
{ "type": "audio", "data": "<base64-encoded audio bytes>" }
```

**Server → Client (nhiều message):**
```json
{ "type": "audio_chunk",  "data": "<base64 audio>" }
{ "type": "text_input",   "data": "こんにちは" }
{ "type": "text_output",  "data": "こんにちは！お元気ですか？" }
{ "type": "nlp_result",   "furigana": "...", "romaji": "...", "translation": "..." }
```

---

## 4. Session Management

### Lưu trữ trong Phase 1

| Lựa chọn | Ưu điểm | Nhược điểm |
|----------|---------|-----------|
| **Redis** | Cực nhanh, TTL tự động, pub/sub | Cần thêm infrastructure |
| **In-memory dict** | Đơn giản, không cần deps | Mất dữ liệu khi restart |
| **MongoDB** | Persistent, flexible schema | Chậm hơn cho đọc/ghi thường xuyên |

**Khuyến nghị:** Redis cho production, in-memory dict cho development/testing.

### Schema lưu trữ Session trong Redis

```
Key:   session:{session_id}
Value: JSON serialization của Session object
TTL:   3600 giây (tự động xoá sau 1 giờ không hoạt động)
```

---

## 5. Cấu trúc thư mục đề xuất (Phase 1)

```
koro-kaiwa-ai/
├── src/
│   ├── core/
│   │   ├── interfaces.py      # ABCs (không thay đổi)
│   │   └── schemas.py         # Data models (không thay đổi)
│   ├── components/
│   │   ├── dummies.py         # Giữ nguyên cho testing
│   │   ├── asr/
│   │   │   ├── whisper_asr.py
│   │   │   └── google_asr.py
│   │   ├── llm/
│   │   │   ├── openai_llm.py
│   │   │   └── gemini_llm.py
│   │   ├── tts/
│   │   │   ├── voicevox_tts.py
│   │   │   └── openai_tts.py
│   │   └── nlp/
│   │       └── kakasi_nlp.py
│   ├── engine.py              # KaiwaEngine (mở rộng để hỗ trợ streaming)
│   └── api/
│       ├── main.py            # FastAPI app
│       ├── routes/
│       │   ├── sessions.py    # REST endpoints
│       │   └── websocket.py   # WebSocket endpoint
│       └── session_store.py   # Redis / in-memory adapter
├── tests/
│   ├── test_engine.py
│   ├── test_components/
│   └── test_api/
├── main.py                    # CLI entry point (giữ nguyên)
└── requirements.txt
```

---

## 6. Dependencies (Phase 1)

```txt
# Backend
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
websockets>=12.0
redis>=5.0.0

# ASR
openai-whisper>=20231117
# hoặc: google-cloud-speech>=2.24.0

# LLM
openai>=1.12.0
# hoặc: google-generativeai>=0.4.0
# hoặc: anthropic>=0.20.0

# TTS
# voicevox: REST API, không cần Python package
openai>=1.12.0  # openai.audio.speech

# NLP
pykakasi>=2.2.1
# Translation: requests + Google Translate API hoặc deepl>=1.17.0
```
