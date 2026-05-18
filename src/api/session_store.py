"""
Session store — lưu trữ và truy xuất Session objects.
Hai implementation: InMemorySessionStore (dev) và RedisSessionStore (production).
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Optional

from ..core.schemas import Message, Session


class BaseSessionStore(ABC):
    """Interface cho mọi session store."""

    @abstractmethod
    def get(self, session_id: str) -> Optional[Session]: ...

    @abstractmethod
    def save(self, session: Session) -> None: ...

    @abstractmethod
    def delete(self, session_id: str) -> None: ...

    @abstractmethod
    def exists(self, session_id: str) -> bool: ...


# ------------------------------------------------------------------ #
# In-memory — dùng cho development, mất dữ liệu khi restart
# ------------------------------------------------------------------ #

class InMemorySessionStore(BaseSessionStore):
    def __init__(self) -> None:
        self._store: dict[str, Session] = {}

    def get(self, session_id: str) -> Optional[Session]:
        return self._store.get(session_id)

    def save(self, session: Session) -> None:
        self._store[session.session_id] = session

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    def exists(self, session_id: str) -> bool:
        return session_id in self._store


# ------------------------------------------------------------------ #
# Redis — dùng cho production
# ------------------------------------------------------------------ #

class RedisSessionStore(BaseSessionStore):
    """
    Lưu session trong Redis với TTL tự động.
    Yêu cầu: pip install redis
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", ttl: int = 3600):
        """
        Args:
            redis_url: URL kết nối Redis.
            ttl: Thời gian sống của session (giây). Session tự xoá sau khi hết hạn.
        """
        import redis  # type: ignore
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl

    def _key(self, session_id: str) -> str:
        return f"kaiwa:session:{session_id}"

    def get(self, session_id: str) -> Optional[Session]:
        raw = self._redis.get(self._key(session_id))
        if raw is None:
            return None
        return self._deserialize(json.loads(raw))

    def save(self, session: Session) -> None:
        self._redis.setex(
            self._key(session.session_id),
            self._ttl,
            json.dumps(self._serialize(session)),
        )

    def delete(self, session_id: str) -> None:
        self._redis.delete(self._key(session_id))

    def exists(self, session_id: str) -> bool:
        return bool(self._redis.exists(self._key(session_id)))

    @staticmethod
    def _serialize(session: Session) -> dict:
        return {
            "session_id": session.session_id,
            "history": [{"role": m.role, "content": m.content} for m in session.history],
        }

    @staticmethod
    def _deserialize(data: dict) -> Session:
        session = Session(session_id=data["session_id"])
        for msg in data["history"]:
            session.add_message(msg["role"], msg["content"])
        return session
