"""
llm_models.py - Canonical Groq model identifiers

Groq's model catalogue changes and access is per-account, so every module
imports its model names from here instead of hardcoding strings.

Models available on the current key (verify with:
    curl https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY"
):
    openai/gpt-oss-120b   - main reasoning model (chat, meal plans)
    openai/gpt-oss-20b    - fast/cheap routing and classification
    qwen/qwen3.8-27b      - general purpose alternative
"""

import os

# Main conversational / generative model.
CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL", "openai/gpt-oss-120b")

# Small, fast model for classification and routing.
ROUTER_MODEL = os.getenv("GROQ_ROUTER_MODEL", "openai/gpt-oss-20b")

# Model used for structured JSON extraction (ingredients, nutrients).
EXTRACTION_MODEL = os.getenv("GROQ_EXTRACTION_MODEL", "openai/gpt-oss-120b")

# Reasoning models spend completion tokens on hidden reasoning before they
# emit content, so any max_completion_tokens budget must cover both.
DEFAULT_REASONING_EFFORT = os.getenv("GROQ_REASONING_EFFORT", "medium")

# Budget that leaves room for reasoning plus a useful answer.
CHAT_MAX_COMPLETION_TOKENS = 4096
EXTRACTION_MAX_COMPLETION_TOKENS = 2048
ROUTER_MAX_COMPLETION_TOKENS = 512

# Models that accept `reasoning_effort`.
REASONING_MODELS = (
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-safeguard-20b",
)


def supports_reasoning_effort(model: str) -> bool:
    """Whether the given model accepts the reasoning_effort parameter."""
    return model in REASONING_MODELS
