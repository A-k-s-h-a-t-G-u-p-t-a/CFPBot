"""Quick diagnostic: run this to verify your Gemini API key and quota."""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv(override=True)

# Show where the key is coming from
env_key = os.environ.get("GEMINI_API_KEY", "")
print(f"System env key: {'set (' + env_key[:8] + '...' + env_key[-4:] + ')' if env_key else 'NOT SET'}")

key = os.getenv("GEMINI_API_KEY")
if not key or key == "your_key_here":
    print("ERROR: GEMINI_API_KEY is not set in .env")
    raise SystemExit(1)

print(f"Key found: {key[:8]}...{key[-4:]}")

import google.generativeai as genai

genai.configure(api_key=key)

# List available models to check access
print("\nChecking available models...")
try:
    models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
    flash_models = [m for m in models if "flash" in m.lower()]
    print(f"Flash models available: {flash_models}")
    if not flash_models:
        print("WARNING: No flash models found — your key may lack access")
except Exception as e:
    print(f"ERROR listing models: {e}")

# Try a minimal call
print("\nTrying a minimal generateContent call...")
model = genai.GenerativeModel("gemini-2.0-flash")
try:
    response = model.generate_content("Reply with just the word: OK")
    print(f"SUCCESS: {response.text.strip()}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
