"""
Chat Module - RAG-powered Conversational AI

Provides:
- ChatEngine: Main RAG orchestrator with Context Pyramid + SRS
- InferenceProvider: Unified Groq/Gemini interface
"""

from .ChatEngine import (
    ChatEngine,
    ChatMessage,
    ChatResponse,
    Source,
    chat,
)

from .InferenceProvider import (
    InferenceProvider,
    InferenceConfig,
    Provider,
    get_inference_provider,
    generate,
)


__all__ = [
    # Chat Engine
    "ChatEngine",
    "ChatMessage",
    "ChatResponse",
    "Source",
    "chat",
    
    # Inference
    "InferenceProvider",
    "InferenceConfig",
    "Provider",
    "get_inference_provider",
    "generate",
]
