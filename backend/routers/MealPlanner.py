"""
MealPlanner.py - AI-Powered Meal Plan Generator

Uses the SRS (Smart Retrieval System) to get nutrition context from
MealPlanner vector store and Groq LLM to generate personalized meal plans.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import json
import logging

# Groq for LLM
from groq import Groq

# SRS for retrieval
from Core.Memory.SRS import get_retrieval_chain, get_context

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
meal_router = APIRouter(prefix="/meal", tags=["Meal Planner"])

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# =============================================================================
# Request/Response Models
# =============================================================================

class MealPlanRequest(BaseModel):
    """Request model for meal plan generation."""
    age: int = Field(..., ge=15, le=50, description="User's age")
    pregnancy_stage: str = Field(
        default="trimester_2",
        description="Pregnancy stage: trimester_1, trimester_2, trimester_3, postpartum"
    )
    diet_type: str = Field(default="mixed", description="Diet type: veg, non_veg, mixed")
    allergies: List[str] = Field(default=[], description="List of food allergies")
    nutrient_focus: List[str] = Field(
        default=[],
        description="Priority nutrients to focus on, e.g., ['iron', 'calcium', 'protein']"
    )
    medical_conditions: List[str] = Field(
        default=[],
        description="Medical conditions like gestational_diabetes, anemia"
    )
    meal_duration: str = Field(
        default="daily",
        description="Plan duration: daily, weekly"
    )
    cultural_preference: str = Field(
        default="indian",
        description="Cultural food preference"
    )
    region: Optional[str] = Field(
        default=None,
        description="Specific region or area (e.g., South India, Punjab)"
    )


class QuickSuggestionRequest(BaseModel):
    """Request model for quick meal suggestions."""
    nutrients: List[str] = Field(..., description="Nutrients to focus on")
    diet_type: str = Field(default="mixed")
    meal_type: str = Field(default="any", description="breakfast, lunch, dinner, snack, any")


# =============================================================================
# Helper Functions
# =============================================================================

def build_meal_query(request: MealPlanRequest) -> str:
    """Build a query string for retrieval based on user preferences."""
    parts = [
        f"Meal plan for {request.age} year old",
        f"during {request.pregnancy_stage.replace('_', ' ')}",
        f"Diet: {request.diet_type}",
    ]
    
    if request.nutrient_focus:
        parts.append(f"Focus on: {', '.join(request.nutrient_focus)}")
    
    if request.medical_conditions:
        parts.append(f"Conditions: {', '.join(request.medical_conditions)}")
    
    if request.allergies:
        parts.append(f"Avoid: {', '.join(request.allergies)}")
    
    parts.append(f"Cultural preference: {request.cultural_preference}")
    
    if request.region:
        parts.append(f"Region: {request.region}")
    
    return ". ".join(parts)


def generate_meal_plan_with_llm(context: str, request: MealPlanRequest) -> Dict[str, Any]:
    """Use Groq LLM to generate a structured meal plan."""
    
    prompt = f"""You are a prenatal nutrition expert. Generate a personalized meal plan based on the following:

USER PROFILE:
- Age: {request.age}
- Pregnancy Stage: {request.pregnancy_stage.replace('_', ' ')}
- Diet Type: {request.diet_type}
- Allergies to avoid: {', '.join(request.allergies) if request.allergies else 'None'}
- Nutrient priorities: {', '.join(request.nutrient_focus) if request.nutrient_focus else 'General balanced nutrition'}
- Medical conditions: {', '.join(request.medical_conditions) if request.medical_conditions else 'None'}
- Duration: {request.meal_duration}
- Duration: {request.meal_duration}
- Cultural preference: {request.cultural_preference}
- Specific Region/Area: {request.region if request.region else 'General'}

NUTRITION KNOWLEDGE BASE:
{context}

INSTRUCTIONS:
1. Create a {"daily" if request.meal_duration == "daily" else "7-day"} meal plan
2. Include Breakfast, Mid-Morning Snack, Lunch, Evening Snack, and Dinner
3. Focus on the priority nutrients mentioned
4. Avoid all listed allergies strictly
5. Keep cultural preferences in mind
6. For each meal, mention key nutrients it provides

Return the response in this JSON format:
{{
    "plan_summary": "Brief overview of the plan",
    "days": [
        {{
            "day": "Day 1" or "Today",
            "meals": [
                {{
                    "type": "Breakfast",
                    "name": "Meal name",
                    "description": "Brief description",
                    "items": ["item1", "item2"],
                    "nutrients": ["iron", "protein"],
                    "calories_approx": 350
                }}
            ],
            "total_calories": 2200,
            "key_nutrients_met": ["iron", "calcium"]
        }}
    ],
    "tips": ["Tip 1", "Tip 2"],
    "foods_to_avoid": ["food1", "food2"],
    "supplements_suggested": ["Folic acid", "Iron if prescribed"]
}}

Return ONLY valid JSON, no additional text."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a prenatal nutrition expert. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON
        # Handle potential markdown code blocks
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        meal_plan = json.loads(result_text)
        return meal_plan
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        # Return a fallback structure
        return {
            "plan_summary": "Could not generate structured plan",
            "raw_response": result_text if 'result_text' in locals() else "No response",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate meal plan: {str(e)}"
        )


# =============================================================================
# API Endpoints
# =============================================================================

@meal_router.get("/test")
async def health_check():
    """Health check endpoint."""
    return {"message": "Meal Planner API is running", "status": "healthy"}


@meal_router.post("/generate")
async def generate_meal_plan(request: MealPlanRequest):
    """
    Generate a personalized meal plan using RAG (Retrieval Augmented Generation).
    
    Flow:
    1. Build query from user preferences
    2. Retrieve relevant nutrition context from MealPlanner store
    3. Generate meal plan using Groq LLM with context
    4. Return structured meal plan
    """
    try:
        # Step 1: Build query
        query = build_meal_query(request)
        logger.info(f"Generating meal plan with query: {query[:100]}...")
        
        # Step 2: Retrieve context from SRS
        context_result = get_context(
            query,
            max_context_length=3000,
            top_k_stores=2,
            top_k_chunks=8
        )
        
        context = context_result.get("context", "")
        if not context:
            context = "General prenatal nutrition guidelines: Focus on iron-rich foods, calcium, folic acid, and protein."
        
        logger.info(f"Retrieved {context_result.get('chunks_used', 0)} chunks from {context_result.get('stores_searched', [])}")
        
        # Step 3: Generate meal plan with LLM
        meal_plan = generate_meal_plan_with_llm(context, request)
        
        # Step 4: Return response
        return JSONResponse(content={
            "success": True,
            "meal_plan": meal_plan,
            "metadata": {
                "pregnancy_stage": request.pregnancy_stage,
                "diet_type": request.diet_type,
                "duration": request.meal_duration,
                "chunks_used": context_result.get("chunks_used", 0),
                "stores_searched": context_result.get("stores_searched", []),
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Meal plan generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate meal plan: {str(e)}"
        )


@meal_router.post("/suggestions")
async def get_meal_suggestions(request: QuickSuggestionRequest):
    """
    Get quick meal suggestions based on nutrient focus.
    
    Lighter endpoint for quick suggestions without full plan generation.
    """
    try:
        # Build simple query
        query = f"Foods and meals rich in {', '.join(request.nutrients)} for {request.diet_type} diet"
        if request.meal_type != "any":
            query += f" for {request.meal_type}"
        
        # Get context
        context_result = get_context(
            query,
            max_context_length=1500,
            top_k_stores=1,
            top_k_chunks=5
        )
        
        context = context_result.get("context", "")
        
        # Quick LLM call for suggestions
        prompt = f"""Based on this nutrition information:
{context}

Give 5 quick {request.meal_type} suggestions for someone needing more {', '.join(request.nutrients)}.
Diet type: {request.diet_type}

Return as JSON array:
[
    {{"name": "Meal name", "description": "Brief description", "nutrients": ["nutrient1", "nutrient2"]}}
]

Return ONLY valid JSON array."""

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800,
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        suggestions = json.loads(result_text)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "nutrients_requested": request.nutrients,
            "diet_type": request.diet_type
        }
        
    except Exception as e:
        logger.error(f"Suggestions generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )
