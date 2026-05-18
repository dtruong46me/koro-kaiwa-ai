"""
CLI entry point — chạy hội thoại demo bằng Dummy components (không cần API keys).
Dùng để kiểm tra pipeline end-to-end trước khi tích hợp API thực.

Chạy:
    python main.py              # Demo với Dummy components
    python main.py --real       # Demo với components thực (cần .env)
    python main.py --server     # Khởi động FastAPI server
"""
from __future__ import annotations

import argparse
import sys

# Đảm bảo stdout dùng UTF-8 trên mọi platform (đặc biệt Windows cmd/PowerShell)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]


def run_dummy_demo() -> None:
    """Chạy demo với Dummy components."""
    from src.components.dummies import DummyASR, DummyLLM, DummyNLP, DummyTTS
    from src.core.schemas import Session
    from src.engine import KaiwaEngine

    print("=" * 55)
    print("  Koro Kaiwa AI — Demo (Dummy Mode)")
    print("=" * 55)

    engine = KaiwaEngine(
        asr=DummyASR(),
        llm=DummyLLM(),
        tts=DummyTTS(),
        nlp=DummyNLP(),
    )
    session = Session(session_id="demo-001")

    # Giả lập 2 lượt hội thoại để kiểm tra session history
    for turn, fake_audio in enumerate(
        [b"fake_audio_1", b"fake_audio_2"], start=1
    ):
        print(f"\n--- Lượt {turn} ---")
        result = engine.interact(session=session, audio_input=fake_audio)
        print(f"\nKết quả:")
        print(f"  Bạn nói      : {result.text_input}")
        print(f"  AI trả lời   : {result.text_output}")
        print(f"  Bản dịch     : {result.nlp.translation}")
        print(f"  Furigana     : {result.nlp.furigana}")
        print(f"  Romaji       : {result.nlp.romaji}")
        print(f"  Audio (bytes): {result.audio_output[:30]}...")

    print(f"\n  Lịch sử session: {len(session.history)} tin nhắn")
    print("=" * 55)


def run_real_demo() -> None:
    """Chạy demo với components thực từ .env."""
    from src.api.dependencies import build_engine
    from src.core.schemas import Session

    print("Đang khởi tạo components thực (đọc từ .env)...")
    engine = build_engine()
    session = Session(session_id="real-demo-001")

    # Trong thực tế, audio_input là bytes từ microphone
    # Ở đây dùng file WAV nếu có, không thì báo lỗi hướng dẫn
    print("\nCần file audio WAV. Chạy demo thực bằng API: python -m uvicorn src.api.main:app --reload")
    print("Sau đó tạo session: POST /sessions")
    print("Kết nối WebSocket: ws://localhost:8000/ws/{session_id}")


def run_server() -> None:
    """Khởi động FastAPI server."""
    import uvicorn  # type: ignore
    from src.config import get_settings
    s = get_settings()
    uvicorn.run("src.api.main:app", host=s.host, port=s.port, reload=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Koro Kaiwa AI")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--real",   action="store_true", help="Dùng components thực từ .env")
    group.add_argument("--server", action="store_true", help="Khởi động FastAPI server")
    args = parser.parse_args()

    if args.server:
        run_server()
    elif args.real:
        run_real_demo()
    else:
        run_dummy_demo()
