"""
FastAPI application — entry point cho server.
Chạy: uvicorn src.api.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .dependencies import build_engine, build_session_store
from .routes import sessions, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo engine và session store một lần khi server start."""
    app.state.engine = build_engine()
    app.state.session_store = build_session_store()
    yield
    # Cleanup nếu cần (đóng connections, giải phóng model...)


app = FastAPI(
    title="Koro Kaiwa AI",
    description="Hệ thống hội thoại AI hỗ trợ học tiếng Nhật.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(sessions.router)
app.include_router(websocket.router)


@app.get("/health", tags=["Health"])
async def health():
    """Kiểm tra server đang hoạt động."""
    return {"status": "ok"}
