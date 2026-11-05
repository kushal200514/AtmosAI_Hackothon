import time
from typing import Any, Optional, Tuple, Dict
from datetime import datetime, timezone

class TTLCache:
    def __init__(self, default_ttl_seconds: int = 300):
        self.default_ttl = default_ttl_seconds
        self._store: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Tuple[Optional[Any], bool, Optional[datetime]]:
        """
        Returns (data, is_stale, cached_timestamp).
        If key does not exist at all, returns (None, True, None).
        If key exists but expired, returns (data, True, cached_timestamp).
        If key exists and fresh, returns (data, False, cached_timestamp).
        """
        entry = self._store.get(key)
        if not entry:
            return None, True, None

        now = time.time()
        is_stale = now > entry["expires_at"]
        return entry["data"], is_stale, entry["cached_at"]

    def set(self, key: str, data: Any, ttl_seconds: Optional[int] = None):
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()
        self._store[key] = {
            "data": data,
            "cached_at": datetime.now(timezone.utc),
            "expires_at": now + ttl
        }

    def clear(self):
        self._store.clear()

cache_manager = TTLCache(default_ttl_seconds=300)

