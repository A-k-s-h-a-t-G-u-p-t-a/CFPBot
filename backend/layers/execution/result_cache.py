import hashlib
import os
import time
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class ResultCache:
    """Exact-match SQL result cache with TTL. Prevents repeated identical queries."""

    def __init__(self, ttl_seconds: int = 300):
        self._cache: dict[str, dict] = {}
        self.ttl = ttl_seconds

    def _key(self, sql: str) -> str:
        return hashlib.md5(sql.encode()).hexdigest()

    def get(self, sql: str) -> Optional[list[dict]]:
        entry = self._cache.get(self._key(sql))
        if not entry:
            return None
        if time.time() - entry["ts"] > self.ttl:
            del self._cache[self._key(sql)]
            return None
        return entry["rows"]

    def set(self, sql: str, rows: list[dict]):
        self._cache[self._key(sql)] = {"rows": rows, "ts": time.time()}

    def clear(self):
        self._cache.clear()


result_cache = ResultCache(ttl_seconds=int(os.getenv("RESULT_CACHE_TTL_SECONDS", 300)))
