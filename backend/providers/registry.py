from backend.providers.gemini import GeminiProvider
from backend.providers.openai import OpenAIProvider
from backend.providers.claude import ClaudeProvider
from backend.providers.ollama import OllamaProvider

class ProviderRegistry:
    def __init__(self):
        self._providers = {
            "gemini": GeminiProvider,
            "openai": OpenAIProvider,
            "claude": ClaudeProvider,
            "ollama": OllamaProvider
        }

    def get_provider(self, name: str):
        name_lower = name.lower()
        if name_lower not in self._providers:
            # Fallback to gemini by default
            return self._providers["gemini"]
        return self._providers[name_lower]

    async def generate_with_fallback(self, provider_name: str, prompt: str, fallback_name: str = "gemini") -> str:
        provider = self.get_provider(provider_name)
        try:
            return await provider.generate(prompt)
        except Exception as e:
            print(f"[ProviderRegistry] Primary provider '{provider_name}' failed: {e}. Falling back to '{fallback_name}'.")
            fallback_provider = self.get_provider(fallback_name)
            try:
                return await fallback_provider.generate(prompt)
            except Exception as fe:
                # If fallback also fails, raise an exception or return a mock indicating failure
                raise Exception(f"Both primary provider '{provider_name}' and fallback '{fallback_name}' failed. Original: {e}, Fallback: {fe}")

registry = ProviderRegistry()
