"""
Nutrition Analysis Engine - AnalyseFood Module (Optimized)

Analyzes food items to extract 5 key nutrients:
- Protein
- Fiber
- Omega-3 (EPA/DHA)
- Iron
- Vitamin D

Optimizations:
- Caching for repeated ingredients
- Better JSON parsing with fallbacks
- Final AI-powered nutrient adjustment
- Improved error handling
"""

import os
import json
import time
import logging
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple, Dict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from Core.Nutrition.MacroBreakdown import get_best_nutrient_breakdown, NutrientBreakDown, NutrientData

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
try:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")

    if api_key:
        client = genai.Client(api_key=api_key)
        GEMINI_MODEL_NAME = "gemini-2.5-flash"
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
# Caching Layer
# ============================================================================

_nutrient_cache: Dict[str, dict] = {}


# ============================================================================
# Pydantic Models
# ============================================================================

class Ingredient(BaseModel):
    """Single ingredient with amount."""
    name: str
    amnt: float = Field(..., gt=0)
    unit: str = Field(default="g")


class IngredientList(BaseModel):
    """List of ingredients for a recipe."""
    name: str
    list: List[Ingredient]
    total_amount: float
    unit: str = Field(default="g")


# ============================================================================
# Robust JSON Extraction
# ============================================================================

def extract_json_from_text(text: str) -> Optional[list]:
    """
    Robustly extract JSON array from text, handling markdown and malformed JSON.
    """
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()

    # Try direct parse first
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except:
        pass

    # Find JSON array in text
    match = re.search(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return data
        except:
            pass

    # Try to fix common JSON errors
    try:
        # Fix single quotes
        text = text.replace("'", '"')
        # Fix trailing commas
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except:
        pass

    return None


# ============================================================================
# Ingredient Extraction
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
    """
    if not GEMINI_AVAILABLE or client is None:
        return _create_fallback_ingredients(name, amount, unit)

    unit_display = {
        'g': 'grams',
        'l': 'liters',
        'ml': 'milliliters'
    }.get(unit.lower(), unit)

    desc_text = f"\nDescription: {description}" if description else ""

    prompt = f"""You are a food composition specialist. Break down this food into its ingredients.

Food: {name}{desc_text}
Total Amount: {amount} {unit_display}

Return ONLY a valid JSON array of ingredients. Each ingredient should have:
- "name": ingredient name (string)
- "amount": quantity (number)
- "unit": measurement unit ("g" or "ml")

The sum of amounts should approximately equal {amount}.

Example format:
[
  {{"name": "chickpeas", "amount": 150, "unit": "g"}},
  {{"name": "flour", "amount": 100, "unit": "g"}},
  {{"name": "oil", "amount": 50, "unit": "ml"}}
]

Return ONLY the JSON array, nothing else:"""

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Extracting ingredients for '{name}' (attempt {attempt + 1})")

            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt
            )
            response_text = response.text.strip()

            # Robust JSON extraction
            ingredients_data = extract_json_from_text(response_text)

            if not ingredients_data:
                logger.warning(f"Could not extract JSON on attempt {attempt + 1}")
                if attempt < max_retries:
                    time.sleep(1.0)
                    continue
                break

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

        except Exception as e:
            logger.warning(f"Error on attempt {attempt + 1}: {e}")

        if attempt < max_retries:
            time.sleep(1.0)

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
# Cached Nutrient Lookup
# ============================================================================

def _process_single_ingredient(ingredient: Ingredient) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
    """
    Process a single ingredient with caching.
    """
    cache_key = f"{ingredient.name.lower()}"

    # Check cache first (cache stores per 100g data)
    if cache_key in _nutrient_cache:
        logger.info(f"✓ Cache hit: {ingredient.name}")
        cached_data = _nutrient_cache[cache_key]

        # Scale from cache
        scale_factor = ingredient.amnt / 100.0
        nutrient_data = {}
        for nutrient_name, (base_amt, unit) in cached_data.items():
            nutrient_data[nutrient_name] = (base_amt * scale_factor, unit)

        return (ingredient.name, nutrient_data, None)

    try:
        breakdown = get_best_nutrient_breakdown(ingredient.name)

        # Store in cache (per 100g)
        cache_data = {}
        for nutrient in breakdown.nutrients:
            cache_data[nutrient.name] = (nutrient.amt, nutrient.unit)
        _nutrient_cache[cache_key] = cache_data

        # Scale for actual amount
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


# ============================================================================
# Nutrient Analysis
# ============================================================================

def analyse_nutrients(
    name: str,
    description: Optional[str] = None,
    amnt: float = 100.0,
    max_workers: int = 5
) -> NutrientBreakDown:
    """
    Analyze a food item and return its complete nutrient breakdown.
    """
    start_time = time.time()

    # Get recipe ingredients
    recipe = get_ingredients(name, description=description, amount=amnt)

    nutrient_totals = defaultdict(float)
    nutrient_units = {}

    # Process all ingredients in parallel
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

    final_nutrients = [
        NutrientData(name=n_name, amt=amt, unit=nutrient_units.get(n_name, "g"))
        for n_name, amt in nutrient_totals.items()
    ]

    logger.info(f"Analysis completed in {time.time() - start_time:.2f}s")

    return NutrientBreakDown(
        name=recipe.name,
        id=hash(recipe.name) % (10 ** 8),
        category="recipe",
        nutrients=final_nutrients
    )


# ============================================================================
# Nutrient Filtering
# ============================================================================

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
    return DISPLAY_NAMES.get(nutrient_name, nutrient_name)


def _normalize_units(amt: float, unit: str) -> Tuple[float, str]:
    unit_upper = unit.upper() if unit else ""
    if unit_upper == 'G':
        return amt, 'g'
    if unit_upper == 'MG':
        return amt, 'mg'
    if unit_upper == 'UG':
        return amt, 'mcg'
    return amt, unit.lower() if unit else 'g'


def clean_nutrient_response(raw_data: NutrientBreakDown) -> NutrientBreakDown:
    """Filter to 5 key nutrients."""
    nutrient_dict = {n.name: n for n in raw_data.nutrients}
    cleaned_nutrients = []
    seen_display_names = set()

    for nutrient_name in PRIORITY_NUTRIENTS.keys():
        if nutrient_name in nutrient_dict:
            nutrient = nutrient_dict[nutrient_name]
            display_name = _get_display_name(nutrient_name)

            if display_name in seen_display_names:
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
# AI-Powered Nutrient Adjustment
# ============================================================================

def adjust_nutrients_with_ai(
    food_name: str,
    amount: float,
    nutrients: List[NutrientData],
    description: Optional[str] = None
) -> List[NutrientData]:
    """
    Use Gemini to validate and adjust nutrient values based on food context.
    """
    if not GEMINI_AVAILABLE or client is None:
        logger.info("Gemini not available, skipping adjustment")
        return nutrients

    if not nutrients:
        logger.warning("No nutrients to adjust")
        return nutrients

    # Build current nutrient summary
    nutrient_summary = "\n".join([
        f"  - {n.name}: {n.amt} {n.unit}" for n in nutrients
    ])

    desc_text = f"\nDescription: {description}" if description else ""

    prompt = f"""You are a nutrition expert. Review and adjust these nutrient values if needed.

Food: {food_name}{desc_text}
Amount: {amount}g

Current Nutrient Values:
{nutrient_summary}

Instructions:
1. Check if these values are realistic for this food and amount
2. Adjust any values that seem incorrect
3. Keep values that seem correct
4. Return ONLY a JSON array

Format:
[
  {{"name": "Protein", "amt": 25.5, "unit": "g"}},
  {{"name": "Fiber", "amt": 8.2, "unit": "g"}}
]

Return ONLY the JSON array:"""

    try:
        logger.info("Requesting AI nutrient adjustment...")

        response = client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt
        )
        response_text = response.text.strip()

        # Robust JSON extraction
        adjusted_data = extract_json_from_text(response_text)

        if not adjusted_data:
            logger.warning("Could not extract JSON from AI response, using original")
            return nutrients

        # Convert to NutrientData objects
        adjusted_nutrients = []
        for item in adjusted_data:
            if isinstance(item, dict):
                adj_name = item.get("name", "")
                adj_amt = item.get("amt", 0)
                adj_unit = item.get("unit", "g")

                if adj_name and adj_amt is not None:
                    adjusted_nutrients.append(NutrientData(
                        name=adj_name,
                        amt=round(float(adj_amt), 2),
                        unit=adj_unit
                    ))

        if adjusted_nutrients:
            logger.info(f"✓ AI adjusted {len(adjusted_nutrients)} nutrients")
            return adjusted_nutrients
        else:
            logger.warning("AI returned empty nutrients, using original")
            return nutrients

    except Exception as e:
        logger.error(f"AI adjustment failed: {e}, using original values")
        return nutrients


# ============================================================================
# Main API Function
# ============================================================================

def nutrient_analysis(
    name: str,
    description: Optional[str] = None,
    amnt: float = 100.0,
    use_ai_adjustment: bool = True
) -> NutrientBreakDown:
    """
    Main entry point: Analyze food and return 5 key nutrients.

    Args:
        name: Food name (e.g., "Chicken Biryani")
        description: Optional description
        amnt: Amount in grams
        use_ai_adjustment: Whether to use AI to adjust final values

    Returns:
        NutrientBreakDown with: Protein, Fiber, Omega-3, Iron, Vitamin D
    """
    logger.info(f"Analyzing: {name} ({amnt}g)")

    total_start = time.time()

    # Step 1: Get raw nutrient data
    breakdown = analyse_nutrients(name, description, amnt)

    # Step 2: Clean to 5 key nutrients
    cleaned = clean_nutrient_response(breakdown)

    # Step 3: AI adjustment for accuracy (optional)
    if use_ai_adjustment and cleaned.nutrients:
        adjusted_nutrients = adjust_nutrients_with_ai(
            food_name=name,
            amount=amnt,
            nutrients=cleaned.nutrients,
            description=description
        )
        cleaned.nutrients = adjusted_nutrients

    logger.info(f"✓ Total processing time: {time.time() - total_start:.2f}s")

    return cleaned


# ============================================================================
# Cache Management
# ============================================================================

def clear_nutrient_cache():
    """Clear the ingredient nutrient cache."""
    global _nutrient_cache
    _nutrient_cache.clear()
    logger.info("Nutrient cache cleared")


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return {
        "cache_size": len(_nutrient_cache),
        "cached_ingredients": list(_nutrient_cache.keys())
    }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Nutrition Analysis")
    print("="*60)

    result = nutrient_analysis(
        "Chole Bhature",
        "North Indian dish with chickpea curry and fried bread",
        300,
        use_ai_adjustment=True
    )

    print(f"\nFood: {result.name}")
    print(f"Category: {result.category}")
    print(f"\nNutrients:")
    print("="*60)
    for nutrient in result.nutrients:
        print(f"  {nutrient.name}: {nutrient.amt} {nutrient.unit}")

    print("\n" + "="*60)
    cache_info = get_cache_stats()
    print(f"Cache: {cache_info['cache_size']} ingredients cached")
    print("="*60)