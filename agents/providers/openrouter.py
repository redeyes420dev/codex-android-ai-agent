"""OpenRouter provider implementation."""

from typing import Dict, Optional
import requests
import json
from ..base import AIClient

class OpenRouterClient(AIClient):
    """OpenRouter API client."""
    
    def __init__(
        self, 
        api_key: str, 
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key
            model: Default model name
            base_url: API base URL
        """
        self.api_key = api_key
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        self.default_model = model or "anthropic/claude-3.5-sonnet"
        self._usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    def complete(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Generate completion using OpenRouter API.
        
        Args:
            prompt: Input prompt
            model: Model to use (overrides default)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated completion text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/cadx/android-ai-agent",
            "X-Title": "CADX Android AI Agent"
        }
        
        payload = {
            "model": model or self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Update usage stats
            if "usage" in data:
                usage = data["usage"]
                self._usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                self._usage["completion_tokens"] += usage.get("completion_tokens", 0)
                self._usage["total_tokens"] += usage.get("total_tokens", 0)
            
            return data["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenRouter API error: {e}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"OpenRouter response parsing error: {e}")
    
    def get_usage(self) -> Dict[str, int]:
        """Get token usage statistics."""
        return self._usage.copy()