"""
Nutrition Analysis Engine - AnalyseFood Module

Analyzes food items to extract 5 key nutrients:
- Protein
- Fiber
- Omega-3 (EPA/DHA)
- Iron
- Vitamin D

Uses Gemini for ingredient extraction with retry wrapper,
and USDA API for nutrient lookup.
"""

import os
import json
import time
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from Core.Nutrition.MacroBreakdown import get_best_nutrient_breakdown, NutrientBreakDown, NutrientData

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API (optional - will fallback if not available)
try:
    from google import genai
    import os

    api_key = os.getenv("GEMINI_API_KEY")

    if api_key:
        client = genai.Client(api_key=api_key)
        GEMINI_MODEL_NAME = "gemini-2.5-flash"  # safest modern default
        GEMINI_AVAILABLE = True
    else:
        logger.warning("GEMINI_API_KEY not found - using fallback extraction")
        client = None
        GEMINI_MODEL_NAME = None
        GEMINI_AVAILABLE = False

except ImportError:
    logger.warning("google-genai not installed - using fallback extraction")
    client = None
    GEMINI_MODEL_NAME = None
    GEMINI_AVAILABLE = False



# ============================================================================
# Pydantic Models
# ============================================================================

class Ingredient(BaseModel):
    """Single ingredient with amount."""
    name: str
    amnt: float = Field(..., gt=0)
    unit: str = Field(default="g")  # 'g' for grams, 'ml' for milliliters


class IngredientList(BaseModel):
    """List of ingredients for a recipe."""
    name: str
    list: List[Ingredient]
    total_amount: float
    unit: str = Field(default="g")


# ============================================================================
# Ingredient Extraction with Retry
# ============================================================================

def get_ingredients(
    name: str,
    description: Optional[str] = None,
    amount: float = 100.0,
    unit: str = "g",
    max_retries: int = 2
) -> IngredientList:
    """
    Extract ingredients from food name/description using Gemini.
    
    Args:
        name: Food name (e.g., "Chicken Biryani")
        description: Optional description
        amount: Total amount in given unit
        unit: Unit of measurement ('g', 'ml', 'l')
        max_retries: Number of retries on empty response
    
    Returns:
        IngredientList with parsed ingredients
    
    Failsafe: Retries if Gemini returns empty list, falls back to name-only ingredient
    """
    if not GEMINI_AVAILABLE or client is None:
        return _create_fallback_ingredients(name, amount, unit)
    
    unit_display = {
        'g': 'grams',
        'l': 'liters',
        'ml': 'milliliters'
    }.get(unit.lower(), unit)

    desc_text = f"\nDescription: {description}" if description else ""
    
    prompt = f"""You are a world-class food composition specialist.
Your task is to break down any given food into its precise ingredients and their proportional amounts.

Rules:
1. Return ONLY valid JSON array - no markdown, no explanations
2. Format: [{{"name": "ingredient_name", "amount": value, "unit": "unit"}}, ...]
3. Use appropriate units: grams (g) for solids, milliliters (ml) for liquids
4. The sum of amounts should approximately equal the total amount provided
5. If unsure, use your expert knowledge to infer realistic amounts

Input:
Name: {name}{desc_text}
Total Amount: {amount} {unit_display}

Output the ingredient breakdown as a JSON array:"""

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Extracting ingredients for '{name}' (attempt {attempt + 1})")
            
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt
            )
            response_text = response.text.strip()
            
            # Clean markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            ingredients_data = json.loads(response_text)
            
            # Check for empty list
            if not ingredients_data:
                logger.warning(f"Empty ingredient list on attempt {attempt + 1}")
                if attempt < max_retries:
                    time.sleep(1.0 * (attempt + 1))  # Simple backoff
                    continue
            
            # Convert to Ingredient objects
            ingredient_list = []
            for item in ingredients_data:
                if isinstance(item, dict):
                    ing_name = item.get("name", "")
                    ing_amount = float(item.get("amount", item.get("amnt", 0)))
                    ing_unit = item.get("unit", "g")
                    
                    if ing_name and ing_amount > 0:
                        ingredient_list.append(Ingredient(
                            name=ing_name,
                            amnt=ing_amount,
                            unit=ing_unit
                        ))
            
            if ingredient_list:
                logger.info(f"✓ Extracted {len(ingredient_list)} ingredients")
                return IngredientList(
                    name=name,
                    list=ingredient_list,
                    total_amount=amount,
                    unit=unit
                )
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
        except Exception as e:
            logger.warning(f"Error on attempt {attempt + 1}: {e}")
        
        if attempt < max_retries:
            time.sleep(1.0 * (attempt + 1))
    
    # All retries failed - use fallback
    logger.warning(f"All attempts failed, using fallback for '{name}'")
    return _create_fallback_ingredients(name, amount, unit)


def _create_fallback_ingredients(name: str, amount: float, unit: str) -> IngredientList:
    """Create fallback when Gemini extraction fails."""
    return IngredientList(
        name=name,
        list=[Ingredient(name=name, amnt=amount, unit=unit)],
        total_amount=amount,
        unit=unit
    )


# ============================================================================
# Nutrient Analysis
# ============================================================================

def _process_single_ingredient(ingredient: Ingredient) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
    """
    Process a single ingredient and get its nutrient breakdown.
    
    Returns: (ingredient_name, nutrient_data_dict, error_message)
    """
    try:
        breakdown = get_best_nutrient_breakdown(ingredient.name)
        
        # Scale nutrients based on actual amount (USDA data is per 100g)
        scale_factor = ingredient.amnt / 100.0
        nutrient_data = {}
        
        for nutrient in breakdown.nutrients:
            scaled_amt = nutrient.amt * scale_factor
            nutrient_data[nutrient.name] = (scaled_amt, nutrient.unit)
        
        logger.info(f"✓ Processed: {ingredient.name} ({ingredient.amnt}{ingredient.unit})")
        return (ingredient.name, nutrient_data, None)
        
    except Exception as e:
        logger.error(f"✗ Error processing {ingredient.name}: {str(e)}")
        return (ingredient.name, None, str(e))


def analyse_nutrients(
    name: str,
    description: Optional[str] = None,
    amnt: float = 100.0,
    max_workers: int = 5
) -> NutrientBreakDown:
    """
    Analyze a food item and return its complete nutrient breakdown.
    
    Args:
        name: Food name
        description: Optional description
        amnt: Amount in grams
        max_workers: Max parallel workers for USDA lookups
    
    Returns:
        NutrientBreakDown with all nutrients
    """
    # Step 1: Get recipe ingredients
    recipe = get_ingredients(name, description=description, amount=amnt)
    
    nutrient_totals = defaultdict(float)
    nutrient_units = {}
    processed_ingredients = []
    
    # Step 2: Process ingredients in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ingredient = {
            executor.submit(_process_single_ingredient, ing): ing
            for ing in recipe.list
        }
        
        for future in as_completed(future_to_ingredient):
            ingredient_name, nutrient_data, error = future.result()
            if nutrient_data is not None:
                for nutrient_name, (amt, unit) in nutrient_data.items():
                    nutrient_totals[nutrient_name] += amt
                    if nutrient_name not in nutrient_units:
                        nutrient_units[nutrient_name] = unit
                processed_ingredients.append(ingredient_name)
    
    # Step 3: Build final nutrients list
    final_nutrients = [
        NutrientData(name=n_name, amt=amt, unit=nutrient_units.get(n_name, "g"))
        for n_name, amt in nutrient_totals.items()
    ]
    
    return NutrientBreakDown(
        name=recipe.name,
        id=hash(recipe.name) % (10 ** 8),
        category="recipe",
        nutrients=final_nutrients
    )


# ============================================================================
# Clean & Filter to 5 Key Nutrients
# ============================================================================

# Priority nutrients we track
PRIORITY_NUTRIENTS = {
    'Protein': 'macros',
    'Fiber, total dietary': 'macros',
    'Iron, Fe': 'minerals',
    'Iron': 'minerals',
    'Vitamin D (D2 + D3)': 'vitamins',
    'Vitamin D': 'vitamins',
    'Fatty acids, total polyunsaturated': 'fats',
    'PUFA 20:5 n-3 (EPA)': 'fats',
    'PUFA 22:6 n-3 (DHA)': 'fats',
}

DISPLAY_NAMES = {
    'Protein': 'Protein',
    'Fiber, total dietary': 'Fiber',
    'Iron, Fe': 'Iron',
    'Iron': 'Iron',
    'Vitamin D (D2 + D3)': 'Vitamin D',
    'Vitamin D': 'Vitamin D',
    'Fatty acids, total polyunsaturated': 'Omega-3',
    'PUFA 20:5 n-3 (EPA)': 'Omega-3 (EPA)',
    'PUFA 22:6 n-3 (DHA)': 'Omega-3 (DHA)',
}


def _get_display_name(nutrient_name: str) -> str:
    """Convert technical nutrient name to display name."""
    return DISPLAY_NAMES.get(nutrient_name, nutrient_name)


def _normalize_units(amt: float, unit: str) -> Tuple[float, str]:
    """Normalize units for display."""
    unit_upper = unit.upper() if unit else ""
    if unit_upper == 'G':
        return amt, 'g'
    if unit_upper == 'MG':
        return amt, 'mg'
    if unit_upper == 'UG':
        return amt, 'mcg'
    return amt, unit.lower() if unit else 'g'


def clean_nutrient_response(raw_data: NutrientBreakDown) -> NutrientBreakDown:
    """
    Filter response to only include the 5 tracked nutrients:
    Protein, Fiber, Omega-3 (EPA/DHA), Iron, and Vitamin D.
    """
    nutrient_dict = {n.name: n for n in raw_data.nutrients}
    cleaned_nutrients = []
    seen_display_names = set()
    
    for nutrient_name in PRIORITY_NUTRIENTS.keys():
        if nutrient_name in nutrient_dict:
            nutrient = nutrient_dict[nutrient_name]
            display_name = _get_display_name(nutrient_name)
            
            # Avoid duplicates (e.g., multiple Omega-3 entries)
            if display_name in seen_display_names:
                # Add to existing
                for cn in cleaned_nutrients:
                    if cn.name == display_name:
                        cn.amt += nutrient.amt
                        break
                continue
            
            amt, unit = _normalize_units(nutrient.amt, nutrient.unit)
            cleaned_nutrients.append(NutrientData(
                name=display_name,
                amt=round(amt, 2),
                unit=unit
            ))
            seen_display_names.add(display_name)
    
    return NutrientBreakDown(
        name=raw_data.name,
        id=raw_data.id,
        category=raw_data.category,
        nutrients=cleaned_nutrients
    )


# ============================================================================
# Main API Function
# ============================================================================

def nutrient_analysis(name: str, description: Optional[str] = None, amnt: float = 100.0) -> NutrientBreakDown:
    """
    Main entry point: Analyze food and return 5 key nutrients.
    
    Args:
        name: Food name (e.g., "Chicken Biryani")
        description: Optional description
        amnt: Amount in grams
    
    Returns:
        NutrientBreakDown with only: Protein, Fiber, Omega-3, Iron, Vitamin D
    """
    logger.info(f"Analyzing: {name} ({amnt}g)")
    breakdown = analyse_nutrients(name, description, amnt)
    return clean_nutrient_response(breakdown)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Test the module
    result = nutrient_analysis("Chole Bature", "with spinach and tomatoes", 300)
    
    print(f"\n{'='*50}")
    print(f"Food: {result.name}")
    print(f"Category: {result.category}")
    print(f"\nTracked Nutrients:")
    print(f"{'='*50}")
    for nutrient in result.nutrients:
        print(f"  {nutrient.name}: {nutrient.amt} {nutrient.unit}")