"""
DataExtractor.py - Module 1 of Habit Analysis Pipeline

This module is responsible for bridging your database (Firestore + local engine functions)
with the analysis layer. Think of it as your data gateway — a clean, normalized interface
between raw stored data and the rest of the pipeline.

Primary Goal:
    To fetch and standardize user-level nutrition and engagement data over time — directly
    from the backend's internal functions (Core.Nutrition.Storage, Core.Nutrition.WaterLog).

Responsibilities:
    - Data Retrieval: Fetches meals, water logs, and aggregates for a user
    - Normalization: Converts nested structures into simple dicts with scalar values per day
    - Data Continuity: Ensures all dates in range exist — fills missing ones with zeros or nulls
    - Temporal Ordering: Outputs results sorted by date
    - Logging: Warns if any sub-fetch fails but does not break pipeline

Tracked Nutrients:
    - protein (g)
    - fiber (g)
    - iron (g)
    - vitamin_d (mcg)
    - omega_3 (g)
    - omega_3_epa (g)
    - omega_3_dha (g)
"""

from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional
import logging

from Core.Nutrition.Storage import (
    get_meals_by_date_range,
    get_all_meals,
    NutrientAnalysis,
    Meal,
)
from Core.Nutrition.WaterLog import (
    get_water_logs_by_date_range,
    get_all_water_logs,
    get_daily_water_summary,
    WaterLog,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataExtractor:
    """
    Handles data retrieval and normalization from backend sources for habit analysis.
    Uses Core.Nutrition modules directly to access Firestore data.
    """

    def __init__(self, user_id: str):
        """
        Initialize the DataExtractor for a specific user.

        Args:
            user_id (str): Unique user identifier (Firestore document ID).
        """
        self.user_id = user_id
        logger.info(f"DataExtractor initialized for user: {user_id}")

    async def fetch_daily_nutrition(self, target_date: date) -> Dict:
        """
        Fetches nutrient totals for a single date by aggregating all meals.

        Args:
            target_date (date): The date to fetch nutrition data for.

        Returns:
            Dict: Normalized dictionary with date and nutrient values.
                  Example:
                  {
                      "date": "2026-01-11",
                      "protein_g": 45.5,
                      "fiber_g": 12.3,
                      "iron_g": 0.015,
                      "vitamin_d_mcg": 8.5,
                      "omega_3_g": 2.1,
                      "omega_3_epa_g": 0.8,
                      "omega_3_dha_g": 1.2,
                      "meal_count": 3,
                      "total_amount_g": 850.0
                  }
        """
        try:
            # Get start and end of the target day (UTC)
            start_of_day = datetime(
                target_date.year, target_date.month, target_date.day,
                0, 0, 0,
                tzinfo=timezone.utc
            )
            end_of_day = datetime(
                target_date.year, target_date.month, target_date.day,
                23, 59, 59, 999999,
                tzinfo=timezone.utc
            )

            # Fetch all meals for this day
            meals = await get_meals_by_date_range(self.user_id, start_of_day, end_of_day)

            # Initialize result with date
            result = {
                "date": target_date.isoformat(),
                "protein_g": 0.0,
                "fiber_g": 0.0,
                "iron_g": 0.0,
                "vitamin_d_mcg": 0.0,
                "omega_3_g": 0.0,
                "omega_3_epa_g": 0.0,
                "omega_3_dha_g": 0.0,
                "meal_count": 0,
                "total_amount_g": 0.0,
            }

            # Aggregate nutrients from all meals
            for meal in meals:
                result["protein_g"] += meal.analysis.protein
                result["fiber_g"] += meal.analysis.fiber
                result["iron_g"] += meal.analysis.iron
                result["vitamin_d_mcg"] += meal.analysis.vitamin_d
                result["omega_3_g"] += meal.analysis.omega_3
                result["omega_3_epa_g"] += meal.analysis.omega_3_epa
                result["omega_3_dha_g"] += meal.analysis.omega_3_dha
                result["total_amount_g"] += meal.amnt
                result["meal_count"] += 1

            return result

        except Exception as e:
            logger.warning(f"Failed to fetch daily nutrition for {target_date}: {e}")
            return self._create_empty_nutrition_record(target_date)

    async def fetch_daily_water(self, target_date: date, goal_ml: float = 2500.0) -> Dict:
        """
        Fetches water intake data for a single date.

        Args:
            target_date (date): The date to fetch water data for.
            goal_ml (float): Daily water intake goal in ml (default: 2500ml).

        Returns:
            Dict: Normalized dictionary with water intake data.
                  Example:
                  {
                      "date": "2026-01-11",
                      "water_intake_ml": 1800.0,
                      "water_log_count": 6,
                      "water_goal_ml": 2500.0,
                      "water_percentage": 72.0
                  }
        """
        try:
            # Get start and end of the target day (UTC)
            start_of_day = datetime(
                target_date.year, target_date.month, target_date.day,
                0, 0, 0,
                tzinfo=timezone.utc
            )
            end_of_day = datetime(
                target_date.year, target_date.month, target_date.day,
                23, 59, 59, 999999,
                tzinfo=timezone.utc
            )

            # Fetch all water logs for this day
            logs = await get_water_logs_by_date_range(self.user_id, start_of_day, end_of_day)

            # Calculate totals
            total_ml = sum(log.amount_ml for log in logs)
            log_count = len(logs)
            percentage = min((total_ml / goal_ml) * 100, 100.0) if goal_ml > 0 else 0.0

            return {
                "date": target_date.isoformat(),
                "water_intake_ml": total_ml,
                "water_log_count": log_count,
                "water_goal_ml": goal_ml,
                "water_percentage": round(percentage, 2),
            }

        except Exception as e:
            logger.warning(f"Failed to fetch daily water for {target_date}: {e}")
            return self._create_empty_water_record(target_date, goal_ml)

    async def fetch_weekly_nutrition_summary(
        self,
        end_date: Optional[date] = None
    ) -> Dict:
        """
        Fetches 7-day aggregate nutrition data ending on the specified date.
        This helps calculate averages, variability, and context-level stats.

        Args:
            end_date (Optional[date]): Reference end date for the week. Defaults to today.

        Returns:
            Dict: Weekly summary data.
                  Example:
                  {
                      "week_start": "2026-01-05",
                      "week_end": "2026-01-11",
                      "average_protein_g": 42.5,
                      "average_fiber_g": 15.2,
                      "average_iron_g": 0.012,
                      "average_vitamin_d_mcg": 6.8,
                      "average_omega_3_g": 1.5,
                      "total_meals": 18,
                      "days_tracked": 6,
                      "average_meals_per_day": 2.57
                  }
        """
        try:
            if end_date is None:
                end_date = date.today()

            start_date = end_date - timedelta(days=6)

            # Fetch daily nutrition for each day in the week
            daily_data = []
            for i in range(7):
                current_date = start_date + timedelta(days=i)
                day_nutrition = await self.fetch_daily_nutrition(current_date)
                daily_data.append(day_nutrition)

            # Calculate aggregates
            total_meals = sum(d["meal_count"] for d in daily_data)
            days_with_meals = sum(1 for d in daily_data if d["meal_count"] > 0)

            # Calculate averages (only for days with data)
            if days_with_meals > 0:
                avg_protein = sum(d["protein_g"] for d in daily_data) / days_with_meals
                avg_fiber = sum(d["fiber_g"] for d in daily_data) / days_with_meals
                avg_iron = sum(d["iron_g"] for d in daily_data) / days_with_meals
                avg_vitamin_d = sum(d["vitamin_d_mcg"] for d in daily_data) / days_with_meals
                avg_omega_3 = sum(d["omega_3_g"] for d in daily_data) / days_with_meals
            else:
                avg_protein = avg_fiber = avg_iron = avg_vitamin_d = avg_omega_3 = 0.0

            return {
                "week_start": start_date.isoformat(),
                "week_end": end_date.isoformat(),
                "average_protein_g": round(avg_protein, 2),
                "average_fiber_g": round(avg_fiber, 2),
                "average_iron_g": round(avg_iron, 4),
                "average_vitamin_d_mcg": round(avg_vitamin_d, 2),
                "average_omega_3_g": round(avg_omega_3, 2),
                "total_meals": total_meals,
                "days_tracked": days_with_meals,
                "average_meals_per_day": round(total_meals / 7, 2),
            }

        except Exception as e:
            logger.warning(f"Failed to fetch weekly summary: {e}")
            return {
                "week_start": None,
                "week_end": None,
                "average_protein_g": 0.0,
                "average_fiber_g": 0.0,
                "average_iron_g": 0.0,
                "average_vitamin_d_mcg": 0.0,
                "average_omega_3_g": 0.0,
                "total_meals": 0,
                "days_tracked": 0,
                "average_meals_per_day": 0.0,
            }

    async def calculate_meal_streak(
        self,
        min_meals_per_day: int = 1,
        days_to_check: int = 30
    ) -> Dict:
        """
        Calculates the user's meal logging streak.

        Args:
            min_meals_per_day (int): Minimum meals to count as a "tracked" day. Default: 1.
            days_to_check (int): Number of days to look back. Default: 30.

        Returns:
            Dict: Streak data.
                  Example:
                  {
                      "current_streak": 4,
                      "longest_streak": 12,
                      "min_meals_per_day": 1,
                      "days_checked": 30
                  }
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_to_check - 1)

            # Fetch daily data for the range
            current_streak = 0
            longest_streak = 0
            temp_streak = 0

            for i in range(days_to_check):
                current_date = end_date - timedelta(days=i)
                day_data = await self.fetch_daily_nutrition(current_date)

                if day_data["meal_count"] >= min_meals_per_day:
                    temp_streak += 1
                    if i == 0 or current_streak > 0:
                        current_streak = temp_streak
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    if i == 0:
                        current_streak = 0
                    temp_streak = 0

            return {
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "min_meals_per_day": min_meals_per_day,
                "days_checked": days_to_check,
            }

        except Exception as e:
            logger.warning(f"Failed to calculate meal streak: {e}")
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "min_meals_per_day": min_meals_per_day,
                "days_checked": days_to_check,
            }

    async def calculate_water_streak(
        self,
        min_percentage: float = 50.0,
        days_to_check: int = 30,
        goal_ml: float = 2500.0
    ) -> Dict:
        """
        Calculates the user's water intake streak.

        Args:
            min_percentage (float): Minimum goal percentage to count as success. Default: 50%.
            days_to_check (int): Number of days to look back. Default: 30.
            goal_ml (float): Daily water goal in ml. Default: 2500ml.

        Returns:
            Dict: Water streak data.
                  Example:
                  {
                      "current_streak": 7,
                      "longest_streak": 14,
                      "min_percentage": 50.0,
                      "goal_ml": 2500.0,
                      "days_checked": 30
                  }
        """
        try:
            end_date = date.today()

            current_streak = 0
            longest_streak = 0
            temp_streak = 0

            for i in range(days_to_check):
                current_date = end_date - timedelta(days=i)
                day_data = await self.fetch_daily_water(current_date, goal_ml)

                if day_data["water_percentage"] >= min_percentage:
                    temp_streak += 1
                    if i == 0 or current_streak > 0:
                        current_streak = temp_streak
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    if i == 0:
                        current_streak = 0
                    temp_streak = 0

            return {
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "min_percentage": min_percentage,
                "goal_ml": goal_ml,
                "days_checked": days_to_check,
            }

        except Exception as e:
            logger.warning(f"Failed to calculate water streak: {e}")
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "min_percentage": min_percentage,
                "goal_ml": goal_ml,
                "days_checked": days_to_check,
            }

    async def fetch_engagement(
        self,
        days: int = 60,
        end_date: Optional[date] = None,
        water_goal_ml: float = 2500.0
    ) -> List[Dict]:
        """
        Fetches daily engagement metrics (meal count, water intake, intensity scores).

        Args:
            days (int): Number of days to look back. Default 60.
            end_date (Optional[date]): End date for the range. Default today.
            water_goal_ml (float): Daily water goal for percentage calculation.

        Returns:
            List[Dict]: Daily engagement data with all gaps filled.
                        Example:
                        [
                            {
                                "date": "2026-01-11",
                                "meal_count": 3,
                                "meal_intensity": 2,
                                "water_intake_ml": 2100.0,
                                "water_intensity": 3,
                                "combined_intensity": 6,
                                "water_percentage": 84.0
                            },
                            ...
                        ]
        """
        try:
            if end_date is None:
                end_date = date.today()

            start_date = end_date - timedelta(days=days - 1)
            all_dates = self._get_date_range(start_date, end_date)

            # Build engagement data for each day
            engagement_data = []

            for current_date in all_dates:
                # Fetch nutrition and water data
                nutrition = await self.fetch_daily_nutrition(current_date)
                water = await self.fetch_daily_water(current_date, water_goal_ml)

                # Calculate intensity scores (0-4 scale)
                meal_intensity = self._calculate_meal_intensity(nutrition["meal_count"])
                water_intensity = self._calculate_water_intensity(water["water_percentage"])
                combined_intensity = meal_intensity + water_intensity

                engagement_data.append({
                    "date": current_date.isoformat(),
                    "meal_count": nutrition["meal_count"],
                    "meal_intensity": meal_intensity,
                    "water_intake_ml": water["water_intake_ml"],
                    "water_intensity": water_intensity,
                    "combined_intensity": combined_intensity,
                    "water_percentage": water["water_percentage"],
                })

            return engagement_data

        except Exception as e:
            logger.warning(f"Failed to fetch engagement data: {e}")
            return []

    async def build_raw_data(
        self,
        start_date: date,
        end_date: date,
        water_goal_ml: float = 2500.0
    ) -> List[Dict]:
        """
        Combines all data sources to create a unified, gap-free daily dataset
        ready for feature engineering.

        Flow:
            1. For each day in range:
               - fetch_daily_nutrition() → get nutrient totals
               - fetch_daily_water() → get water intake
            2. Calculate streaks
            3. Merge all data sources
            4. Return list sorted by date

        Args:
            start_date (date): Start of the date range.
            end_date (date): End of the date range.
            water_goal_ml (float): Daily water goal in ml.

        Returns:
            List[Dict]: Unified daily-level dataset.
                        Example:
                        [
                            {
                                "date": "2026-01-11",
                                "protein_g": 45.5,
                                "fiber_g": 12.3,
                                "iron_g": 0.015,
                                "vitamin_d_mcg": 8.5,
                                "omega_3_g": 2.1,
                                "omega_3_epa_g": 0.8,
                                "omega_3_dha_g": 1.2,
                                "meal_count": 3,
                                "total_amount_g": 850.0,
                                "water_intake_ml": 1800.0,
                                "water_percentage": 72.0,
                                "meal_intensity": 2,
                                "water_intensity": 2,
                                "combined_intensity": 4,
                                "current_meal_streak": 5,
                                "longest_meal_streak": 12,
                                "current_water_streak": 3,
                                "longest_water_streak": 8
                            },
                            ...
                        ]
        """
        logger.info(f"Building raw data from {start_date} to {end_date}")

        # Calculate streaks (global for the user)
        meal_streak = await self.calculate_meal_streak()
        water_streak = await self.calculate_water_streak(goal_ml=water_goal_ml)

        # Get all dates in range
        all_dates = self._get_date_range(start_date, end_date)

        raw_data = []

        for current_date in all_dates:
            # Fetch nutrition and water data for this day
            nutrition = await self.fetch_daily_nutrition(current_date)
            water = await self.fetch_daily_water(current_date, water_goal_ml)

            # Calculate intensity scores
            meal_intensity = self._calculate_meal_intensity(nutrition["meal_count"])
            water_intensity = self._calculate_water_intensity(water["water_percentage"])

            # Merge all data sources
            merged_record = {
                "date": current_date.isoformat(),
                # Nutrition data
                "protein_g": nutrition["protein_g"],
                "fiber_g": nutrition["fiber_g"],
                "iron_g": nutrition["iron_g"],
                "vitamin_d_mcg": nutrition["vitamin_d_mcg"],
                "omega_3_g": nutrition["omega_3_g"],
                "omega_3_epa_g": nutrition["omega_3_epa_g"],
                "omega_3_dha_g": nutrition["omega_3_dha_g"],
                "meal_count": nutrition["meal_count"],
                "total_amount_g": nutrition["total_amount_g"],
                # Water data
                "water_intake_ml": water["water_intake_ml"],
                "water_log_count": water["water_log_count"],
                "water_percentage": water["water_percentage"],
                # Intensity scores
                "meal_intensity": meal_intensity,
                "water_intensity": water_intensity,
                "combined_intensity": meal_intensity + water_intensity,
                # Streak data (global)
                "current_meal_streak": meal_streak["current_streak"],
                "longest_meal_streak": meal_streak["longest_streak"],
                "current_water_streak": water_streak["current_streak"],
                "longest_water_streak": water_streak["longest_streak"],
            }

            raw_data.append(merged_record)

        logger.info(f"Successfully built {len(raw_data)} days of raw data")
        return raw_data

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_date_range(self, start_date: date, end_date: date) -> List[date]:
        """
        Generate a continuous daily range.

        Args:
            start_date (date): Start of the range (inclusive).
            end_date (date): End of the range (inclusive).

        Returns:
            List[date]: List of dates in chronological order.
        """
        delta = end_date - start_date
        return [start_date + timedelta(days=i) for i in range(delta.days + 1)]

    def _calculate_meal_intensity(self, meal_count: int) -> int:
        """
        Calculate meal logging intensity on a 0-4 scale.

        Args:
            meal_count (int): Number of meals logged.

        Returns:
            int: Intensity score (0-4).
        """
        if meal_count == 0:
            return 0
        elif meal_count == 1:
            return 1
        elif meal_count == 2:
            return 2
        elif meal_count == 3:
            return 3
        else:
            return 4  # 4+ meals

    def _calculate_water_intensity(self, percentage: float) -> int:
        """
        Calculate water intake intensity on a 0-4 scale.

        Args:
            percentage (float): Percentage of water goal achieved.

        Returns:
            int: Intensity score (0-4).
        """
        if percentage < 25:
            return 0
        elif percentage < 50:
            return 1
        elif percentage < 75:
            return 2
        elif percentage < 100:
            return 3
        else:
            return 4  # 100%+ of goal

    def _create_empty_nutrition_record(self, target_date: date) -> Dict:
        """
        Create a zero-filled nutrition record for a missing day.

        Args:
            target_date (date): The date for the record.

        Returns:
            Dict: Zero-filled nutrition record.
        """
        return {
            "date": target_date.isoformat(),
            "protein_g": 0.0,
            "fiber_g": 0.0,
            "iron_g": 0.0,
            "vitamin_d_mcg": 0.0,
            "omega_3_g": 0.0,
            "omega_3_epa_g": 0.0,
            "omega_3_dha_g": 0.0,
            "meal_count": 0,
            "total_amount_g": 0.0,
        }

    def _create_empty_water_record(self, target_date: date, goal_ml: float = 2500.0) -> Dict:
        """
        Create a zero-filled water record for a missing day.

        Args:
            target_date (date): The date for the record.
            goal_ml (float): Daily water goal in ml.

        Returns:
            Dict: Zero-filled water record.
        """
        return {
            "date": target_date.isoformat(),
            "water_intake_ml": 0.0,
            "water_log_count": 0,
            "water_goal_ml": goal_ml,
            "water_percentage": 0.0,
        }


# =============================================================================
# Example usage and testing
# =============================================================================

async def test_extractor():
    """Test function to demonstrate DataExtractor usage."""
    from datetime import date, timedelta

    # Initialize with a test user ID
    user_id = "MbG3wwDSH1o5lqQYoFG1"
    extractor = DataExtractor(user_id)

    # Define date range (last 7 days)
    end = date.today()
    start = end - timedelta(days=6)

    print("\n" + "=" * 80)
    print("DATA EXTRACTOR - TEST RUN")
    print("=" * 80)
    print(f"User: {user_id}")
    print(f"Date Range: {start} to {end}")
    print("=" * 80 + "\n")

    # Test 1: Fetch daily nutrition
    print("[TEST 1] Fetching daily nutrition for today...")
    daily_nutrition = await extractor.fetch_daily_nutrition(date.today())
    print(f"✓ Retrieved {len(daily_nutrition)} fields")
    print(f"  Meals: {daily_nutrition.get('meal_count', 0)}")
    print(f"  Protein: {daily_nutrition.get('protein_g', 0)}g")
    print(f"  Fiber: {daily_nutrition.get('fiber_g', 0)}g\n")

    # Test 2: Fetch daily water
    print("[TEST 2] Fetching daily water for today...")
    daily_water = await extractor.fetch_daily_water(date.today())
    print(f"✓ Water intake: {daily_water.get('water_intake_ml', 0)}ml")
    print(f"  Goal progress: {daily_water.get('water_percentage', 0)}%\n")

    # Test 3: Fetch weekly summary
    print("[TEST 3] Fetching weekly nutrition summary...")
    weekly_summary = await extractor.fetch_weekly_nutrition_summary()
    print(f"✓ Week: {weekly_summary.get('week_start')} to {weekly_summary.get('week_end')}")
    print(f"  Days tracked: {weekly_summary.get('days_tracked')}")
    print(f"  Total meals: {weekly_summary.get('total_meals')}")
    print(f"  Avg protein: {weekly_summary.get('average_protein_g')}g\n")

    # Test 4: Calculate meal streak
    print("[TEST 4] Calculating meal streak...")
    meal_streak = await extractor.calculate_meal_streak()
    print(f"✓ Current streak: {meal_streak.get('current_streak')} days")
    print(f"  Longest streak: {meal_streak.get('longest_streak')} days\n")

    # Test 5: Calculate water streak
    print("[TEST 5] Calculating water streak...")
    water_streak = await extractor.calculate_water_streak()
    print(f"✓ Current streak: {water_streak.get('current_streak')} days")
    print(f"  Longest streak: {water_streak.get('longest_streak')} days\n")

    # Test 6: Fetch engagement data
    print("[TEST 6] Fetching engagement data (7 days)...")
    engagement = await extractor.fetch_engagement(days=7)
    print(f"✓ Retrieved {len(engagement)} days of engagement data")
    if engagement:
        latest = engagement[-1]
        print(f"  Latest day: meal_intensity={latest['meal_intensity']}, "
              f"water_intensity={latest['water_intensity']}\n")

    # Test 7: Build complete raw data
    print("[TEST 7] Building complete raw dataset (7 days)...")
    raw_data = await extractor.build_raw_data(start, end)
    print(f"✓ Successfully built {len(raw_data)} days of unified data")

    if raw_data:
        print("\n[PREVIEW] Latest record:")
        record = raw_data[-1]
        for key, value in record.items():
            print(f"    {key}: {value}")

    print("\n" + "=" * 80)
    print("DATA EXTRACTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_extractor())