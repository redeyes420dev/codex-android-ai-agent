"""OpenAI provider implementation."""

from typing import Dict, Optional
import openai
from ..base import AIClient

class OpenAIClient(AIClient):
    """OpenAI API client."""
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Default model name
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.default_model = model or "gpt-4"
        self._usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    def complete(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Generate completion using OpenAI API.
        
        Args:
            prompt: Input prompt
            model: Model to use (overrides default)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated completion text
        """
        try:
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Update usage stats
            if response.usage:
                self._usage["prompt_tokens"] += response.usage.prompt_tokens
                self._usage["completion_tokens"] += response.usage.completion_tokens
                self._usage["total_tokens"] += response.usage.total_tokens
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")
    
    def get_usage(self) -> Dict[str, int]:
        """Get token usage statistics."""
        return self._usage.copy()