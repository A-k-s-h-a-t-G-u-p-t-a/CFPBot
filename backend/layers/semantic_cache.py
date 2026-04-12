import os
import pickle
import time
from typing import Optional

import numpy as np
from dotenv import load_dotenv
from fastembed import TextEmbedding

load_dotenv()

_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
_SNAPSHOT = os.path.join(os.path.dirname(__file__), "../data/cache_snapshot.pkl")


class SemanticCache:
    def __init__(self, threshold: float = 0.92, ttl_hours: float = 1.0):
        self.threshold   = threshold
        self.ttl_seconds = ttl_hours * 3600
        self._cache: list[dict] = []
        self._hits   = 0
        self._misses = 0
        self._load_snapshot()

    def lookup(self, question: str, cache_key: str | None = None) -> Optional[dict]:
        emb = self._embed(question)
        now = time.time()
        for entry in self._cache:
            if now - entry["ts"] > self.ttl_seconds:
                continue
            if cache_key is not None:
                if entry.get("key") == cache_key:
                    self._hits += 1
                    return entry["answer"]
                continue
            if float(np.dot(emb, entry["emb"])) >= self.threshold:
                self._hits += 1
                return entry["answer"]
        self._misses += 1
        return None

    def store(self, question: str, answer: dict, cache_key: str | None = None):
        self._cache.append({
            "emb":    self._embed(question),
            "answer": answer,
            "ts":     time.time(),
            "key":    cache_key,
        })
        self._save_snapshot()

    def invalidate_all(self):
        self._cache.clear()
        if os.path.exists(_SNAPSHOT):
            os.remove(_SNAPSHOT)

    def hit_rate(self) -> str:
        total = self._hits + self._misses
        return f"{int(self._hits / total * 100)}%" if total else "0%"

    def _embed(self, text: str) -> np.ndarray:
        return np.array(list(_model.embed([text]))[0])

    def _save_snapshot(self):
        try:
            with open(_SNAPSHOT, "wb") as f:
                pickle.dump(self._cache, f)
        except Exception:
            pass

    def _load_snapshot(self):
        if os.path.exists(_SNAPSHOT):
            try:
                with open(_SNAPSHOT, "rb") as f:
                    self._cache = pickle.load(f)
                print(f"[SemanticCache] Restored {len(self._cache)} entries")
            except Exception:
                self._cache = []


semantic_cache = SemanticCache(
    threshold=float(os.getenv("CACHE_THRESHOLD", 0.92)),
    ttl_hours=float(os.getenv("SEMANTIC_CACHE_TTL_HOURS", 1.0)),
)
