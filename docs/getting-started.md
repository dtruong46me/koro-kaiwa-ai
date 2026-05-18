# Bắt đầu nhanh (Getting Started)

Hướng dẫn cài đặt, chạy thử và hiểu luồng hoạt động của hệ thống Koro Kaiwa AI.

---

## 1. Yêu cầu hệ thống

- **Python 3.9+**
- Không có dependency nào ngoài thư viện chuẩn của Python ở giai đoạn MVP hiện tại.

Kiểm tra phiên bản Python:
```bash
python --version
```

---

## 2. Chạy MVP

Clone repository và chạy trực tiếp:

```bash
git clone <repo-url>
cd koro-kaiwa-ai
python main.py
```

### Kết quả mong đợi

```
Khởi động hệ thống Koro Kaiwa AI MVP...

--- Bắt đầu lượt hội thoại cho Session: session_MVP_001 ---
[ASR Module] Đang xử lý Audio Data...
[Engine Flow] User (Text A) : こんにちは
[LLM Module] Đang sinh câu trả lời nhận thức theo Context...
[Engine Flow] AI   (Text B) : こんにちは！お元気ですか？
[TTS Module] Đang biến đổi Text -> Audio: 'こんにちは！お元気ですか？'
[Engine Flow] Đã sinh âm thanh phản hồi (TTS).
[NLP Module] Xử lý Text B để lấy Furigana/Romaji/Dịch: 'こんにちは！お元気ですか？'
[Engine Flow] Đã hoàn thành thông tin phụ trợ NLP.

=== KẾT QUẢ PHẢN HỒI VỀ CLIENT ===
- Lời nói của bạn (Transcribed): こんにちは
- Phản hồi của AI              : こんにちは！お元気ですか？
- Bản dịch phụ trợ (Translation): Xin chào! Bạn có khỏe không?
- Hướng dẫn đọc    (Furigana)  : こんにちは！お 元気(げんき) ですか？
- Phiên âm Latinh  (Romaji)    : Konnichiwa! Ogenki desu ka?
- File âm thanh    (Audio_Data): b'fake_audio_stream_data_based_on_input_text' (bytes)
==================================
```

---

## 3. Hiểu luồng hoạt động

### 3.1 main.py khởi tạo gì?

```python
# 1. Khởi tạo 4 Dummy components
asr = DummyASR()    # Trả về chuỗi cố định "こんにちは"
llm = DummyLLM()    # Trả về phản hồi dựa trên từ khoá trong input
tts = DummyTTS()    # Trả về bytes giả lập
nlp = DummyNLP()    # Trả về NLPResult giả lập

# 2. Khởi tạo engine (Dependency Injection)
engine = KaiwaEngine(asr=asr, llm=llm, tts=tts, nlp=nlp)

# 3. Tạo Session để quản lý lịch sử hội thoại
session = Session(session_id="session_MVP_001")

# 4. Gọi interact() với audio giả
result = engine.interact(session=session, audio_input=b"fake_user_mic_voice_data")
```

### 3.2 Dữ liệu di chuyển qua pipeline như thế nào?

```
b"fake_user_mic_voice_data"
        │ DummyASR.transcribe()
        ▼
"こんにちは"  (Text A)
        │ session.add_message("user", text_a)
        │ DummyLLM.generate_response(context)
        ▼
"こんにちは！お元気ですか？"  (Text B)
        │ session.add_message("assistant", text_b)
        │
        ├─► DummyTTS.synthesize(text_b) → b"fake_audio_stream..."
        └─► DummyNLP.process(text_b)   → NLPResult(furigana, romaji, translation)
```

---

## 4. Thay thế Dummy bằng implementation thực

Đây là bước tiếp theo sau khi MVP chạy thành công. Mỗi component thực phải kế thừa ABC tương ứng.

**Ví dụ: Thay DummyASR bằng Whisper**

```python
# src/components/asr/whisper_asr.py
import whisper
from src.core.interfaces import BaseASR

class WhisperASR(BaseASR):
    def __init__(self, model_name: str = "base"):
        self.model = whisper.load_model(model_name)

    def transcribe(self, audio_data: bytes) -> str:
        # Chuyển đổi bytes → numpy array → transcribe
        import numpy as np, io, soundfile as sf
        audio, _ = sf.read(io.BytesIO(audio_data))
        result = self.model.transcribe(audio, language="ja")
        return result["text"]
```

Sau đó trong `main.py`, chỉ cần đổi:
```python
# Trước
asr = DummyASR()

# Sau
from src.components.asr.whisper_asr import WhisperASR
asr = WhisperASR(model_name="large-v3")
```

Engine và Session không cần thay đổi gì. Đây là lợi ích của Dependency Injection + Strategy Pattern.

---

## 5. Cấu trúc project để điều hướng nhanh

| Cần làm gì | File cần đọc |
|------------|-------------|
| Hiểu kiến trúc tổng quan | [docs/architecture.md](architecture.md) |
| Thêm ASR/LLM/TTS mới | [src/core/interfaces.py](../src/core/interfaces.py) → tạo class kế thừa |
| Hiểu data models | [src/core/schemas.py](../src/core/schemas.py) |
| Xem engine điều phối | [src/engine.py](../src/engine.py) |
| Xem ví dụ implementation | [src/components/dummies.py](../src/components/dummies.py) |
| Kế hoạch Phase 1 | [docs/phase1/implementation_guide.md](phase1/implementation_guide.md) |
| Kế hoạch Phase 2 | [docs/phase2/research_and_development.md](phase2/research_and_development.md) |
| Reference API đầy đủ | [docs/api-reference.md](api-reference.md) |

---

## 6. Chạy nhiều lượt hội thoại

Để kiểm tra quản lý lịch sử hội thoại, gọi `interact()` nhiều lần trên cùng một Session:

```python
session = Session(session_id="test_multi_turn")

# Lượt 1
result1 = engine.interact(session=session, audio_input=b"audio_1")

# Lượt 2 — LLM nhận được context từ lượt 1
result2 = engine.interact(session=session, audio_input=b"audio_2")

# Kiểm tra lịch sử
print(session.history)
# [Message(role="user", ...), Message(role="assistant", ...),
#  Message(role="user", ...), Message(role="assistant", ...)]
```
