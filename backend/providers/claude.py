import os
import httpx

class ClaudeProvider:
    @staticmethod
    async def generate(prompt: str) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return f"[MOCK Claude] response for: {prompt[:60]}"
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                data = {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}]
                }
                r = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=30.0)
                if r.status_code == 200:
                    return r.json()["content"][0]["text"]
                else:
                    raise Exception(f"Claude API failed with status {r.status_code}: {r.text}")
        except Exception as e:
            raise Exception(f"Claude execution error: {e}")
