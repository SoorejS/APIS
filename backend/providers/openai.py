import os
import httpx

class OpenAIProvider:
    @staticmethod
    async def generate(prompt: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return f"[MOCK OpenAI] response for: {prompt[:60]}"
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                }
                r = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=30.0)
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"OpenAI API failed with status {r.status_code}: {r.text}")
        except Exception as e:
            raise Exception(f"OpenAI execution error: {e}")
