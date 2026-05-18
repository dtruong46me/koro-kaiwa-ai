"""
WebSocket endpoint — xử lý hội thoại real-time với streaming.

Protocol:
  Client → Server:  { "type": "audio", "data": "<base64 audio bytes>" }
  Server → Client:  Nhiều message theo thứ tự:
    { "type": "text_input",  "data": "<Text A>" }
    { "type": "audio_chunk", "data": "<base64 MP3>", "text": "<câu đã TTS>" }  (×N)
    { "type": "text_output", "data": "<Text B đầy đủ>" }
    { "type": "nlp_result",  "furigana": "...", "romaji": "...", "translation": "..." }
    { "type": "error",       "message": "..." }  (khi có lỗi)
"""
from __future__ import annotations

import base64

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...core.schemas import NLPResult
from ..session_store import BaseSessionStore
from ...engine import KaiwaEngine

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Nhận audio từ client, stream phản hồi theo thứ tự:
    text_input → audio_chunk(s) → text_output → nlp_result.
    """
    await websocket.accept()

    engine: KaiwaEngine = websocket.app.state.engine
    store: BaseSessionStore = websocket.app.state.session_store

    session = store.get(session_id)
    if session is None:
        await websocket.send_json({"type": "error", "message": "Session không tồn tại."})
        await websocket.close(code=4004)
        return

    try:
        while True:
            payload = await websocket.receive_json()

            if payload.get("type") != "audio":
                continue

            audio_bytes = base64.b64decode(payload["data"])

            for event in engine.stream_interact(session=session, audio_input=audio_bytes):
                if event.type == "text_input":
                    await websocket.send_json({
                        "type": "text_input",
                        "data": event.data,
                    })

                elif event.type == "audio_chunk":
                    await websocket.send_json({
                        "type": "audio_chunk",
                        "data": base64.b64encode(event.data).decode(),
                        "text": event.text,
                    })

                elif event.type == "text_output":
                    await websocket.send_json({
                        "type": "text_output",
                        "data": event.data,
                    })

                elif event.type == "nlp_result":
                    nlp: NLPResult = event.data
                    await websocket.send_json({
                        "type": "nlp_result",
                        "furigana": nlp.furigana,
                        "romaji": nlp.romaji,
                        "translation": nlp.translation,
                    })

            # Lưu session sau mỗi lượt hội thoại hoàn thành
            store.save(session)

    except WebSocketDisconnect:
        store.save(session)
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        store.save(session)
        await websocket.close(code=1011)
