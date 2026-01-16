"""
Chat Router - API Endpoints for RAG Chatbot

Provides endpoints for:
- Single-turn chat with RAG
- Streaming chat responses
- Message history management
- Provider information
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from Core.Chat import ChatEngine, get_inference_provider


router = APIRouter(prefix="/chat", tags=["Chat"])


# =============================================================================
# Request/Response Models
# =============================================================================

class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str = Field(..., min_length=1, description="User message")
    provider: str = Field(default="groq", description="LLM provider: groq or gemini")
    model: Optional[str] = Field(default=None, description="Specific model to use")
    include_sources: bool = Field(default=True, description="Include source citations")
    max_history: int = Field(default=10, ge=1, le=50, description="Max messages to keep")


class ChatMessageResponse(BaseModel):
    """Response from chat endpoint."""
    message: str
    sources: List[dict]
    provider: str
    model: str
    context_used: bool
    retrieval_time_ms: float
    generation_time_ms: float


class HistoryMessage(BaseModel):
    """A message in history."""
    id: str
    role: str
    content: str
    created_at: Optional[str]


class HistoryResponse(BaseModel):
    """Response for history endpoint."""
    user_id: str
    count: int
    messages: List[HistoryMessage]


# =============================================================================
# Chat Endpoints
# =============================================================================

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatRequest, user_id: str = Query(...)):
    """
    Send a message and get a RAG-powered response.
    
    Uses:
    - Context Pyramid for user-specific context (5 layers)
    - SRS for knowledge retrieval
    - Groq or Gemini for response generation
    
    Messages are saved to history (Layer 4 of Context Pyramid).
    """
    try:
        engine = ChatEngine(
            user_id=user_id,
            max_history=request.max_history,
        )
        
        response = await engine.chat(
            message=request.message,
            provider=request.provider,
            model=request.model,
            include_sources=request.include_sources,
        )
        
        return ChatMessageResponse(**response.to_dict())
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_message(request: ChatRequest, user_id: str = Query(...)):
    """
    Send a message and get a streaming response.
    
    Returns Server-Sent Events (SSE) with response chunks.
    """
    try:
        engine = ChatEngine(
            user_id=user_id,
            max_history=request.max_history,
        )
        
        async def generate():
            try:
                async for chunk in engine.chat_stream(
                    message=request.message,
                    provider=request.provider,
                    model=request.model,
                ):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# History Endpoints
# =============================================================================

@router.get("/history/{user_id}", response_model=HistoryResponse)
async def get_history(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100)
):
    """
    Get message history for a user.
    
    This is the same data used by Context Pyramid Layer 4.
    """
    try:
        engine = ChatEngine(user_id)
        messages = await engine.get_history(limit=limit)
        
        return HistoryResponse(
            user_id=user_id,
            count=len(messages),
            messages=[HistoryMessage(**m) for m in messages],
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{user_id}")
async def clear_history(user_id: str):
    """
    Clear all message history for a user.
    
    This clears Layer 4 of the Context Pyramid.
    """
    try:
        engine = ChatEngine(user_id)
        count = await engine.clear_history()
        
        return {
            "success": True,
            "user_id": user_id,
            "messages_deleted": count,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Provider Endpoints
# =============================================================================

@router.get("/providers")
async def list_providers():
    """
    List available LLM providers and their status.
    """
    try:
        provider = get_inference_provider()
        return provider.get_available_providers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
