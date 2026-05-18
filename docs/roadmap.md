# Lộ trình phát triển (Roadmap)

Dự án Koro Kaiwa AI được chia làm hai giai đoạn chính, đi từ MVP hoàn chỉnh đến hệ thống AI học ngôn ngữ thông minh thế hệ mới.

---

## Trạng thái hiện tại: Pre-Phase 1 (MVP Data Flow)

**Mục tiêu:** Xác nhận kiến trúc hoạt động đúng trước khi tích hợp API thực.

- [x] Định nghĩa Abstract Base Classes (`BaseASR`, `BaseLLM`, `BaseTTS`, `BaseNLP`)
- [x] Xây dựng Data Models (`Message`, `NLPResult`, `Session`)
- [x] Triển khai `KaiwaEngine` điều phối toàn bộ pipeline
- [x] Tạo Dummy implementations để kiểm tra luồng dữ liệu end-to-end
- [x] Entry point `main.py` chạy và in kết quả đầy đủ

---

## Giai đoạn 1: MVP Hoàn chỉnh

**Mục tiêu:** Thay thế toàn bộ Dummy components bằng API thực, xây dựng backend có thể sử dụng được.

### 1.1 Tích hợp ASR thực
- [ ] Implement `WhisperASR` hoặc `GoogleASR` kế thừa `BaseASR`
- [ ] Hỗ trợ streaming audio từ microphone qua WebSocket
- [ ] Xử lý tiếng Nhật và tiếng Việt

### 1.2 Tích hợp LLM thực
- [ ] Implement `OpenAILLM` hoặc `GeminiLLM` kế thừa `BaseLLM`
- [ ] System prompt thiết lập AI đóng vai người bạn luyện tiếng Nhật
- [ ] Cơ chế cắt ngắn lịch sử (sliding window) tránh vượt context window
- [ ] Hỗ trợ streaming response (trả về từng token thay vì chờ toàn bộ)

### 1.3 Tích hợp TTS thực
- [ ] Implement `VoicevoxTTS` hoặc `OpenAITTS` kế thừa `BaseTTS`
- [ ] Streaming audio output: TTS xử lý từng câu và gửi ngay, không đợi Text B đầy đủ

### 1.4 Tích hợp NLP thực
- [ ] Implement `KakashiNLP` hoặc tương đương kế thừa `BaseNLP`
- [ ] Furigana: chú thích cách đọc Kanji (pykakasi / Kuroshiro)
- [ ] Romaji: phiên âm Latin toàn bộ câu
- [ ] Translation: dịch sang tiếng Việt (Google Translate API / DeepL)

### 1.5 Backend & Session Management
- [ ] Xây dựng FastAPI backend với WebSocket endpoint
- [ ] Tích hợp Redis để lưu Session (in-memory, truy xuất nhanh)
- [ ] REST API để tạo/kết thúc session
- [ ] Chạy NLP bất đồng bộ thực sự (FastAPI BackgroundTasks hoặc Celery)

### 1.6 Giao diện người dùng (UI)
- [ ] Giao diện web cơ bản: nút record, hiển thị văn bản, audio player
- [ ] Cập nhật bất đồng bộ: Audio trước → Translation → Furigana → Romaji
- [ ] Hiển thị lịch sử hội thoại trong phiên

---

## Giai đoạn 2: Trợ lý luyện phát âm & Giao tiếp thế hệ mới

**Mục tiêu:** Tích hợp AI chuyên sâu để phân tích và cải thiện phát âm người dùng.

### 2.1 Phân tích phát âm (Pronunciation Assessment)
- [ ] Áp dụng Forced Alignment (Wav2Vec2 / Montreal Forced Aligner)
- [ ] Trích xuất đặc trưng: Pitch Accent, nhịp điệu (Rhythm), trường độ (Duration)
- [ ] Xây dựng pipeline so sánh với phát âm chuẩn (native speaker reference)
- [ ] Tạo báo cáo lỗi chi tiết: vị trí sai, loại lỗi, mức độ nghiêm trọng

### 2.2 Hệ thống phản hồi thông minh (Tutor Feedback)
- [ ] Mở rộng `BaseLLM.generate_response()` nhận thêm `pronunciation_report`
- [ ] System prompt: LLM đóng vai giáo viên, quyết định khi nào nhắc nhở lỗi
- [ ] Phân loại mức độ phản hồi: bỏ qua / nhắc nhẹ / yêu cầu phát âm lại

### 2.3 Mô hình Speech-to-Speech (S2S) End-to-End
- [ ] Nghiên cứu và thu thập dataset hội thoại Audio-In → Audio-Out
- [ ] Fine-tune Multimodal Foundation Model (Audio-native LLM)
- [ ] Tích hợp Text Decoder song song để vẫn có dữ liệu cho NLP phụ trợ
- [ ] Thay thế pipeline ASR → LLM → TTS bằng S2S khi đủ chất lượng

Chi tiết kỹ thuật xem [phase2/research_and_development.md](phase2/research_and_development.md).

---

## Tóm tắt theo giai đoạn

| Giai đoạn | Trạng thái | Kết quả chính |
|-----------|-----------|---------------|
| Pre-Phase 1 | ✅ Hoàn thành | Kiến trúc và data flow xác nhận hoạt động |
| Phase 1 | 🔄 Đang phát triển | Backend thực, API tích hợp, UI cơ bản |
| Phase 2 | 📋 Nghiên cứu | Phân tích phát âm, S2S model |
