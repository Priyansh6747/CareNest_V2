"""
InferenceProvider.py - Unified LLM Inference Interface

Groq is the sole LLM provider for CareNest.

Note on reasoning models: `openai/gpt-oss-*` emit a separate reasoning stream
before any content. `max_completion_tokens` covers reasoning + answer, so the
token budget must be large enough or the content comes back empty.
"""

import os
import logging
from typing import Optional, AsyncGenerator, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

from Core.llm_models import (
    CHAT_MODEL,
    ROUTER_MODEL,
    DEFAULT_REASONING_EFFORT,
    CHAT_MAX_COMPLETION_TOKENS,
    supports_reasoning_effort,
)

load_dotenv()

logger = logging.getLogger(__name__)


AVAILABLE_GROQ_MODELS = [
    CHAT_MODEL,
    ROUTER_MODEL,
]


@dataclass
class InferenceConfig:
    """Configuration for inference."""
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = CHAT_MAX_COMPLETION_TOKENS
    reasoning_effort: Optional[str] = None

    def get_model(self) -> str:
        """Get model name, using the default if not specified."""
        return self.model or CHAT_MODEL

    def get_reasoning_effort(self) -> Optional[str]:
        """Only reasoning-capable models accept this parameter."""
        if not supports_reasoning_effort(self.get_model()):
            return None
        return self.reasoning_effort or DEFAULT_REASONING_EFFORT


class InferenceProvider:
    """
    Unified interface for LLM inference.

    Supports Groq (fast, good for most queries).
    """

    def __init__(self):
        """Initialize the inference provider."""
        self._groq_client = None

        self.groq_available = bool(os.getenv("GROQ_API_KEY"))

        if not self.groq_available:
            logger.warning("GROQ_API_KEY not set")

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

    def _build_request_kwargs(
        self,
        prompt: str,
        system_prompt: Optional[str],
        config: InferenceConfig,
        stream: bool,
    ) -> Dict[str, Any]:
        """Build the chat.completions.create kwargs."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs: Dict[str, Any] = {
            "model": config.get_model(),
            "messages": messages,
            "temperature": config.temperature,
            "max_completion_tokens": config.max_tokens,
        }

        effort = config.get_reasoning_effort()
        if effort:
            kwargs["reasoning_effort"] = effort

        if stream:
            kwargs["stream"] = True

        return kwargs

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

        if not self.groq_client:
            raise RuntimeError("Groq client not available")

        kwargs = self._build_request_kwargs(prompt, system_prompt, config, stream=False)

        try:
            response = self.groq_client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content

            if not content or not content.strip():
                finish = response.choices[0].finish_reason
                logger.warning(
                    f"Groq returned empty content (model={config.get_model()}, "
                    f"finish_reason={finish}) - likely ran out of "
                    f"max_completion_tokens on reasoning"
                )

            return content or ""

        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[InferenceConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a response with streaming.

        Only answer content is yielded; the reasoning channel is skipped so
        users never see the model's private scratchpad.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            config: Inference configuration

        Yields:
            Response content chunks
        """
        config = config or InferenceConfig()

        if not self.groq_client:
            raise RuntimeError("Groq client not available")

        kwargs = self._build_request_kwargs(prompt, system_prompt, config, stream=True)

        try:
            stream = self.groq_client.chat.completions.create(**kwargs)

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    yield content

        except Exception as e:
            logger.error(f"Groq streaming failed: {e}")
            raise

    def get_available_providers(self) -> Dict[str, Any]:
        """Get available providers and their status."""
        return {
            "groq": {
                "available": self.groq_available,
                "models": AVAILABLE_GROQ_MODELS,
                "default": CHAT_MODEL,
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
    system_prompt: Optional[str] = None,
    **kwargs
) -> str:
    """Quick generate function."""
    config = InferenceConfig(**kwargs)
    return get_inference_provider().generate(prompt, system_prompt, config)
