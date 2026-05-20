from google import genai
import os
from backend.core.config import settings

_client = None

def _get_client():
    global _client
    api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if _client is None and api_key:
        try:
            _client = genai.Client(api_key=api_key)
        except Exception:
            _client = None
    return _client


class GeminiProvider:
    @staticmethod
    async def generate(prompt: str) -> str:
        client = _get_client()
        if client is None:
            return f"[MOCK Gemini] response for: {prompt[:60]}"

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini execution error: {e}")
