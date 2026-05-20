import httpx

class OllamaProvider:
    @staticmethod
    async def generate(prompt: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False
                }
                r = await client.post("http://localhost:11434/api/generate", json=data, timeout=10.0)
                if r.status_code == 200:
                    return r.json()["response"]
                else:
                    raise Exception(f"Ollama failed with status {r.status_code}")
        except Exception as e:
            return f"[MOCK Ollama] response for: {prompt[:60]}"
