# Koro Kaiwa AI (コロ会話AI)

**Koro Kaiwa AI** là một hệ thống Trí tuệ Nhân tạo đối thoại tiếng Nhật được phát triển bởi nhóm Koro Kaiwa. Mục tiêu của dự án là tạo ra một trợ lý AI có khả năng giao tiếp tự nhiên, hiệu quả bằng tiếng Nhật, giúp người dùng học tập, thực hành và nâng cao khả năng ngôn ngữ của mình.

## Tổng quan dự án

Dự án ứng dụng các công nghệ xử lý giọng nói và ngôn ngữ tự nhiên tiên tiến để mô phỏng một cuộc hội thoại thực tế. Về cơ bản, hệ thống sẽ lắng nghe giọng nói của người dùng, chuyển đổi thành văn bản, hiểu ngữ cảnh dựa trên lịch sử hội thoại, sinh ra câu trả lời phù hợp, và cuối cùng là phản hồi lại bằng giọng nói.

Đồng thời, để hỗ trợ việc học tiếng Nhật tốt nhất, hệ thống còn cung cấp thêm thông tin về **Furigana, Romaji và Bản dịch** cho các câu trả lời của AI một cách bất đồng bộ để đảm bảo trải nghiệm giao tiếp không bị gián đoạn.

## Tài liệu (Documentation)

Chi tiết về thiết kế hệ thống và định hướng phát triển có thể tham khảo trong thư mục `/docs`:
- [Kiến trúc hệ thống (Architecture)](docs/architecture.md)
- [Lộ trình phát triển (Roadmap)](docs/roadmap.md)

## Cấu trúc hoạt động cơ bản (MVP)

1. **ASR (Automatic Speech Recognition):** Chuyển đổi giọng nói người dùng thành văn bản (Text A).
2. **LLM (Large Language Model):** Xử lý văn bản đầu vào kết hợp lịch sử hội thoại để sinh ra văn bản phản hồi (Text B).
3. **TTS (Text-to-Speech):** Chuyển đổi văn bản phản hồi thành giọng nói để phát cho người dùng.
4. **Xử lý ngôn ngữ phụ trợ (Asynchronous):** Một tiến trình chạy ngầm sẽ lấy Text B để xử lý và trích xuất Furigana, Romaji và Translation, sau đó cập nhật lên giao diện.

---
*Dự án đang trong giai đoạn phát triển tích cực.*