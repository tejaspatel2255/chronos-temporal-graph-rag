import hashlib
import time
from typing import Dict, Any, Optional

class QueryCache:
    """In-memory LRU-style query cache with configurable TTL and manual invalidation."""
    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 100):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _hash_key(self, question: str, force_fallback: bool = False, session_id: Optional[str] = None) -> str:
        raw_key = f"{question.strip().lower()}|fallback={force_fallback}|session={session_id or ''}"
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    def get(self, question: str, force_fallback: bool = False, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Returns cached query result if present and not expired."""
        key = self._hash_key(question, force_fallback, session_id)
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            # Expired cache entry
            del self.cache[key]
            return None

        # Return cached payload with cache hit metadata
        payload = dict(entry["payload"])
        payload["cached"] = True
        payload["cache_timestamp"] = entry["timestamp"]
        return payload

    def set(self, question: str, payload: Dict[str, Any], force_fallback: bool = False, session_id: Optional[str] = None):
        """Stores a query result payload in cache."""
        key = self._hash_key(question, force_fallback, session_id)
        
        # Enforce max entries capacity limit
        if len(self.cache) >= self.max_entries and key not in self.cache:
            # Evict oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]

        self.cache[key] = {
            "timestamp": time.time(),
            "payload": payload
        }

    def invalidate_all(self) -> int:
        """Flushes all entries from the query cache. Returns count of invalidated entries."""
        count = len(self.cache)
        self.cache.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Returns current cache telemetry stats."""
        valid_entries = 0
        now = time.time()
        for entry in self.cache.values():
            if now - entry["timestamp"] <= self.ttl_seconds:
                valid_entries += 1
        return {
            "total_cached_queries": valid_entries,
            "max_entries": self.max_entries,
            "ttl_seconds": self.ttl_seconds
        }

# Global singleton query cache instance
query_cache = QueryCache(ttl_seconds=3600, max_entries=100)
