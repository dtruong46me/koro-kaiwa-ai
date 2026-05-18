"""
REST endpoints cho quản lý Session.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...core.schemas import Session
from ..session_store import BaseSessionStore

router = APIRouter(prefix="/sessions", tags=["Sessions"])


class SessionResponse(BaseModel):
    session_id: str
    message: str


def _get_store(request: Request) -> BaseSessionStore:
    return request.app.state.session_store


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(request: Request):
    """Tạo phiên hội thoại mới, trả về session_id."""
    store = _get_store(request)
    session_id = str(uuid.uuid4())
    store.save(Session(session_id=session_id))
    return SessionResponse(session_id=session_id, message="Phiên hội thoại đã được tạo.")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, request: Request):
    """Kiểm tra phiên có tồn tại không."""
    store = _get_store(request)
    if not store.exists(session_id):
        raise HTTPException(status_code=404, detail="Session không tồn tại.")
    return SessionResponse(session_id=session_id, message="Session đang hoạt động.")


@router.delete("/{session_id}", response_model=SessionResponse)
async def delete_session(session_id: str, request: Request):
    """Xoá phiên hội thoại và toàn bộ lịch sử."""
    store = _get_store(request)
    if not store.exists(session_id):
        raise HTTPException(status_code=404, detail="Session không tồn tại.")
    store.delete(session_id)
    return SessionResponse(session_id=session_id, message="Phiên hội thoại đã được xoá.")
