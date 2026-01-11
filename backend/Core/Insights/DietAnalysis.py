"""
DietAnalysis.py - Pregnancy Nutrition Analysis Module

This module provides nutrition analysis specifically designed for pregnant women,
with trimester-specific Recommended Daily Allowances (RDAs) based on medical guidelines.

Key Features:
    - Trimester-specific RDAs for all tracked nutrients
    - Pregnancy-adjusted BMR/TDEE calculations
    - Nutrient gap analysis comparing intake vs recommendations
    - Variability pattern detection

Tracked Nutrients:
    - protein (g)
    - fiber (g)
    - iron (mg)
    - vitamin_d (mcg)
    - omega_3 (g)
    - omega_3_epa (g)
    - omega_3_dha (g)
    - calcium (mg)
    - folate (mcg)
"""

from typing import List, Dict, Any, Union
from pydantic import BaseModel
from datetime import date, datetime
from enum import Enum
import statistics
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

class Nutrient(BaseModel):
    amt: float
    unit: str
    name: str


class Meal(BaseModel):
    id: str
    nutrients: List[Nutrient]
    serving_size: float
    category: str
    status: int
    food_id: int
    timestamp: datetime
    name: str


class DailyStats(BaseModel):
    date: date
    meal_count: int
    meals: List[Meal]
    nutrient_totals: List[Nutrient]


class WeeklyNutrient(BaseModel):
    week_start: date
    week_end: date
    daily_stats: List[DailyStats]
    total_meals: int
    days_tracked: int
    weekly_nutrient_totals: List[Nutrient]
    average_daily_nutrients: List[Nutrient]


# =============================================================================
# Pregnancy-Specific RDA Constants
# =============================================================================

# Pregnancy Stage enum (matches schema.py PregnancyStage)
class PregnancyStageLocal(str, Enum):
    trimester_1 = "trimester_1"
    trimester_2 = "trimester_2"
    trimester_3 = "trimester_3"
    postpartum = "postpartum"


# RDA values by trimester based on medical guidelines
# Sources: NIH, WHO, ACOG guidelines
PREGNANCY_RDA = {
    # Macronutrients
    "protein_g": {
        "trimester_1": 46.0,   # Same as non-pregnant
        "trimester_2": 71.0,   # +25g increase
        "trimester_3": 71.0,   # +25g increase
        "postpartum": 71.0,    # Lactation requires higher protein
    },
    "fiber_g": {
        "trimester_1": 28.0,
        "trimester_2": 28.0,
        "trimester_3": 28.0,
        "postpartum": 29.0,
    },
    
    # Micronutrients
    "iron_mg": {
        "trimester_1": 27.0,   # Critical for blood volume expansion
        "trimester_2": 27.0,
        "trimester_3": 27.0,
        "postpartum": 9.0,     # Returns to lower levels
    },
    "vitamin_d_mcg": {
        "trimester_1": 15.0,   # 600 IU
        "trimester_2": 15.0,
        "trimester_3": 15.0,
        "postpartum": 15.0,
    },
    "calcium_mg": {
        "trimester_1": 1000.0,  # 1300 for teens <19
        "trimester_2": 1000.0,
        "trimester_3": 1000.0,  # Fetal demand peaks in T3
        "postpartum": 1000.0,
    },
    "folate_mcg": {
        "trimester_1": 600.0,   # Critical for neural tube development
        "trimester_2": 600.0,
        "trimester_3": 600.0,
        "postpartum": 500.0,
    },
    
    # Omega-3 Fatty Acids (mg)
    "omega_3_g": {
        "trimester_1": 1.4,    # Combined EPA + DHA recommendation
        "trimester_2": 1.4,
        "trimester_3": 1.4,
        "postpartum": 1.3,
    },
    "omega_3_epa_g": {
        "trimester_1": 0.2,    # 200mg minimum
        "trimester_2": 0.25,   # 250mg
        "trimester_3": 0.25,
        "postpartum": 0.2,
    },
    "omega_3_dha_g": {
        "trimester_1": 0.2,    # 200mg minimum for brain development
        "trimester_2": 0.2,
        "trimester_3": 0.3,    # 300mg in T3 for fetal brain
        "postpartum": 0.2,
    },
}

# Additional calorie requirements during pregnancy
PREGNANCY_CALORIE_ADJUSTMENT = {
    "trimester_1": 0,      # No additional calories needed
    "trimester_2": 340,    # +340 kcal/day
    "trimester_3": 450,    # +450 kcal/day
    "postpartum": 330,     # For lactation (partial breastfeeding)
}


# =============================================================================
# Helper Functions
# =============================================================================

def dict_to_weekly_nutrient(data: Dict[str, Any]) -> WeeklyNutrient:
    """Convert a dictionary to WeeklyNutrient model."""
    weekly_nutrient_totals = [
        Nutrient(amt=n["amt"], unit=n["unit"], name=n["name"])
        for n in data.get("weekly_nutrient_totals", [])
    ]

    average_daily_nutrients = [
        Nutrient(amt=n["amt"], unit=n["unit"], name=n["name"])
        for n in data.get("average_daily_nutrients", [])
    ]

    daily_stats_list = []
    for day_data in data.get("daily_stats", []):
        nutrient_totals = [
            Nutrient(amt=n["amt"], unit=n["unit"], name=n["name"])
            for n in day_data.get("nutrient_totals", [])
        ]

        meals = []
        for meal_data in day_data.get("meals", []):
            meal_nutrients = [
                Nutrient(amt=n["amt"], unit=n["unit"], name=n["name"])
                for n in meal_data.get("nutrients", [])
            ]

            meals.append(Meal(
                id=meal_data["id"],
                nutrients=meal_nutrients,
                serving_size=meal_data["serving_size"],
                category=meal_data["category"],
                status=meal_data["status"],
                food_id=meal_data["food_id"],
                timestamp=meal_data["timestamp"],
                name=meal_data["name"]
            ))

        daily_stats_list.append(DailyStats(
            date=day_data["date"],
            meal_count=day_data["meal_count"],
            meals=meals,
            nutrient_totals=nutrient_totals
        ))

    return WeeklyNutrient(
        week_start=data["week_start"],
        week_end=data["week_end"],
        daily_stats=daily_stats_list,
        total_meals=data["total_meals"],
        days_tracked=data["days_tracked"],
        weekly_nutrient_totals=weekly_nutrient_totals,
        average_daily_nutrients=average_daily_nutrients
    )


def get_pregnancy_rda(
    nutrient: str,
    trimester: str,
    age: int = 25
) -> float:
    """
    Get the RDA for a specific nutrient based on pregnancy stage.
    
    Args:
        nutrient: Nutrient name (e.g., "protein_g", "iron_mg")
        trimester: Pregnancy stage (trimester_1, trimester_2, trimester_3, postpartum)
        age: Mother's age (affects calcium RDA for teens)
    
    Returns:
        RDA value for the nutrient
    """
    if nutrient not in PREGNANCY_RDA:
        logger.warning(f"Unknown nutrient '{nutrient}', returning 0")
        return 0.0
    
    rda = PREGNANCY_RDA[nutrient].get(trimester, 0.0)
    
    # Adjust calcium for teens
    if nutrient == "calcium_mg" and age < 19:
        rda = 1300.0
    
    return rda


def _compute_variability_patterns(weekly_data: WeeklyNutrient) -> Dict[str, str]:
    """
    Analyze daily nutrient intake variability.
    
    Returns patterns like {"protein_variability": "low", "iron_variability": "high"}
    """
    patterns = {}
    nutrient_daily_values = {}

    for day_stats in weekly_data.daily_stats:
        for nutrient in day_stats.nutrient_totals:
            name = nutrient.name.lower()
            if name not in nutrient_daily_values:
                nutrient_daily_values[name] = []
            nutrient_daily_values[name].append(nutrient.amt)

    for nutrient_name, values in nutrient_daily_values.items():
        if len(values) < 2:
            patterns[f"{nutrient_name}_variability"] = "unknown"
            continue

        mean_val = statistics.mean(values)
        if mean_val == 0:
            patterns[f"{nutrient_name}_variability"] = "unknown"
            continue

        std_dev = statistics.stdev(values)
        coefficient_of_variation = (std_dev / mean_val) * 100

        if coefficient_of_variation < 15:
            variability = "low"
        elif coefficient_of_variation < 30:
            variability = "medium"
        else:
            variability = "high"

        patterns[f"{nutrient_name}_variability"] = variability

    return patterns


# =============================================================================
# Main Pregnancy Nutrition Analysis
# =============================================================================

def compute_pregnancy_needs(
    weekly_nutrition_summary: Union[WeeklyNutrient, Dict[str, Any]],
    trimester: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    activity_factor: float = 1.4
) -> Dict[str, Any]:
    """
    Compute nutrition needs for a pregnant woman based on trimester.
    
    This is the main function for pregnancy-specific dietary analysis.
    It calculates:
        - Pregnancy-adjusted TDEE (with trimester calorie additions)
        - Trimester-specific RDA targets for all tracked nutrients
        - Current intake vs recommendations
        - Nutrient gaps (positive = deficit, negative = surplus)
        - Intake variability patterns
    
    Args:
        weekly_nutrition_summary: Weekly nutrition data from DataExtractor
        trimester: Current pregnancy stage (trimester_1, trimester_2, trimester_3, postpartum)
        age: Mother's age in years
        height_cm: Height in centimeters
        weight_kg: Current weight in kilograms (pre-pregnancy weight recommended)
        activity_factor: Activity multiplier (default 1.4 for light activity)
            - 1.2: Sedentary (little or no exercise)
            - 1.4: Lightly active (light exercise 1-3 days/week)
            - 1.6: Moderately active (moderate exercise 3-5 days/week)
            - 1.75: Very active (hard exercise 6-7 days/week)
    
    Returns:
        Dict containing:
            - TDEE: Total Daily Energy Expenditure (adjusted for pregnancy)
            - trimester: Current pregnancy stage
            - rda_targets: All nutrient RDAs for this trimester
            - weekly_actual: Average daily intake from the week
            - nutrient_gaps: Difference between RDA and actual (positive = deficit)
            - percentage_met: What % of each RDA is being met
            - priority_nutrients: Top 3 nutrients with biggest gaps
            - patterns: Variability analysis
    """
    logger.info(f"Computing pregnancy needs for {trimester}, age {age}")
    
    # Convert dict to model if needed
    if isinstance(weekly_nutrition_summary, dict):
        weekly_nutrition_summary = dict_to_weekly_nutrient(weekly_nutrition_summary)
    
    # Step 1: Compute pregnancy-adjusted TDEE
    # Using Mifflin-St Jeor formula (for females)
    BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    base_TDEE = BMR * activity_factor
    
    # Add pregnancy calorie adjustment
    calorie_adjustment = PREGNANCY_CALORIE_ADJUSTMENT.get(trimester, 0)
    adjusted_TDEE = base_TDEE + calorie_adjustment
    
    logger.info(f"BMR: {BMR:.0f}, Base TDEE: {base_TDEE:.0f}, Adjusted TDEE: {adjusted_TDEE:.0f}")
    
    # Step 2: Get all RDA targets for this trimester
    rda_targets = {}
    for nutrient in PREGNANCY_RDA.keys():
        rda_targets[nutrient] = get_pregnancy_rda(nutrient, trimester, age)
    
    # Step 3: Extract actual weekly intake
    weekly_actual = {}
    
    # Mapping from various nutrient name formats to our standard names
    name_map = {
        "protein": "protein_g",
        "protein_g": "protein_g",
        "fiber": "fiber_g",
        "fiber_g": "fiber_g",
        "iron": "iron_mg",
        "iron_g": "iron_mg",  # Convert g to mg handled below
        "iron_mg": "iron_mg",
        "vitamin_d": "vitamin_d_mcg",
        "vitamin_d_mcg": "vitamin_d_mcg",
        "vitd": "vitamin_d_mcg",
        "vitamin d": "vitamin_d_mcg",
        "calcium": "calcium_mg",
        "calcium_mg": "calcium_mg",
        "folate": "folate_mcg",
        "folate_mcg": "folate_mcg",
        "folic_acid": "folate_mcg",
        "omega_3": "omega_3_g",
        "omega_3_g": "omega_3_g",
        "omega3": "omega_3_g",
        "omega_3_epa": "omega_3_epa_g",
        "omega_3_epa_g": "omega_3_epa_g",
        "epa": "omega_3_epa_g",
        "omega_3_dha": "omega_3_dha_g",
        "omega_3_dha_g": "omega_3_dha_g",
        "dha": "omega_3_dha_g",
    }
    
    for nutrient in weekly_nutrition_summary.average_daily_nutrients:
        name_lower = nutrient.name.lower().replace(" ", "_")
        normalized_name = name_map.get(name_lower, name_lower)
        
        value = nutrient.amt
        
        # Handle unit conversions
        # Iron is sometimes tracked in grams but RDA is in mg
        if normalized_name == "iron_mg" and nutrient.unit == "g":
            value = value * 1000  # Convert g to mg
        
        weekly_actual[normalized_name] = round(value, 2)
    
    # Step 4: Calculate nutrient gaps and percentages
    nutrient_gaps = {}
    percentage_met = {}
    
    for nutrient, target in rda_targets.items():
        actual = weekly_actual.get(nutrient, 0)
        gap = round(target - actual, 2)
        nutrient_gaps[nutrient] = gap
        
        if target > 0:
            pct = min((actual / target) * 100, 200)  # Cap at 200%
            percentage_met[nutrient] = round(pct, 1)
        else:
            percentage_met[nutrient] = 100.0
    
    # Step 5: Identify priority nutrients (biggest gaps as % of RDA)
    gap_percentages = []
    for nutrient, target in rda_targets.items():
        if target > 0:
            actual = weekly_actual.get(nutrient, 0)
            gap_pct = ((target - actual) / target) * 100
            if gap_pct > 0:  # Only include deficits
                gap_percentages.append((nutrient, gap_pct))
    
    # Sort by gap percentage (descending) and take top 3
    gap_percentages.sort(key=lambda x: x[1], reverse=True)
    priority_nutrients = [item[0] for item in gap_percentages[:3]]
    
    # Step 6: Compute variability patterns
    patterns = _compute_variability_patterns(weekly_nutrition_summary)
    
    # Step 7: Prepare result
    result = {
        "TDEE": round(adjusted_TDEE, 0),
        "BMR": round(BMR, 0),
        "calorie_adjustment": calorie_adjustment,
        "trimester": trimester,
        "age": age,
        "rda_targets": rda_targets,
        "weekly_actual": weekly_actual,
        "nutrient_gaps": nutrient_gaps,
        "percentage_met": percentage_met,
        "priority_nutrients": priority_nutrients,
        "patterns": patterns,
        "days_tracked": weekly_nutrition_summary.days_tracked,
        "total_meals": weekly_nutrition_summary.total_meals,
    }
    
    logger.info(f"Analysis complete. Priority nutrients: {priority_nutrients}")
    
    return result


# =============================================================================
# Legacy Function (preserved for backward compatibility)
# =============================================================================

def compute_user_needs(
        weekly_nutrition_summary: Union[WeeklyNutrient, Dict[str, Any]],
        gender: str,
        age: int,
        height_cm: float,
        weight_kg: float,
        activity_factor: float,
        goal: str
) -> Dict[str, Any]:
    """
    Legacy function for general nutrition analysis.
    For pregnancy-specific analysis, use compute_pregnancy_needs() instead.
    """
    if isinstance(weekly_nutrition_summary, dict):
        weekly_nutrition_summary = dict_to_weekly_nutrient(weekly_nutrition_summary)

    # Compute BMR using Mifflin-St Jeor formula
    if gender.lower() == "male":
        BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    TDEE = BMR * activity_factor

    goal_adjustments = {
        "weight_loss": 0.875,
        "maintenance": 1.0,
        "weight_gain": 1.15,
        "muscle_gain": 1.2
    }
    adjusted_TDEE = TDEE * goal_adjustments.get(goal.lower(), 1.0)

    macro_ratios = {
        "weight_loss": {"protein": 0.25, "fat": 0.25, "carbs": 0.50},
        "maintenance": {"protein": 0.20, "fat": 0.30, "carbs": 0.50},
        "weight_gain": {"protein": 0.20, "fat": 0.25, "carbs": 0.55},
        "muscle_gain": {"protein": 0.30, "fat": 0.25, "carbs": 0.45}
    }
    ratios = macro_ratios.get(goal.lower(), macro_ratios["maintenance"])

    protein_g = round((adjusted_TDEE * ratios["protein"]) / 4, 1)
    fat_g = round((adjusted_TDEE * ratios["fat"]) / 9, 1)
    carbs_g = round((adjusted_TDEE * ratios["carbs"]) / 4, 1)

    macros_target = {
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g
    }

    micros_target = {
        "iron_mg": 18 if gender.lower() == "female" else 8,
        "calcium_mg": 1000,
        "vitaminC_mg": 75 if gender.lower() == "female" else 90,
        "fiber_g": 30
    }

    weekly_actual = {}
    for nutrient in weekly_nutrition_summary.average_daily_nutrients:
        name_map = {
            "protein": "protein_g",
            "fat": "fat_g",
            "carbohydrates": "carbs_g",
            "carbs": "carbs_g",
            "iron": "iron_mg",
            "calcium": "calcium_mg",
            "vitamin c": "vitaminC_mg",
            "vitaminc": "vitaminC_mg",
            "fiber": "fiber_g"
        }
        normalized_name = name_map.get(nutrient.name.lower(), nutrient.name.lower())
        weekly_actual[normalized_name] = round(nutrient.amt, 1)

    nutrient_gaps = {}
    for macro in ["protein_g", "fat_g", "carbs_g"]:
        target = macros_target[macro]
        actual = weekly_actual.get(macro, 0)
        nutrient_gaps[macro] = round(target - actual, 1)

    for micro, target in micros_target.items():
        actual = weekly_actual.get(micro, 0)
        nutrient_gaps[micro] = round(target - actual, 1)

    patterns = _compute_variability_patterns(weekly_nutrition_summary)

    return {
        "TDEE": round(adjusted_TDEE, 0),
        "macros_target": macros_target,
        "micros_target": micros_target,
        "weekly_actual": weekly_actual,
        "nutrient_gaps": nutrient_gaps,
        "patterns": patterns,
        "goal": goal
    }