import asyncio
import os

import google.generativeai as genai
from dotenv import load_dotenv
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

_model = genai.GenerativeModel("gemini-2.0-flash")

# Cap concurrent Gemini calls to stay within free-tier rate limits
_semaphore = asyncio.Semaphore(4)


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
        response = await _model.generate_content_async(
            contents,
            generation_config=generation_config if generation_config else None,
        )
        return response.text
