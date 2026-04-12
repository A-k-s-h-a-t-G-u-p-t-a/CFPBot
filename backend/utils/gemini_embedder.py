"""
Thin wrapper around the Gemini text-embedding-004 model.
Returns 768-dimensional float vectors compatible with pgvector.
"""
import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

_PRIMARY_EMBEDDING_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/text-embedding-004")
_FALLBACK_EMBEDDING_MODEL = os.getenv("GEMINI_EMBED_FALLBACK_MODEL", "models/embedding-001")


def embed_text(text: str) -> list[float]:
    """Embed a single string. Returns a list of 768 floats."""
    try:
        result = genai.embed_content(model=_PRIMARY_EMBEDDING_MODEL, content=text)
        return result["embedding"]
    except Exception:
        result = genai.embed_content(model=_FALLBACK_EMBEDDING_MODEL, content=text)
        return result["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple strings. More efficient than calling embed_text in a loop."""
    return [embed_text(t) for t in texts]
