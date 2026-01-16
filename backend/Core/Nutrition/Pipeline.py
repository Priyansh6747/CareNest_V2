"""
Full Nutrition Pipeline Module

Complete meal logging pipeline:
1. User provides: name, description, amount, image (optional)
2. AI analyzes: extracts nutrients (protein, fiber, iron, vitamin D, omega-3)
3. Returns: structured nutrient data ready for storage

This module bridges user input with the AnalyseFood engine.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from Core.Nutrition.AnalyseFood import nutrient_analysis, NutrientBreakDown
from Core.Nutrition.Storage import (
    NutrientAnalysis,
    MealCreate,
    Meal,
    create_meal
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Input Models
# ============================================================================

class MealInput(BaseModel):
    """User input for meal logging - just name, description, and amount."""
    name: str = Field(..., description="Meal name (e.g., 'Chole Bhature')")
    desc: Optional[str] = Field(default=None, description="Meal description")
    amnt: float = Field(default=100.0, gt=0, description="Amount in grams")
    image_url: Optional[str] = Field(default=None, description="Optional image URL for future image analysis")


class AnalysisResult(BaseModel):
    """Result of nutrient analysis."""
    name: str
    description: Optional[str]
    amount: float
    nutrients: Dict[str, float]
    analysis: NutrientAnalysis
    success: bool
    message: Optional[str] = None


# ============================================================================
# Pipeline Functions
# ============================================================================

def analyze_meal(
    name: str,
    desc: Optional[str] = None,
    amnt: float = 100.0,
    use_ai_adjustment: bool = True
) -> AnalysisResult:
    """
    Analyze a meal and return structured nutrient data.
    
    This is the core pipeline function:
    1. Takes user input (name, description, amount)
    2. Uses AI to extract ingredients and calculate nutrients
    3. Returns structured nutrient analysis
    
    Args:
        name: Meal name (e.g., "Chole Bhature")
        desc: Optional description (e.g., "Chickpea curry with fried bread")
        amnt: Amount in grams
        use_ai_adjustment: Whether to use AI to refine nutrient values
    
    Returns:
        AnalysisResult with nutrients and analysis data
    """
    logger.info(f"Starting meal analysis for: {name} ({amnt}g)")
    
    try:
        # Step 1: Run AI-powered nutrient analysis
        breakdown = nutrient_analysis(
            name=name,
            description=desc,
            amnt=amnt,
            use_ai_adjustment=use_ai_adjustment
        )
        
        # Step 2: Convert to structured format
        nutrient_dict = {}
        for nutrient in breakdown.nutrients:
            key = nutrient.name.lower().replace(' ', '_').replace('-', '_')
            nutrient_dict[nutrient.name] = nutrient.amt
        
        # Step 3: Create NutrientAnalysis object
        analysis = _breakdown_to_analysis(breakdown)
        
        logger.info(f"✓ Analysis complete for: {name}")
        
        return AnalysisResult(
            name=name,
            description=desc,
            amount=amnt,
            nutrients=nutrient_dict,
            analysis=analysis,
            success=True
        )
        
    except Exception as e:
        logger.error(f"✗ Analysis failed for {name}: {str(e)}")
        
        # Return empty analysis on failure
        return AnalysisResult(
            name=name,
            description=desc,
            amount=amnt,
            nutrients={},
            analysis=NutrientAnalysis(
                protein=0.0,
                fiber=0.0,
                iron=0.0,
                vitamin_d=0.0,
                omega_3=0.0
            ),
            success=False,
            message=str(e)
        )


async def analyze_and_save_meal(
    user_id: str,
    name: str,
    desc: Optional[str] = None,
    amnt: float = 100.0,
    use_ai_adjustment: bool = True
) -> Meal:
    """
    Full pipeline: Analyze meal and save to database.
    
    Args:
        user_id: User ID for storage
        name: Meal name
        desc: Optional description
        amnt: Amount in grams
        use_ai_adjustment: Whether to use AI refinement
    
    Returns:
        Saved Meal object with ID and timestamps
    
    Raises:
        Exception: If analysis or save fails
    """
    logger.info(f"Full pipeline: {name} for user {user_id}")
    
    # Step 1: Analyze
    result = analyze_meal(name, desc, amnt, use_ai_adjustment)
    
    if not result.success:
        raise Exception(f"Analysis failed: {result.message}")
    
    # Step 2: Create meal data
    meal_data = MealCreate(
        name=name,
        desc=desc,
        amnt=amnt,
        analysis=result.analysis
    )
    
    # Step 3: Save to database
    meal = await create_meal(user_id, meal_data)
    
    logger.info(f"✓ Meal saved: {meal.id}")
    
    return meal


def _breakdown_to_analysis(breakdown: NutrientBreakDown) -> NutrientAnalysis:
    """Convert NutrientBreakDown to NutrientAnalysis format."""
    nutrient_map = {n.name.lower(): n.amt for n in breakdown.nutrients}
    
    return NutrientAnalysis(
        protein=nutrient_map.get('protein', 0.0),
        fiber=nutrient_map.get('fiber', 0.0),
        iron=nutrient_map.get('iron', 0.0),
        vitamin_d=nutrient_map.get('vitamin d', 0.0),
        omega_3=nutrient_map.get('omega-3', nutrient_map.get('omega_3', 0.0)),
        omega_3_epa=nutrient_map.get('omega-3 (epa)', 0.0),
        omega_3_dha=nutrient_map.get('omega-3 (dha)', 0.0),
    )


# ============================================================================
# Convenience Functions
# ============================================================================

def quick_analyze(name: str, amount: float = 100.0) -> Dict[str, Any]:
    """
    Quick analysis - returns simple dict for easy use.
    
    Example:
        >>> result = quick_analyze("Banana", 120)
        >>> print(result['nutrients'])
        {'Protein': 1.3, 'Fiber': 2.6, ...}
    """
    result = analyze_meal(name, amnt=amount)
    
    return {
        "name": name,
        "amount": amount,
        "nutrients": result.nutrients,
        "success": result.success
    }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Test the pipeline
    print("\n" + "=" * 60)
    print("Testing Full Nutrition Pipeline")
    print("=" * 60)
    
    result = analyze_meal(
        name="Chole Bhature",
        desc="North Indian chickpea curry with fried bread",
        amnt=300
    )
    
    print(f"\nMeal: {result.name}")
    print(f"Amount: {result.amount}g")
    print(f"Success: {result.success}")
    print("\nNutrients:")
    for name, value in result.nutrients.items():
        print(f"  {name}: {value}")
    
    print("\nAnalysis Object:")
    print(f"  Protein: {result.analysis.protein}g")
    print(f"  Fiber: {result.analysis.fiber}g")
    print(f"  Iron: {result.analysis.iron}mg")
    print(f"  Vitamin D: {result.analysis.vitamin_d}mcg")
    print(f"  Omega-3: {result.analysis.omega_3}g")
