from google import genai
from backend.core.config import settings

_client = None

def _get_client():
    global _client
    if _client is None and settings.GEMINI_API_KEY:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


class GeminiProvider:
    @staticmethod
    async def generate(prompt: str) -> str:
        client = _get_client()
        if client is None:
            # No API key — return mock so tests can run without credentials
            return "[MOCK] APIS backend is running. Set GEMINI_API_KEY in .env for real responses."

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text
