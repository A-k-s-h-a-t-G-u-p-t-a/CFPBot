import asyncio
import os

import google.generativeai as genai
from dotenv import load_dotenv
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

load_dotenv()


def _load_api_keys() -> list[str]:
    """
    Supports all of these patterns:
    1) GEMINI_API_KEYS="key1,key2,key3"
    2) GEMINI_API_KEY + GEMINI_API_KEY_2 + GEMINI_API_KEY_3 ...
    3) GEMINI_API_KEY only
    """
    keys: list[str] = []

    keys_csv = os.getenv("GEMINI_API_KEYS", "")
    if keys_csv:
        keys.extend([k.strip() for k in keys_csv.split(",") if k.strip()])

    numbered: list[tuple[int, str]] = []
    for env_name, value in os.environ.items():
        if not value:
            continue
        if env_name == "GEMINI_API_KEY":
            numbered.append((1, value.strip()))
            continue
        if env_name.startswith("GEMINI_API_KEY_"):
            suffix = env_name.removeprefix("GEMINI_API_KEY_")
            if suffix.isdigit():
                numbered.append((int(suffix), value.strip()))

    for _, key in sorted(numbered, key=lambda x: x[0]):
        if key:
            keys.append(key)

    # Deduplicate while preserving order
    unique_keys: list[str] = []
    seen: set[str] = set()
    for key in keys:
        if key and key not in seen:
            unique_keys.append(key)
            seen.add(key)
    return unique_keys


_API_KEYS = _load_api_keys()
if not _API_KEYS:
    raise RuntimeError("No Gemini API key configured. Set GEMINI_API_KEY or GEMINI_API_KEYS.")

_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_rr_index = 0
_rr_lock = asyncio.Lock()

# Cap concurrent Gemini calls to stay within free-tier rate limits
_semaphore = asyncio.Semaphore(4)


async def _next_key_start_index() -> int:
    global _rr_index
    async with _rr_lock:
        start = _rr_index
        _rr_index = (_rr_index + 1) % len(_API_KEYS)
        return start


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(Exception),
)
async def call_gemini(prompt: str, system: str = "", json_mode: bool = False) -> str:
    """
    Single entry point for all Gemini calls.
    Handles rate-limit backoff (1s → 2s → 4s) and caps concurrency at 4.
    """
    async with _semaphore:
        generation_config = {}
        if json_mode:
            generation_config["response_mime_type"] = "application/json"

        contents = f"{system}\n\n{prompt}" if system else prompt
        start_idx = await _next_key_start_index()
        last_exc: Exception | None = None

        # Try all keys in round-robin order for this call
        for offset in range(len(_API_KEYS)):
            idx = (start_idx + offset) % len(_API_KEYS)
            key = _API_KEYS[idx]
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(_MODEL_NAME)
                response = await model.generate_content_async(
                    contents,
                    generation_config=generation_config if generation_config else None,
                )
                return response.text
            except Exception as exc:
                last_exc = exc
                continue

        raise RuntimeError(f"All Gemini API keys failed for model '{_MODEL_NAME}'") from last_exc
