import logging
from typing import Optional, List, Dict, Any
import httpx
from backend.app.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(
        self,
        provider: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = provider or settings.AI_PROVIDER
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or (settings.CF_WORKERS_AI_MODEL if self.provider == "cloudflare_workers_ai" else settings.OLLAMA_MODEL)

    def _get_cloudflare_headers(self) -> Dict[str, str]:
        """Headers for Cloudflare Access protected tunnels or custom Cloudflare setups."""
        headers = {}
        if settings.CF_ACCESS_CLIENT_ID:
            headers["CF-Access-Client-Id"] = settings.CF_ACCESS_CLIENT_ID
        if settings.CF_ACCESS_CLIENT_SECRET:
            headers["CF-Access-Client-Secret"] = settings.CF_ACCESS_CLIENT_SECRET
        if settings.CF_BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {settings.CF_BEARER_TOKEN}"
        return headers

    def is_available(self) -> bool:
        """Check if selected AI provider (Local/Cloudflare Ollama or Cloudflare Workers AI) is reachable."""
        if self.provider == "cloudflare_workers_ai":
            if not settings.CF_ACCOUNT_ID or not settings.CF_API_TOKEN:
                return False
            # Verify credentials via lightweight account check
            try:
                headers = {"Authorization": f"Bearer {settings.CF_API_TOKEN}"}
                url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CF_ACCOUNT_ID}/ai/models/search?search=qwen"
                with httpx.Client(timeout=2.5) as client:
                    res = client.get(url, headers=headers)
                    return res.status_code == 200
            except Exception:
                return False

        # Provider == 'ollama' (Local or via Cloudflare Tunnel)
        try:
            headers = self._get_cloudflare_headers()
            with httpx.Client(timeout=2.5) as client:
                res = client.get(f"{self.base_url}/api/tags", headers=headers)
                return res.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """List models available on the provider."""
        if self.provider == "cloudflare_workers_ai":
            return [
                "@cf/qwen/qwen2.5-7b-instruct",
                "@cf/meta/llama-3.1-8b-instruct",
                "@cf/mistral/mistral-7b-instruct-v0.2"
            ]

        # Ollama via Cloudflare Tunnel / Local
        try:
            headers = self._get_cloudflare_headers()
            with httpx.Client(timeout=2.5) as client:
                res = client.get(f"{self.base_url}/api/tags", headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    if models:
                        return models
        except Exception:
            pass
        return ["qwen2.5:7b", "qwen2.5:3b", "llama3.2:3b", "mistral:7b"]

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Generate text using Cloudflare Workers AI or Ollama via Cloudflare Tunnel / Local.
        Gracefully returns None if unreachable (triggering local fallback).
        """
        if self.provider == "cloudflare_workers_ai":
            return self._generate_cloudflare_workers_ai(prompt, system_prompt)

        return self._generate_ollama(prompt, system_prompt)

    def _generate_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        headers = self._get_cloudflare_headers()
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 600
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(f"{self.base_url}/api/generate", json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("response", "").strip()
                else:
                    logger.warning(f"Ollama/Cloudflare returned status {res.status_code}: {res.text}")
                    return None
        except Exception as e:
            logger.warning(f"Error querying Ollama via Cloudflare: {e}. Switching to fallback.")
            return None

    def _generate_cloudflare_workers_ai(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        if not settings.CF_ACCOUNT_ID or not settings.CF_API_TOKEN:
            logger.warning("Cloudflare Workers AI credentials missing. Switching to fallback.")
            return None

        headers = {
            "Authorization": f"Bearer {settings.CF_API_TOKEN}",
            "Content-Type": "application/json"
        }
        url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CF_ACCOUNT_ID}/ai/run/{self.model}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"messages": messages}

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    result = data.get("result", {})
                    response_text = result.get("response", "")
                    return response_text.strip()
                else:
                    logger.warning(f"Cloudflare Workers AI error {res.status_code}: {res.text}")
                    return None
        except Exception as e:
            logger.warning(f"Error calling Cloudflare Workers AI: {e}. Switching to fallback.")
            return None

ai_service = AIService()
