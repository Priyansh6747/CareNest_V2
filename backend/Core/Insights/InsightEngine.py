"""
InsightEngine.py - Main Pregnancy Nutrition Insights Orchestrator

This module is the primary entry point for generating comprehensive nutrition
insights for pregnant women. It orchestrates:
    - Historical data extraction
    - Time-series forecasting with Chronos-Bolt via AutoGluon (CPU-friendly)
    - Nutrient gap analysis
    - Actionable recommendations

Module-level Export:
    get_pregnancy_insights() - Main function to get complete insights

Dependencies:
    - autogluon: pip install autogluon (recommended for Chronos-Bolt)
    - pandas: For data manipulation
    - numpy: For numerical operations
"""

from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local imports
from Core.Insights.DataExtractor import DataExtractor
from Core.Insights.FeatureBuilder import FeatureBuilder
from Core.Insights.DietAnalysis import (
    compute_pregnancy_needs,
    get_pregnancy_rda,
    PREGNANCY_RDA,
)


# =============================================================================
# AutoGluon-based Chronos Forecaster (Production Recommended)
# =============================================================================

class ChronosForecaster:
    """
    Production-ready Chronos-Bolt forecaster using AutoGluon.
    
    AutoGluon provides:
        - Zero-shot inference with Chronos-Bolt
        - Optional fine-tuning and covariate support
        - Ensembling with other models for maximum accuracy
        - CPU-friendly inference
    
    Install: pip install autogluon
    """
    
    def __init__(self, model_path: str = "amazon/chronos-bolt-mini"):
        """
        Initialize the AutoGluon Chronos forecaster.
        
        Args:
            model_path: HuggingFace model path for Chronos-Bolt
        """
        self.model_path = model_path
        self.predictor = None
        self._is_available = None
        self._pd = None
        
        logger.info(f"ChronosForecaster initialized with model: {model_path}")
    
    def _check_availability(self) -> bool:
        """Check if AutoGluon TimeSeries is available."""
        if self._is_available is not None:
            return self._is_available
        
        try:
            from autogluon.timeseries import TimeSeriesPredictor, TimeSeriesDataFrame
            import pandas as pd
            self._pd = pd
            self._is_available = True
            logger.info("AutoGluon TimeSeries is available")
        except ImportError as e:
            logger.warning(f"AutoGluon not available: {e}")
            logger.warning("Install with: pip install autogluon")
            self._is_available = False
        
        return self._is_available
    
    def _prepare_dataframe(
        self,
        context: List[float],
        item_id: str = "nutrient"
    ):
        """
        Convert context list to AutoGluon TimeSeriesDataFrame format.
        
        Args:
            context: Historical values
            item_id: Identifier for this time series
        
        Returns:
            TimeSeriesDataFrame ready for prediction
        """
        from autogluon.timeseries import TimeSeriesDataFrame
        
        # Create date range ending today
        end_date = date.today()
        start_date = end_date - timedelta(days=len(context) - 1)
        dates = [start_date + timedelta(days=i) for i in range(len(context))]
        
        # Build DataFrame in AutoGluon format
        df = self._pd.DataFrame({
            "item_id": [item_id] * len(context),
            "timestamp": dates,
            "target": context
        })
        
        return TimeSeriesDataFrame.from_data_frame(df)
    
    def forecast_single(
        self,
        context: List[float],
        prediction_length: int = 7
    ) -> Optional[np.ndarray]:
        """
        Generate forecast for a single time series using Chronos-Bolt.
        
        Args:
            context: Historical values (at least 10 data points recommended)
            prediction_length: Number of future steps to predict
        
        Returns:
            Numpy array of mean forecasts, or None if failed
        """
        if not self._check_availability():
            return None
        
        if len(context) < 3:
            logger.warning("Insufficient context for forecasting")
            return None
        
        try:
            from autogluon.timeseries import TimeSeriesPredictor
            
            # Prepare data
            ts_df = self._prepare_dataframe(context)
            
            # Create predictor with Chronos-Bolt
            # Using a temporary directory for the predictor
            import tempfile
            with tempfile.TemporaryDirectory() as tmp_dir:
                predictor = TimeSeriesPredictor(
                    prediction_length=prediction_length,
                    path=tmp_dir,
                    verbosity=0  # Suppress output
                )
                
                # Fit with zero-shot Chronos (no actual training, just loads model)
                predictor.fit(
                    ts_df,
                    hyperparameters={
                        "Chronos": {"model_path": self.model_path},
                    },
                    time_limit=60,  # Limit for safety
                    enable_ensemble=False  # Single model for speed
                )
                
                # Generate predictions
                predictions = predictor.predict(ts_df)
                
                # Extract mean forecast values
                forecast_values = predictions["mean"].values
                
                return forecast_values.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Chronos forecast failed: {e}")
            return None
    
    def forecast_batch(
        self,
        contexts: List[List[float]],
        prediction_length: int = 7
    ) -> List[Optional[np.ndarray]]:
        """
        Generate forecasts for multiple time series.
        
        For efficiency, combines all series into one TimeSeriesDataFrame.
        
        Args:
            contexts: List of historical value lists
            prediction_length: Number of future steps to predict
        
        Returns:
            List of numpy arrays (or None for failed forecasts)
        """
        if not self._check_availability():
            return [None] * len(contexts)
        
        try:
            from autogluon.timeseries import TimeSeriesPredictor, TimeSeriesDataFrame
            
            # Build combined DataFrame
            all_rows = []
            end_date = date.today()
            
            for idx, context in enumerate(contexts):
                if len(context) < 3:
                    continue
                    
                start_date = end_date - timedelta(days=len(context) - 1)
                dates = [start_date + timedelta(days=i) for i in range(len(context))]
                
                for i, val in enumerate(context):
                    all_rows.append({
                        "item_id": f"series_{idx}",
                        "timestamp": dates[i],
                        "target": val
                    })
            
            if not all_rows:
                return [None] * len(contexts)
            
            df = self._pd.DataFrame(all_rows)
            ts_df = TimeSeriesDataFrame.from_data_frame(df)
            
            # Predict
            import tempfile
            with tempfile.TemporaryDirectory() as tmp_dir:
                predictor = TimeSeriesPredictor(
                    prediction_length=prediction_length,
                    path=tmp_dir,
                    verbosity=0
                )
                
                predictor.fit(
                    ts_df,
                    hyperparameters={
                        "Chronos": {"model_path": self.model_path},
                    },
                    time_limit=120,
                    enable_ensemble=False
                )
                
                predictions = predictor.predict(ts_df)
                
                # Extract results per series
                results = []
                for idx in range(len(contexts)):
                    item_id = f"series_{idx}"
                    if item_id in predictions.index.get_level_values("item_id"):
                        series_preds = predictions.loc[item_id]["mean"].values
                        results.append(series_preds.astype(np.float32))
                    else:
                        results.append(None)
                
                return results
            
        except Exception as e:
            logger.error(f"Batch forecast failed: {e}")
            return [None] * len(contexts)


# =============================================================================
# Fallback Forecaster (when Chronos is not available)
# =============================================================================

class SimpleForecaster:
    """
    Simple fallback forecaster using moving averages.
    Used when Chronos is not available.
    """
    
    def __init__(self, window: int = 7):
        self.window = window
        logger.info("Using SimpleForecaster (Chronos not available)")
    
    def forecast_single(
        self,
        context: List[float],
        prediction_length: int = 7
    ) -> np.ndarray:
        """
        Simple forecast using exponential moving average.
        """
        if len(context) < 3:
            # Not enough data, return last value or 0
            last_val = context[-1] if context else 0.0
            return np.full(prediction_length, last_val)
        
        # Calculate exponential moving average
        alpha = 2.0 / (self.window + 1)
        ema = context[0]
        for val in context[1:]:
            ema = alpha * val + (1 - alpha) * ema
        
        # Calculate trend
        recent = context[-min(self.window, len(context)):]
        if len(recent) >= 2:
            trend = (recent[-1] - recent[0]) / len(recent)
        else:
            trend = 0.0
        
        # Generate forecast with slight trend decay
        forecasts = []
        for i in range(prediction_length):
            forecast_val = ema + trend * (i + 1) * 0.8  # Decay trend
            forecasts.append(max(0, forecast_val))  # Non-negative values
        
        return np.array(forecasts)
    
    def forecast_batch(
        self,
        contexts: List[List[float]],
        prediction_length: int = 7
    ) -> List[np.ndarray]:
        """Batch forecasting."""
        return [self.forecast_single(ctx, prediction_length) for ctx in contexts]


# =============================================================================
# Main Insight Engine
# =============================================================================

class InsightEngine:
    """
    Main orchestrator for pregnancy nutrition insights.
    
    Combines:
        - Historical data from DataExtractor
        - Feature engineering from FeatureBuilder
        - Time-series forecasting (Chronos-Bolt-Mini or fallback)
        - Pregnancy-specific RDA analysis from DietAnalysis
    """
    
    # Nutrients we track and forecast
    TRACKED_NUTRIENTS = [
        "protein_g",
        "fiber_g",
        "iron_g",          # Note: stored as g, RDA is in mg
        "vitamin_d_mcg",
        "omega_3_g",
        "omega_3_epa_g",
        "omega_3_dha_g",
    ]
    
    def __init__(
        self,
        user_id: str,
        use_chronos: bool = True
    ):
        """
        Initialize the Insight Engine.
        
        Args:
            user_id: User's Firebase UID
            use_chronos: Whether to attempt using Chronos (falls back to simple if unavailable)
        """
        self.user_id = user_id
        self.extractor = DataExtractor(user_id)
        self.feature_builder = FeatureBuilder(normalize=False, window_days=7)
        
        # Initialize forecaster
        if use_chronos:
            self.forecaster = ChronosForecaster()
            # Check if Chronos is available, fallback if not
            if not self.forecaster._check_availability():
                logger.info("Falling back to SimpleForecaster")
                self.forecaster = SimpleForecaster()
        else:
            self.forecaster = SimpleForecaster()
        
        logger.info(f"InsightEngine initialized for user: {user_id}")
    
    async def _fetch_historical_data(
        self,
        context_days: int = 30
    ) -> List[Dict]:
        """Fetch historical nutrition data."""
        end_date = date.today()
        start_date = end_date - timedelta(days=context_days - 1)
        
        logger.info(f"Fetching data from {start_date} to {end_date}")
        raw_data = await self.extractor.build_raw_data(start_date, end_date)
        
        return raw_data
    
    def _extract_nutrient_timeseries(
        self,
        raw_data: List[Dict],
        nutrient: str
    ) -> List[float]:
        """Extract a single nutrient's time series from raw data."""
        return [day.get(nutrient, 0.0) for day in raw_data]
    
    def _generate_forecast_dates(
        self,
        prediction_length: int
    ) -> List[str]:
        """Generate list of forecast date strings."""
        start = date.today() + timedelta(days=1)
        return [(start + timedelta(days=i)).isoformat() for i in range(prediction_length)]
    
    def _determine_trend(self, values: np.ndarray) -> str:
        """Determine if trend is increasing, decreasing, or stable."""
        if len(values) < 2:
            return "stable"
        
        first_half = np.mean(values[:len(values)//2]) if len(values) > 1 else values[0]
        second_half = np.mean(values[len(values)//2:]) if len(values) > 1 else values[-1]
        
        diff_pct = (second_half - first_half) / (first_half + 1e-8) * 100
        
        if diff_pct > 10:
            return "increasing"
        elif diff_pct < -10:
            return "decreasing"
        else:
            return "stable"
    
    async def generate_insights(
        self,
        trimester: str,
        age: int,
        height_cm: float,
        weight_kg: float,
        activity_factor: float = 1.4,
        forecast_days: int = 7,
        context_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive nutrition insights.
        
        Args:
            trimester: Current pregnancy stage
            age: Mother's age in years
            height_cm: Height in cm
            weight_kg: Current weight in kg
            activity_factor: Activity level multiplier
            forecast_days: Days to forecast ahead
            context_days: Historical days to analyze
        
        Returns:
            Complete insights dictionary
        """
        logger.info(f"Generating insights for trimester: {trimester}")
        
        # Step 1: Fetch historical data
        raw_data = await self._fetch_historical_data(context_days)
        
        if not raw_data:
            logger.warning("No historical data available")
            return self._create_empty_insights(trimester, age)
        
        # Step 2: Calculate current nutrient status
        today_data = raw_data[-1] if raw_data else {}
        week_data = raw_data[-7:] if len(raw_data) >= 7 else raw_data
        
        # Calculate weekly averages
        weekly_avg = {}
        for nutrient in self.TRACKED_NUTRIENTS:
            values = [day.get(nutrient, 0) for day in week_data]
            weekly_avg[nutrient] = sum(values) / len(values) if values else 0
        
        # Step 3: Generate forecasts for each nutrient
        forecasts = {}
        forecast_dates = self._generate_forecast_dates(forecast_days)
        
        for nutrient in self.TRACKED_NUTRIENTS:
            timeseries = self._extract_nutrient_timeseries(raw_data, nutrient)
            
            if len(timeseries) < 3:
                # Not enough data for forecasting
                logger.warning(f"Insufficient data for forecasting {nutrient}")
                forecasts[nutrient] = {
                    "values": [weekly_avg.get(nutrient, 0)] * forecast_days,
                    "dates": forecast_dates,
                    "trend": "unknown"
                }
                continue
            
            forecast_values = self.forecaster.forecast_single(timeseries, forecast_days)
            
            if forecast_values is not None:
                # Ensure non-negative values
                forecast_values = np.maximum(forecast_values, 0)
                forecasts[nutrient] = {
                    "values": forecast_values.tolist(),
                    "dates": forecast_dates,
                    "trend": self._determine_trend(forecast_values)
                }
            else:
                forecasts[nutrient] = {
                    "values": [weekly_avg.get(nutrient, 0)] * forecast_days,
                    "dates": forecast_dates,
                    "trend": "unknown"
                }
        
        # Step 4: Calculate RDA gaps
        current_nutrients = []
        for nutrient in self.TRACKED_NUTRIENTS:
            rda = get_pregnancy_rda(
                nutrient.replace("_g", "_mg") if "iron" in nutrient else nutrient,
                trimester,
                age
            )
            
            # Handle iron unit conversion (stored as g, RDA in mg)
            current_value = weekly_avg.get(nutrient, 0)
            if "iron" in nutrient and rda > 0:
                current_value_mg = current_value * 1000  # g to mg
                gap = rda - current_value_mg
                pct = (current_value_mg / rda) * 100 if rda > 0 else 0
                current_nutrients.append({
                    "name": nutrient,
                    "current_intake": round(current_value_mg, 2),
                    "recommended": rda,
                    "unit": "mg",
                    "gap": round(gap, 2),
                    "percentage_met": round(min(pct, 200), 1)
                })
            else:
                unit = "mcg" if "mcg" in nutrient else "g"
                gap = rda - current_value
                pct = (current_value / rda) * 100 if rda > 0 else 0
                current_nutrients.append({
                    "name": nutrient,
                    "current_intake": round(current_value, 2),
                    "recommended": rda,
                    "unit": unit,
                    "gap": round(gap, 2),
                    "percentage_met": round(min(pct, 200), 1)
                })
        
        # Step 5: Identify priority nutrients
        priority = sorted(
            [n for n in current_nutrients if n["gap"] > 0],
            key=lambda x: x["gap"] / (x["recommended"] + 1e-8),
            reverse=True
        )[:3]
        priority_names = [n["name"] for n in priority]
        
        # Step 6: Generate recommendations
        recommendations = self._generate_recommendations(priority_names, trimester)
        
        # Step 7: Calculate consistency score
        days_with_meals = sum(1 for day in raw_data if day.get("meal_count", 0) > 0)
        consistency_score = (days_with_meals / len(raw_data)) * 100 if raw_data else 0
        
        # Step 8: Get streak data
        meal_streak = await self.extractor.calculate_meal_streak()
        water_streak = await self.extractor.calculate_water_streak()
        
        # Compile final result
        result = {
            "user_id": self.user_id,
            "trimester": trimester,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            
            # Current status
            "current_nutrients": current_nutrients,
            "today_intake": {
                k: today_data.get(k, 0) for k in self.TRACKED_NUTRIENTS
            },
            
            # Forecasts
            "nutrient_forecasts": forecasts,
            "forecast_horizon_days": forecast_days,
            
            # Recommendations
            "priority_nutrients": priority_names,
            "dietary_recommendations": recommendations,
            
            # Trends and consistency
            "consistency_score": round(consistency_score, 1),
            "streak_data": {
                "meal_streak": meal_streak.get("current_streak", 0),
                "water_streak": water_streak.get("current_streak", 0),
                "longest_meal_streak": meal_streak.get("longest_streak", 0),
                "longest_water_streak": water_streak.get("longest_streak", 0),
            },
            
            # Water trends (new feature)
            "water_trends": await self._generate_water_trends(
                raw_data, week_data, today_data, forecast_days, forecast_dates
            ),
            
            # Metadata
            "context_days_used": len(raw_data),
            "forecaster_type": type(self.forecaster).__name__,
        }
        
        logger.info("Insights generation complete")
        return result
    
    async def _generate_water_trends(
        self,
        raw_data: List[Dict],
        week_data: List[Dict],
        today_data: Dict,
        forecast_days: int,
        forecast_dates: List[str],
        water_goal_ml: float = 2500.0
    ) -> Dict[str, Any]:
        """
        Generate comprehensive water intake trends and forecasts.
        
        Args:
            raw_data: All historical data
            week_data: Last 7 days of data
            today_data: Today's data
            forecast_days: Number of days to forecast
            forecast_dates: List of forecast date strings
            water_goal_ml: Daily water goal in ml (default: 2500ml for pregnancy)
        
        Returns:
            Water trends dictionary with:
                - current_intake_ml: Today's water intake
                - weekly_average_ml: 7-day average
                - goal_ml: Daily target
                - goal_percentage: Progress toward goal
                - hydration_status: "excellent", "good", "fair", "needs_improvement"
                - forecast: Predicted intake for next days
                - trend: Overall trend direction
                - recommendations: Hydration tips
        """
        # Current and weekly stats
        today_water = today_data.get("water_intake_ml", 0)
        weekly_water = [day.get("water_intake_ml", 0) for day in week_data]
        weekly_avg = sum(weekly_water) / len(weekly_water) if weekly_water else 0
        
        # Goal progress
        goal_percentage = (today_water / water_goal_ml) * 100 if water_goal_ml > 0 else 0
        weekly_goal_pct = (weekly_avg / water_goal_ml) * 100 if water_goal_ml > 0 else 0
        
        # Determine hydration status
        if weekly_goal_pct >= 90:
            hydration_status = "excellent"
        elif weekly_goal_pct >= 70:
            hydration_status = "good"
        elif weekly_goal_pct >= 50:
            hydration_status = "fair"
        else:
            hydration_status = "needs_improvement"
        
        # Generate water forecast
        water_timeseries = [day.get("water_intake_ml", 0) for day in raw_data]
        
        if len(water_timeseries) >= 3:
            forecast_values = self.forecaster.forecast_single(water_timeseries, forecast_days)
            if forecast_values is not None:
                forecast_values = np.maximum(forecast_values, 0)
                water_forecast = {
                    "values": forecast_values.tolist(),
                    "dates": forecast_dates,
                    "trend": self._determine_trend(forecast_values),
                    "predicted_avg_ml": round(float(np.mean(forecast_values)), 1)
                }
            else:
                water_forecast = {
                    "values": [weekly_avg] * forecast_days,
                    "dates": forecast_dates,
                    "trend": "stable",
                    "predicted_avg_ml": round(weekly_avg, 1)
                }
        else:
            water_forecast = {
                "values": [weekly_avg] * forecast_days,
                "dates": forecast_dates,
                "trend": "unknown",
                "predicted_avg_ml": round(weekly_avg, 1)
            }
        
        # Days meeting goal in the past week
        days_meeting_goal = sum(1 for w in weekly_water if w >= water_goal_ml * 0.8)
        
        # Hydration recommendations
        hydration_tips = []
        if hydration_status == "needs_improvement":
            hydration_tips.append("Set reminders to drink water every 2 hours")
            hydration_tips.append("Keep a water bottle with you at all times")
        elif hydration_status == "fair":
            hydration_tips.append("Try to add one more glass of water per day")
        
        if weekly_avg < 2000:
            hydration_tips.append("Proper hydration is crucial during pregnancy - aim for 2.5L daily")
        
        # Water consistency score
        water_consistency = (days_meeting_goal / len(week_data)) * 100 if week_data else 0
        
        return {
            "current_intake_ml": round(today_water, 1),
            "weekly_average_ml": round(weekly_avg, 1),
            "goal_ml": water_goal_ml,
            "today_goal_percentage": round(min(goal_percentage, 200), 1),
            "weekly_goal_percentage": round(min(weekly_goal_pct, 200), 1),
            "hydration_status": hydration_status,
            "days_meeting_goal": days_meeting_goal,
            "water_consistency_score": round(water_consistency, 1),
            "forecast": water_forecast,
            "recommendations": hydration_tips
        }
    
    def _generate_recommendations(
        self,
        priority_nutrients: List[str],
        trimester: str
    ) -> List[str]:
        """Generate dietary recommendations based on priority nutrients."""
        recommendations = []
        
        nutrient_foods = {
            "protein_g": "Include more lean meats, eggs, legumes, and dairy products",
            "fiber_g": "Add more whole grains, fruits, vegetables, and beans",
            "iron_g": "Eat iron-rich foods like spinach, lentils, and fortified cereals with vitamin C",
            "iron_mg": "Eat iron-rich foods like spinach, lentils, and fortified cereals with vitamin C",
            "vitamin_d_mcg": "Consider fortified milk, fatty fish, or safe sun exposure",
            "omega_3_g": "Include fatty fish (salmon, sardines), walnuts, or flaxseeds",
            "omega_3_epa_g": "Eat fatty fish twice a week or consider a fish oil supplement",
            "omega_3_dha_g": "Prioritize fatty fish or algae-based DHA supplements for fetal brain development",
            "calcium_mg": "Increase dairy products, fortified plant milks, or leafy greens",
            "folate_mcg": "Eat dark leafy greens, citrus fruits, and fortified grains",
        }
        
        for nutrient in priority_nutrients:
            if nutrient in nutrient_foods:
                recommendations.append(nutrient_foods[nutrient])
        
        # Trimester-specific advice
        if trimester == "trimester_1":
            recommendations.append("Focus on folate-rich foods to support neural tube development")
        elif trimester == "trimester_2":
            recommendations.append("Protein needs increase now - aim for 71g daily")
        elif trimester == "trimester_3":
            recommendations.append("DHA is crucial now for baby's brain development")
        elif trimester == "postpartum":
            recommendations.append("Maintain good nutrition to support recovery and lactation")
        
        return recommendations
    
    def _create_empty_insights(
        self,
        trimester: str,
        age: int
    ) -> Dict[str, Any]:
        """Create empty insights structure when no data available."""
        return {
            "user_id": self.user_id,
            "trimester": trimester,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "current_nutrients": [],
            "today_intake": {},
            "nutrient_forecasts": {},
            "forecast_horizon_days": 0,
            "priority_nutrients": [],
            "dietary_recommendations": [
                "Start logging your meals to get personalized nutrition insights",
            ],
            "consistency_score": 0.0,
            "streak_data": {
                "meal_streak": 0,
                "water_streak": 0,
                "longest_meal_streak": 0,
                "longest_water_streak": 0,
            },
            "water_trends": {
                "current_intake_ml": 0,
                "weekly_average_ml": 0,
                "goal_ml": 2500.0,
                "today_goal_percentage": 0,
                "weekly_goal_percentage": 0,
                "hydration_status": "needs_improvement",
                "days_meeting_goal": 0,
                "water_consistency_score": 0,
                "forecast": {"values": [], "dates": [], "trend": "unknown", "predicted_avg_ml": 0},
                "recommendations": ["Start logging water intake to track hydration"]
            },
            "context_days_used": 0,
            "forecaster_type": type(self.forecaster).__name__,
            "error": "No historical data available",
        }


# =============================================================================
# Module-Level Export Function
# =============================================================================

async def get_pregnancy_insights(
    user_id: str,
    trimester: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    activity_factor: float = 1.4,
    forecast_days: int = 7,
    context_days: int = 30,
    use_chronos: bool = True
) -> Dict[str, Any]:
    """
    Main module export function for pregnancy nutrition insights.
    
    This is the primary entry point for getting comprehensive nutrition
    insights for a pregnant user. It combines historical analysis,
    time-series forecasting, and pregnancy-specific RDA comparisons.
    
    Args:
        user_id: User's Firebase UID
        trimester: Current pregnancy stage
            - "trimester_1": First trimester (weeks 1-12)
            - "trimester_2": Second trimester (weeks 13-26)
            - "trimester_3": Third trimester (weeks 27-40)
            - "postpartum": After delivery
        age: Mother's age in years
        height_cm: Height in centimeters
        weight_kg: Current weight in kilograms
        activity_factor: Physical activity multiplier
            - 1.2: Sedentary (little or no exercise)
            - 1.4: Lightly active (light exercise 1-3 days/week) [default]
            - 1.6: Moderately active (moderate exercise 3-5 days/week)
            - 1.75: Very active (hard exercise 6-7 days/week)
        forecast_days: Number of days to forecast ahead (default: 7)
        context_days: Historical days to use for context (default: 30)
        use_chronos: Whether to use Chronos-Bolt-Mini for forecasting (default: True)
            Falls back to simple forecasting if Chronos is unavailable.
    
    Returns:
        Dictionary containing:
            - user_id: User identifier
            - trimester: Current pregnancy stage
            - generated_at: Timestamp of generation
            - current_nutrients: List of nutrient status objects with:
                - name, current_intake, recommended, unit, gap, percentage_met
            - today_intake: Today's nutrient values
            - nutrient_forecasts: Dict of forecasts per nutrient with:
                - values: List of predicted values
                - dates: List of forecast dates
                - trend: "increasing", "decreasing", or "stable"
            - forecast_horizon_days: Number of forecasted days
            - priority_nutrients: Top 3 nutrients with biggest gaps
            - dietary_recommendations: Actionable food suggestions
            - consistency_score: 0-100 tracking consistency score
            - streak_data: Current and longest meal/water streaks
            - context_days_used: How many historical days were used
            - forecaster_type: "ChronosForecaster" or "SimpleForecaster"
    
    Example:
        ```python
        insights = await get_pregnancy_insights(
            user_id="abc123",
            trimester="trimester_2",
            age=28,
            height_cm=165,
            weight_kg=65
        )
        print(f"Priority nutrients: {insights['priority_nutrients']}")
        print(f"Recommendations: {insights['dietary_recommendations']}")
        ```
    """
    engine = InsightEngine(user_id, use_chronos=use_chronos)
    
    return await engine.generate_insights(
        trimester=trimester,
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
        activity_factor=activity_factor,
        forecast_days=forecast_days,
        context_days=context_days
    )


# =============================================================================
# Testing
# =============================================================================

async def test_insight_engine():
    """Test function to demonstrate InsightEngine usage."""
    print("\n" + "=" * 80)
    print("INSIGHT ENGINE - TEST RUN")
    print("=" * 80)
    
    user_id = "MbG3wwDSH1o5lqQYoFG1"
    
    print(f"\nUser: {user_id}")
    print("Trimester: trimester_2")
    print("Age: 28, Height: 165cm, Weight: 65kg")
    print("-" * 80)
    
    # Run insights generation
    insights = await get_pregnancy_insights(
        user_id=user_id,
        trimester="trimester_2",
        age=28,
        height_cm=165,
        weight_kg=65,
        forecast_days=7,
        context_days=14,  # Shorter for testing
        use_chronos=True
    )
    
    print("\n[RESULTS]")
    print(f"Generated at: {insights['generated_at']}")
    print(f"Forecaster: {insights['forecaster_type']}")
    print(f"Context days: {insights['context_days_used']}")
    print(f"Consistency score: {insights['consistency_score']}%")
    
    print("\n[PRIORITY NUTRIENTS]")
    for nutrient in insights['priority_nutrients']:
        print(f"  - {nutrient}")
    
    print("\n[RECOMMENDATIONS]")
    for rec in insights['dietary_recommendations']:
        print(f"  - {rec}")
    
    print("\n[STREAK DATA]")
    for key, val in insights['streak_data'].items():
        print(f"  {key}: {val}")
    
    if insights.get('nutrient_forecasts'):
        print("\n[SAMPLE FORECAST - protein_g]")
        protein_forecast = insights['nutrient_forecasts'].get('protein_g', {})
        print(f"  Trend: {protein_forecast.get('trend', 'N/A')}")
        if protein_forecast.get('values'):
            print(f"  Next 7 days: {[round(v, 1) for v in protein_forecast['values'][:7]]}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_insight_engine())
