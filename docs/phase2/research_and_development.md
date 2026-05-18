# Giai đoạn 2: Nghiên cứu và Phát triển AI nâng cao

Tài liệu mô tả các hướng nghiên cứu, phương pháp kỹ thuật và lộ trình tích hợp các tính năng AI chuyên sâu vào hệ thống.

---

## 1. Phân tích phát âm (Pronunciation Assessment)

**Mục tiêu:** Phát hiện và báo cáo lỗi phát âm của người dùng theo thời gian thực, bao gồm lỗi âm vị, pitch accent và nhịp điệu.

### 1.1 Pipeline phân tích

```
Audio Input (User Voice)
        │
        ▼
  ┌────────────┐
  │    VAD     │  (Voice Activity Detection — tách từng từ/âm tiết)
  └────────────┘
        │
        ▼
  ┌────────────────────┐
  │  Forced Alignment  │  Căn chiếu sóng âm với chuỗi phoneme
  │  (Wav2Vec2 / MFA)  │
  └────────────────────┘
        │
        ▼
  ┌────────────────────┐
  │ Feature Extraction │  Pitch, Duration, Energy, Formants
  └────────────────────┘
        │
        ▼
  ┌────────────────────┐
  │  Comparison with   │  So sánh với phát âm chuẩn (native speaker reference)
  │  Reference Audio   │
  └────────────────────┘
        │
        ▼
  PronunciationReport { errors: [...], score: float }
```

### 1.2 Forced Alignment

**Montreal Forced Aligner (MFA):**
- Tool mạnh nhất hiện tại cho alignment ở cấp độ phoneme.
- Yêu cầu: Dictionary phát âm tiếng Nhật (CMU hoặc IPA-based).
- Output: TextGrid file với timestamp của từng phoneme.

**Wav2Vec2 (CTC-based):**
- Không cần dictionary, học trực tiếp từ audio.
- Model `facebook/wav2vec2-large-xlsr-53-japanese` cho tiếng Nhật.
- Nhanh hơn MFA, phù hợp real-time.

### 1.3 Đặc trưng Pitch Accent (tiếng Nhật)

Tiếng Nhật là ngôn ngữ **pitch accent** — cùng từ nhưng pitch pattern khác nhau tạo nghĩa khác nhau (e.g., 橋 "hashi" = cầu vs 箸 "hashi" = đũa).

```python
# Trích xuất F0 (fundamental frequency) bằng librosa
import librosa
f0, voiced_flag, voiced_probs = librosa.pyin(
    audio_signal,
    fmin=librosa.note_to_hz('C2'),
    fmax=librosa.note_to_hz('C7')
)
# So sánh F0 pattern của người dùng với reference
```

**Nguồn dữ liệu reference:**
- **JVS (Japanese Versatile Speech) Corpus**: 100 người đọc 100 câu mỗi người.
- **JSUT**: Japanese speech corpus cho TTS research.

### 1.4 Schema báo cáo lỗi

```python
@dataclass
class PronunciationError:
    phoneme: str          # Âm vị bị sai, e.g., "r" vs "l"
    position: int         # Vị trí trong câu (byte offset)
    error_type: str       # "substitution" | "deletion" | "pitch" | "rhythm"
    severity: float       # 0.0 (nhẹ) → 1.0 (nặng)
    suggestion: str       # Mô tả cách sửa

@dataclass
class PronunciationReport:
    overall_score: float          # 0.0 → 1.0
    errors: List[PronunciationError]
    rhythm_score: float
    pitch_score: float
```

---

## 2. Hệ thống phản hồi ngữ cảnh (Intelligent Tutor Feedback)

**Mục tiêu:** Tích hợp báo cáo phát âm vào luồng LLM để AI phản hồi như một giáo viên thực thụ.

### 2.1 Mở rộng BaseLLM

Phase 2 sẽ mở rộng interface `BaseLLM` (hoặc tạo `BaseTutorLLM`):

```python
class BaseTutorLLM(BaseLLM):
    @abstractmethod
    def generate_response(
        self,
        context: List[Message],
        pronunciation_report: Optional[PronunciationReport] = None
    ) -> str: ...
```

### 2.2 Logic quyết định phản hồi lỗi

LLM được hướng dẫn qua System Prompt để quyết định mức độ phản hồi:

| Điều kiện | Hành động |
|-----------|----------|
| `overall_score >= 0.85` | Không đề cập lỗi phát âm, hội thoại bình thường |
| `0.60 <= score < 0.85` | Nhắc nhở nhẹ, tiếp tục hội thoại: "Cách phát âm của bạn gần đúng rồi! Thử lại nhé..." |
| `score < 0.60` | Dừng lại và hướng dẫn: "Mình muốn chú ý đến cách bạn phát âm từ X..." |

**Ví dụ System Prompt mở rộng:**
```
Bạn là giáo viên tiếng Nhật thân thiện.

Khi có báo cáo phát âm, hãy:
- Nếu score >= 0.85: tiếp tục hội thoại bình thường.
- Nếu 0.60-0.85: lồng ghép một gợi ý nhẹ vào cuối câu trả lời.
- Nếu < 0.60: ưu tiên sửa lỗi trước khi tiếp tục hội thoại.

Báo cáo phát âm: {pronunciation_report}
```

---

## 3. Mô hình End-to-End Speech-to-Speech (S2S)

**Mục tiêu:** Thay thế pipeline 3 bước (ASR → LLM → TTS) bằng một mô hình duy nhất, giảm độ trễ và giữ nguyên đặc tính giọng nói.

### 3.1 Kiến trúc đề xuất

```
Input Voice → [Audio Encoder] → Audio Embeddings
                                        │
                               [Multimodal LLM Core]
                                        │
                                ┌───────┴────────┐
                           [Audio Decoder]   [Text Decoder]
                                │                   │
                           Output Voice         Text B (cho NLP async)
```

**Lý do cần Text Decoder song song:**
- NLP phụ trợ (furigana, romaji, translation) vẫn cần văn bản.
- Logging và debugging.
- Fallback khi audio decoder lỗi.

### 3.2 Foundation Models để Fine-tune

| Model | Điểm mạnh | Ghi chú |
|-------|-----------|---------|
| **Moshi (Kyutai)** | Real-time S2S, open-source | Tiếng Nhật cần fine-tune |
| **GPT-4o Audio** | Chất lượng cao, API sẵn sàng | Chi phí cao, ít control |
| **SeamlessM4T (Meta)** | Multimodal, multilingual | Phù hợp Nhật-Việt |
| **Qwen2-Audio** | Open-source, audio-native | Community đang phát triển |

### 3.3 Thu thập dữ liệu

**Dataset tối thiểu cho fine-tuning:**
- 100+ giờ hội thoại tiếng Nhật (Audio In → Audio Out).
- Cặp (audio người hỏi, audio AI trả lời) có chất lượng cao.
- Đa dạng topic: chào hỏi, mua sắm, hỏi đường, thời tiết...

**Nguồn dữ liệu:**
- JVS Corpus, JSUT, JSpeech.
- Synthetic data: dùng TTS chất lượng cao để tạo "ground truth" audio.
- Augmentation: thêm noise, reverb, speed variation để tăng robustness.

### 3.4 Lộ trình nghiên cứu

```
Bước 1: Baseline S2S
    └─► Fine-tune Moshi/SeamlessM4T với dataset tiếng Nhật
    └─► Đánh giá chất lượng: MOS score, WER, latency

Bước 2: Tích hợp thử nghiệm
    └─► Chạy song song với pipeline ASR→LLM→TTS
    └─► A/B testing: đánh giá trải nghiệm người dùng thực

Bước 3: Tối ưu hoá
    └─► Quantization (INT8/INT4) để giảm latency
    └─► Streaming output: bắt đầu phát audio trước khi model hoàn thành

Bước 4: Production deployment
    └─► Thay thế hoàn toàn pipeline cũ khi đủ chất lượng
```

---

## 4. Metrics đánh giá

### Chất lượng phát âm
- **Phoneme Error Rate (PER)**: Tỉ lệ phoneme bị nhận dạng sai.
- **Pitch Accuracy Score**: % pitch accent đúng trên tổng số từ.

### Chất lượng S2S Model
- **MOS (Mean Opinion Score)**: Đánh giá chủ quan từ người dùng (1-5).
- **Word Error Rate (WER)**: Độ chính xác transcription từ Text Decoder.
- **End-to-end Latency**: Thời gian từ khi user ngừng nói đến khi nhận được audio đầu tiên.

### Mục tiêu latency Phase 2
| Metric | Mục tiêu |
|--------|---------|
| Time-to-first-audio | < 800ms |
| Full response latency | < 2000ms |
| NLP completion | < 3000ms |
