"""Google Gemini provider implementation."""

from typing import Dict, Optional
import google.generativeai as genai
from ..base import AIClient

class GeminiClient(AIClient):
    """Google Gemini API client."""
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        """Initialize Gemini client.
        
        Args:
            api_key: Google AI API key
            model: Default model name
        """
        genai.configure(api_key=api_key)
        self.default_model = model or "gemini-pro"
        self._usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    def complete(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Generate completion using Gemini API.
        
        Args:
            prompt: Input prompt
            model: Model to use (overrides default)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated completion text
        """
        try:
            model_name = model or self.default_model
            gemini_model = genai.GenerativeModel(model_name)
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Update usage stats (Gemini doesn't provide detailed token counts)
            # Rough estimation
            prompt_tokens = len(prompt.split()) * 1.3  # Approximate tokens
            completion_tokens = len(response.text.split()) * 1.3
            
            self._usage["prompt_tokens"] += int(prompt_tokens)
            self._usage["completion_tokens"] += int(completion_tokens)
            self._usage["total_tokens"] += int(prompt_tokens + completion_tokens)
            
            return response.text
            
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}")
    
    def get_usage(self) -> Dict[str, int]:
        """Get token usage statistics."""
        return self._usage.copy()