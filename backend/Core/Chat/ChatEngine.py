"""
ChatEngine.py - RAG Chat Orchestrator

Combines:
- Context Pyramid (5-layer user context)
- SRS (Smart Retrieval System for knowledge)
- LLM Inference (Groq/Gemini)

Manages Layer 4 (message history) by saving chat messages.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field

from config import firestoreDB
from Core.Memory.SRS import get_retrieval_chain
from Core.Memory.ContextPyramid import PyramidManager

from .InferenceProvider import (
    InferenceProvider,
    InferenceConfig,
    Provider,
    get_inference_provider,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class Source:
    """A knowledge source used in the response."""
    book: str
    text_preview: str
    score: float


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
        }


@dataclass
class ChatResponse:
    """Response from the chat engine."""
    message: str
    sources: List[Source]
    provider: str
    model: str
    context_used: bool
    retrieval_time_ms: float
    generation_time_ms: float
    
    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "sources": [
                {"book": s.book, "preview": s.text_preview[:100], "score": s.score}
                for s in self.sources
            ],
            "provider": self.provider,
            "model": self.model,
            "context_used": self.context_used,
            "retrieval_time_ms": round(self.retrieval_time_ms, 2),
            "generation_time_ms": round(self.generation_time_ms, 2),
        }


# =============================================================================
# System Prompts
# =============================================================================

DEFAULT_SYSTEM_PROMPT = """You are CareNest, a helpful maternal and infant health assistant. 

You provide accurate, caring, and supportive guidance on:
- Pregnancy nutrition and wellness
- Infant care and feeding
- Symptom awareness and when to seek medical care
- General maternal health questions

Guidelines:
- Be warm, supportive, and non-judgmental
- Use the provided context to give accurate information
- If unsure, recommend consulting a healthcare provider
- Keep responses concise but thorough
- Reference specific sources when available

IMPORTANT: Always prioritize safety. For any concerning symptoms, recommend consulting a doctor."""


# =============================================================================
# Chat Engine
# =============================================================================

class ChatEngine:
    """
    RAG-powered chat engine for CareNest.
    
    Flow:
    1. Get user context from Context Pyramid (all 5 layers)
    2. Retrieve relevant knowledge from SRS
    3. Build prompt with combined context
    4. Generate response via Groq/Gemini
    5. Save messages to Firestore (manages Layer 4)
    """
    
    DEFAULT_MAX_HISTORY = 10
    DEFAULT_MAX_CONTEXT_TOKENS = 2000
    DEFAULT_TOP_K_CHUNKS = 5
    
    def __init__(
        self,
        user_id: str,
        max_history: int = None,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the chat engine.
        
        Args:
            user_id: User's Firestore document ID
            max_history: Max messages to keep in Layer 4
            system_prompt: Custom system prompt (optional)
        """
        self.user_id = user_id
        self.max_history = max_history or self.DEFAULT_MAX_HISTORY
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        
        # Components
        self.pyramid = PyramidManager(user_id)
        self.retrieval_chain = get_retrieval_chain()
        self.inference = get_inference_provider()
        
        # Firestore reference for messages
        self._messages_ref = (
            firestoreDB.collection("users")
            .document(user_id)
            .collection("messages")
        )
    
    async def chat(
        self,
        message: str,
        provider: str = "groq",
        model: Optional[str] = None,
        include_sources: bool = True,
        save_messages: bool = True,
    ) -> ChatResponse:
        """
        Process a chat message and generate a response.
        
        Args:
            message: User's message
            provider: LLM provider ("groq" or "gemini")
            model: Specific model to use (optional)
            include_sources: Include source citations
            save_messages: Save to message history
            
        Returns:
            ChatResponse with message and metadata
        """
        import time
        start_time = time.time()
        
        # Step 1: Build combined context
        context, sources = await self._get_combined_context(message)
        retrieval_time = (time.time() - start_time) * 1000
        
        # Step 2: Build prompt
        prompt = self._build_prompt(message, context)
        
        # Step 3: Generate response
        gen_start = time.time()
        config = InferenceConfig(
            provider=Provider(provider),
            model=model,
        )
        
        response_text = self.inference.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            config=config,
        )
        generation_time = (time.time() - gen_start) * 1000
        
        # Step 4: Save messages (manages Layer 4)
        if save_messages:
            await self._save_message("user", message)
            await self._save_message("assistant", response_text)
        
        return ChatResponse(
            message=response_text,
            sources=sources if include_sources else [],
            provider=provider,
            model=config.get_model(),
            context_used=bool(context),
            retrieval_time_ms=retrieval_time,
            generation_time_ms=generation_time,
        )
    
    async def chat_stream(
        self,
        message: str,
        provider: str = "groq",
        model: Optional[str] = None,
        save_messages: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        Process a chat message with streaming response.
        
        Args:
            message: User's message
            provider: LLM provider
            model: Specific model
            save_messages: Save to history
            
        Yields:
            Response chunks
        """
        # Get context
        context, _ = await self._get_combined_context(message)
        prompt = self._build_prompt(message, context)
        
        config = InferenceConfig(
            provider=Provider(provider),
            model=model,
        )
        
        # Save user message
        if save_messages:
            await self._save_message("user", message)
        
        # Stream response
        full_response = []
        async for chunk in self.inference.generate_stream(
            prompt=prompt,
            system_prompt=self.system_prompt,
            config=config,
        ):
            full_response.append(chunk)
            yield chunk
        
        # Save assistant response
        if save_messages:
            await self._save_message("assistant", "".join(full_response))
    
    async def _get_combined_context(
        self,
        query: str
    ) -> tuple[str, List[Source]]:
        """
        Get combined context from Pyramid and SRS.
        
        Returns:
            Tuple of (context_string, sources_list)
        """
        sources = []
        context_parts = []
        
        # 1. Get user context from pyramid
        try:
            user_context = await self.pyramid.get_context_for_query(
                query,
                max_tokens=self.DEFAULT_MAX_CONTEXT_TOKENS // 2
            )
            if user_context:
                context_parts.append("## Your Information\n" + user_context)
        except Exception as e:
            logger.warning(f"Failed to get pyramid context: {e}")
        
        # 2. Get knowledge from SRS
        try:
            retrieval_result = self.retrieval_chain.retrieve_with_context(
                query,
                max_context_length=self.DEFAULT_MAX_CONTEXT_TOKENS // 2,
                top_k_chunks=self.DEFAULT_TOP_K_CHUNKS,
            )
            
            if retrieval_result.get("context"):
                context_parts.append("## Relevant Information\n" + retrieval_result["context"])
            
            # Extract sources
            for chunk in self.retrieval_chain.retrieve(query).chunks[:5]:
                sources.append(Source(
                    book=chunk.source_book,
                    text_preview=chunk.text[:200],
                    score=chunk.score,
                ))
                
        except Exception as e:
            logger.warning(f"Failed to get SRS context: {e}")
        
        return "\n\n".join(context_parts), sources
    
    def _build_prompt(self, message: str, context: str) -> str:
        """Build the final prompt with context."""
        if context:
            return f"""Context:
{context}

---

User Question: {message}

Please provide a helpful response based on the context above."""
        else:
            return message
    
    async def _save_message(self, role: str, content: str) -> None:
        """
        Save a message to Firestore (manages Layer 4).
        
        Also enforces max_history limit.
        """
        try:
            # Add new message
            self._messages_ref.add({
                "role": role,
                "content": content,
                "created_at": datetime.now(timezone.utc),
            })
            
            # Trim old messages if over limit
            await self._trim_message_history()
            
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
    
    async def _trim_message_history(self) -> None:
        """Trim message history to max_history limit."""
        try:
            # Get all messages ordered by time
            query = (
                self._messages_ref
                .order_by("created_at", direction="ASCENDING")
            )
            
            docs = list(query.stream())
            
            # Delete oldest if over limit
            if len(docs) > self.max_history * 2:  # Keep pairs
                to_delete = len(docs) - (self.max_history * 2)
                for doc in docs[:to_delete]:
                    doc.reference.delete()
                    
                logger.info(f"Trimmed {to_delete} old messages for user {self.user_id}")
                
        except Exception as e:
            logger.warning(f"Failed to trim messages: {e}")
    
    async def get_history(self, limit: int = 20) -> List[Dict]:
        """Get message history."""
        try:
            query = (
                self._messages_ref
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
            )
            
            messages = []
            for doc in query.stream():
                data = doc.to_dict()
                messages.append({
                    "id": doc.id,
                    "role": data.get("role"),
                    "content": data.get("content"),
                    "created_at": data.get("created_at").isoformat() if data.get("created_at") else None,
                })
            
            messages.reverse()
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []
    
    async def clear_history(self) -> int:
        """Clear all message history. Returns count deleted."""
        try:
            docs = list(self._messages_ref.stream())
            count = len(docs)
            
            for doc in docs:
                doc.reference.delete()
            
            logger.info(f"Cleared {count} messages for user {self.user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            return 0


# =============================================================================
# Convenience Functions
# =============================================================================

async def chat(
    user_id: str,
    message: str,
    provider: str = "groq",
    **kwargs
) -> ChatResponse:
    """Quick chat function."""
    engine = ChatEngine(user_id)
    return await engine.chat(message, provider=provider, **kwargs)
