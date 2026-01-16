"""
InferenceProvider.py - Unified LLM Inference Interface

Provides a unified interface for Groq and Gemini LLM inference.
"""

import os
import logging
from typing import Optional, AsyncGenerator, Dict, Any
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Provider(str, Enum):
    """Available LLM providers."""
    GROQ = "groq"
    GEMINI = "gemini"


@dataclass
class InferenceConfig:
    """Configuration for inference."""
    provider: Provider = Provider.GROQ
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    
    def get_model(self) -> str:
        """Get model name, using defaults if not specified."""
        if self.model:
            return self.model
        
        defaults = {
            Provider.GROQ: "llama-3.3-70b-versatile",
            Provider.GEMINI: "gemini-2.5-flash",
        }
        return defaults.get(self.provider, "llama-3.3-70b-versatile")


class InferenceProvider:
    """
    Unified interface for LLM inference.
    
    Supports:
    - Groq (fast, good for most queries)
    - Gemini (rich reasoning, multimodal capable)
    """
    
    def __init__(self):
        """Initialize inference providers."""
        self._groq_client = None
        self._gemini_client = None
        
        # Check API keys
        self.groq_available = bool(os.getenv("GROQ_API_KEY"))
        self.gemini_available = bool(os.getenv("GEMINI_API_KEY"))
        
        if not self.groq_available:
            logger.warning("GROQ_API_KEY not set")
        if not self.gemini_available:
            logger.warning("GEMINI_API_KEY not set")
    
    @property
    def groq_client(self):
        """Lazy-load Groq client."""
        if self._groq_client is None and self.groq_available:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                logger.info("Groq client initialized")
            except ImportError:
                logger.error("groq package not installed")
        return self._groq_client
    
    @property
    def gemini_client(self):
        """Lazy-load Gemini client."""
        if self._gemini_client is None and self.gemini_available:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                logger.info("Gemini client initialized")
            except ImportError:
                logger.error("google-genai package not installed")
        return self._gemini_client
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[InferenceConfig] = None
    ) -> str:
        """
        Generate a response synchronously.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            config: Inference configuration
            
        Returns:
            Generated response text
        """
        config = config or InferenceConfig()
        
        if config.provider == Provider.GROQ:
            return self._generate_groq(prompt, system_prompt, config)
        elif config.provider == Provider.GEMINI:
            return self._generate_gemini(prompt, system_prompt, config)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")
    
    def _generate_groq(
        self,
        prompt: str,
        system_prompt: Optional[str],
        config: InferenceConfig
    ) -> str:
        """Generate using Groq."""
        if not self.groq_client:
            raise RuntimeError("Groq client not available")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.groq_client.chat.completions.create(
                model=config.get_model(),
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise
    
    def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        config: InferenceConfig
    ) -> str:
        """Generate using Gemini."""
        if not self.gemini_client:
            raise RuntimeError("Gemini client not available")
        
        # Combine system prompt with user prompt for Gemini
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            response = self.gemini_client.models.generate_content(
                model=config.get_model(),
                contents=full_prompt,
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[InferenceConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a response with streaming.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            config: Inference configuration
            
        Yields:
            Response chunks
        """
        config = config or InferenceConfig()
        
        if config.provider == Provider.GROQ:
            async for chunk in self._stream_groq(prompt, system_prompt, config):
                yield chunk
        elif config.provider == Provider.GEMINI:
            async for chunk in self._stream_gemini(prompt, system_prompt, config):
                yield chunk
    
    async def _stream_groq(
        self,
        prompt: str,
        system_prompt: Optional[str],
        config: InferenceConfig
    ) -> AsyncGenerator[str, None]:
        """Stream using Groq."""
        if not self.groq_client:
            raise RuntimeError("Groq client not available")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = self.groq_client.chat.completions.create(
                model=config.get_model(),
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Groq streaming failed: {e}")
            raise
    
    async def _stream_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        config: InferenceConfig
    ) -> AsyncGenerator[str, None]:
        """Stream using Gemini."""
        if not self.gemini_client:
            raise RuntimeError("Gemini client not available")
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            # Gemini streaming
            response = self.gemini_client.models.generate_content_stream(
                model=config.get_model(),
                contents=full_prompt,
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            raise
    
    def get_available_providers(self) -> Dict[str, Any]:
        """Get available providers and their status."""
        return {
            "groq": {
                "available": self.groq_available,
                "models": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"],
                "default": "llama-3.3-70b-versatile",
            },
            "gemini": {
                "available": self.gemini_available,
                "models": ["gemini-2.5-flash", "gemini-2.0-flash"],
                "default": "gemini-2.5-flash",
            },
        }


# =============================================================================
# Module-level singleton
# =============================================================================

_provider: Optional[InferenceProvider] = None


def get_inference_provider() -> InferenceProvider:
    """Get the global InferenceProvider instance."""
    global _provider
    if _provider is None:
        _provider = InferenceProvider()
    return _provider


# =============================================================================
# Convenience functions
# =============================================================================

def generate(
    prompt: str,
    provider: str = "groq",
    system_prompt: Optional[str] = None,
    **kwargs
) -> str:
    """Quick generate function."""
    config = InferenceConfig(
        provider=Provider(provider),
        **kwargs
    )
    return get_inference_provider().generate(prompt, system_prompt, config)
