"""
FeatureBuilder.py - Module 2 of Pregnancy Nutrition Analysis Pipeline

Purpose:
    To convert raw daily-level nutrition data from DataExtractor into a
    structured, Chronos-compatible feature matrix optimized for pregnancy
    nutrition forecasting.

Tracked Nutrients (Pregnancy-Specific):
    - protein_g
    - fiber_g
    - iron_g
    - vitamin_d_mcg
    - omega_3_g
    - omega_3_epa_g
    - omega_3_dha_g

Additional Features:
    - water_intake_ml
    - meal_count
    - total_amount_g

Responsibilities:
    - DataFrame Construction: Converts raw daily dicts → chronological DataFrame
    - Feature Enrichment: Adds rolling averages and variability metrics
    - Normalization: Optionally normalizes numeric columns
    - Missing Data Handling: Fills missing values with zeros
    - Chronos Prep: Outputs numpy arrays or torch tensors for model input
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Feature Configuration
# =============================================================================

# Core pregnancy nutrients we track
PREGNANCY_NUTRIENTS = [
    "protein_g",
    "fiber_g",
    "iron_g",
    "vitamin_d_mcg",
    "omega_3_g",
    "omega_3_epa_g",
    "omega_3_dha_g",
]

# Additional tracking features
TRACKING_FEATURES = [
    "meal_count",
    "water_intake_ml",
    "total_amount_g",
    "water_percentage",
]

# All features to include in rolling calculations
ALL_FEATURES = PREGNANCY_NUTRIENTS + TRACKING_FEATURES


# =============================================================================
# Feature Builder Class
# =============================================================================

class FeatureBuilder:
    """
    Builds a clean, enriched feature matrix from extracted nutrition data.
    
    Optimized for pregnancy nutrition tracking with the following features:
        - 7 core nutrients (protein, fiber, iron, vitamin_d, omega_3, EPA, DHA)
        - Tracking metrics (meals, water, amounts)
        - Rolling statistics (mean, std, variability)
    """

    def __init__(self, normalize: bool = True, window_days: int = 7):
        """
        Initialize feature builder.

        Args:
            normalize (bool): Whether to normalize features using z-score.
            window_days (int): Rolling window size for statistics (default 7).
        """
        self.normalize = normalize
        self.window_days = window_days
        self.norm_params: Dict[str, Tuple[float, float]] = {}  # (mean, std) per feature
        self.feature_columns: List[str] = []
        
        logger.info(f"FeatureBuilder initialized: normalize={normalize}, window={window_days}")

    def build_dataframe(self, raw_data: List[Dict]) -> pd.DataFrame:
        """
        Convert raw JSON-like list from DataExtractor into a structured DataFrame.

        Args:
            raw_data (List[Dict]): List of daily records from DataExtractor.
                Example:
                [
                    {"date": "2026-01-08", "protein_g": 45.5, "fiber_g": 12.3, ...},
                    {"date": "2026-01-09", "protein_g": 50.2, "fiber_g": 15.1, ...}
                ]

        Returns:
            pd.DataFrame: Time-indexed DataFrame with all daily metrics.
        """
        if not raw_data:
            logger.warning("Empty raw_data provided to build_dataframe")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        
        # Parse date column and set as index
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # Sort chronologically
        df = df.sort_index()
        
        # Fill NaN values with 0
        df = df.fillna(0)
        
        # Ensure numeric columns are float type
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                df[col] = df[col].astype(float)
        
        logger.info(f"Built DataFrame: {len(df)} days, {len(df.columns)} base features")
        
        return df

    def add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add temporal dynamics (rolling means, stds, variability) for key nutrients.

        Features Added per nutrient:
            - {col}_roll_mean_{window}d: Rolling mean
            - {col}_roll_std_{window}d: Rolling standard deviation
            - {col}_variability: Coefficient of variation (std/mean)

        Args:
            df (pd.DataFrame): Base DataFrame from build_dataframe.

        Returns:
            pd.DataFrame: Enhanced DataFrame with rolling features.
        """
        if df.empty:
            return df
        
        # Columns to create rolling features for
        rolling_cols = [col for col in ALL_FEATURES if col in df.columns]
        
        new_features_count = 0
        
        for col in rolling_cols:
            # Rolling mean
            roll_mean_col = f"{col}_roll_mean_{self.window_days}d"
            df[roll_mean_col] = df[col].rolling(
                window=self.window_days, 
                min_periods=1
            ).mean()
            
            # Rolling standard deviation
            roll_std_col = f"{col}_roll_std_{self.window_days}d"
            df[roll_std_col] = df[col].rolling(
                window=self.window_days, 
                min_periods=1
            ).std().fillna(0)
            
            # Coefficient of variation (normalized variability)
            variability_col = f"{col}_variability"
            df[variability_col] = df[roll_std_col] / (df[roll_mean_col] + 1e-8)
            df[variability_col] = df[variability_col].fillna(0)
            
            new_features_count += 3
        
        logger.info(f"Added {new_features_count} rolling features (window={self.window_days}d)")
        
        return df

    def add_ratio_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create meaningful ratio features for pregnancy nutrition analysis.

        Features Added:
            - omega_3_balance: EPA to DHA ratio (brain development indicator)
            - iron_per_meal: Iron intake normalized by meal count
            - protein_per_meal: Protein normalized by meals
            - hydration_score: Water percentage (already tracked)

        Args:
            df (pd.DataFrame): DataFrame with rolling features.

        Returns:
            pd.DataFrame: Enhanced DataFrame with ratio features.
        """
        if df.empty:
            return df
        
        new_features_count = 0
        
        # Omega-3 EPA to DHA ratio (balance indicator)
        if all(col in df.columns for col in ['omega_3_epa_g', 'omega_3_dha_g']):
            df['omega_3_balance'] = df['omega_3_epa_g'] / (df['omega_3_dha_g'] + 1e-8)
            df['omega_3_balance'] = df['omega_3_balance'].fillna(0).clip(0, 5)
            new_features_count += 1
        
        # Iron per meal (consistency indicator)
        if all(col in df.columns for col in ['iron_g', 'meal_count']):
            df['iron_per_meal'] = df['iron_g'] / (df['meal_count'] + 1e-8)
            df['iron_per_meal'] = df['iron_per_meal'].fillna(0)
            new_features_count += 1
        
        # Protein per meal
        if all(col in df.columns for col in ['protein_g', 'meal_count']):
            df['protein_per_meal'] = df['protein_g'] / (df['meal_count'] + 1e-8)
            df['protein_per_meal'] = df['protein_per_meal'].fillna(0)
            new_features_count += 1
        
        # Fiber per meal
        if all(col in df.columns for col in ['fiber_g', 'meal_count']):
            df['fiber_per_meal'] = df['fiber_g'] / (df['meal_count'] + 1e-8)
            df['fiber_per_meal'] = df['fiber_per_meal'].fillna(0)
            new_features_count += 1
        
        # Water to meal ratio
        if all(col in df.columns for col in ['water_intake_ml', 'meal_count']):
            df['water_per_meal'] = df['water_intake_ml'] / (df['meal_count'] + 1e-8)
            df['water_per_meal'] = df['water_per_meal'].fillna(0)
            new_features_count += 1
        
        logger.info(f"Added {new_features_count} ratio features")
        
        return df

    def normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize all numeric columns using z-score normalization.

        Formula: z = (x - mean) / std

        Stores normalization parameters in self.norm_params for denormalization.

        Args:
            df (pd.DataFrame): DataFrame with all features.

        Returns:
            pd.DataFrame: Normalized DataFrame.
        """
        if df.empty:
            return df
        
        self.norm_params = {}
        
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
                mean = df[col].mean()
                std = df[col].std()
                
                # Store parameters
                self.norm_params[col] = (mean, std)
                
                # Normalize (avoid division by zero)
                if std > 1e-8:
                    df[col] = (df[col] - mean) / std
                else:
                    df[col] = 0.0
        
        logger.info(f"Normalized {len(self.norm_params)} features")
        
        return df

    def build_feature_matrix(
        self, 
        raw_data: List[Dict], 
        context_length: Optional[int] = 30,
        as_tensor: bool = False
    ) -> Union[np.ndarray, 'torch.Tensor']:
        """
        Main pipeline: raw data → enriched feature matrix ready for Chronos.

        Pipeline Steps:
            1. build_dataframe(raw_data)
            2. add_rolling_features(df)
            3. add_ratio_features(df)
            4. normalize_features(df) if self.normalize
            5. Select last context_length days
            6. Convert to numpy array or torch tensor

        Args:
            raw_data (List[Dict]): Raw daily data from DataExtractor.
            context_length (Optional[int]): Number of recent days to include.
                                           If None, include all data.
            as_tensor (bool): If True, return torch.Tensor. Otherwise numpy array.

        Returns:
            np.ndarray or torch.Tensor: Shape [context_length, num_features]
        """
        logger.info(f"Building feature matrix with context_length={context_length}")
        
        # Step 1: Build base DataFrame
        df = self.build_dataframe(raw_data)
        
        if df.empty:
            logger.warning("Empty DataFrame after build_dataframe")
            if as_tensor:
                import torch
                return torch.tensor([])
            return np.array([])
        
        # Step 2: Add rolling features
        df = self.add_rolling_features(df)
        
        # Step 3: Add ratio features
        df = self.add_ratio_features(df)
        
        # Step 4: Normalize if requested
        if self.normalize:
            df = self.normalize_features(df)
        
        # Store feature column names
        self.feature_columns = list(df.columns)
        
        # Step 5: Select last context_length days
        if context_length is not None and len(df) > context_length:
            df = df.iloc[-context_length:]
            logger.info(f"Selected last {context_length} days")
        
        # Step 6: Convert to array/tensor
        feature_matrix = df.values.astype(np.float32)
        
        logger.info(f"Final feature matrix shape: {feature_matrix.shape}")
        logger.info(f"Total features: {len(self.feature_columns)}")
        
        if as_tensor:
            import torch
            return torch.tensor(feature_matrix, dtype=torch.float32)
        
        return feature_matrix

    def extract_single_nutrient(
        self,
        raw_data: List[Dict],
        nutrient: str
    ) -> np.ndarray:
        """
        Extract a single nutrient's time series for forecasting.

        Args:
            raw_data (List[Dict]): Raw daily data.
            nutrient (str): Nutrient column name (e.g., "protein_g").

        Returns:
            np.ndarray: 1D array of nutrient values over time.
        """
        if not raw_data:
            return np.array([])
        
        values = [day.get(nutrient, 0.0) for day in raw_data]
        return np.array(values, dtype=np.float32)

    def extract_all_nutrients(
        self,
        raw_data: List[Dict]
    ) -> Dict[str, np.ndarray]:
        """
        Extract time series for all tracked pregnancy nutrients.

        Args:
            raw_data (List[Dict]): Raw daily data.

        Returns:
            Dict[str, np.ndarray]: Mapping nutrient name → 1D time series.
        """
        result = {}
        for nutrient in PREGNANCY_NUTRIENTS:
            result[nutrient] = self.extract_single_nutrient(raw_data, nutrient)
        return result

    def denormalize(
        self, 
        predictions: np.ndarray, 
        feature_names: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        Revert normalized predictions back to original scale.

        Args:
            predictions (np.ndarray): Normalized predictions. Shape [n_samples, n_features]
            feature_names (Optional[List[str]]): Names of features to denormalize.

        Returns:
            np.ndarray: Denormalized predictions.
        """
        if not self.norm_params:
            logger.warning("No normalization params. Returning predictions as-is.")
            return predictions
        
        denormalized = predictions.copy()
        
        if feature_names is None:
            feature_names = list(self.norm_params.keys())
        
        for i, col in enumerate(feature_names):
            if col in self.norm_params and i < predictions.shape[-1]:
                mean, std = self.norm_params[col]
                if len(predictions.shape) == 1:
                    denormalized[i] = predictions[i] * std + mean
                else:
                    denormalized[:, i] = predictions[:, i] * std + mean
        
        return denormalized

    def get_feature_summary(self) -> Dict:
        """
        Return summary information about the built features.

        Returns:
            Dict containing:
                - total_features: Total feature count
                - feature_names: List of feature names
                - pregnancy_nutrients: Core pregnancy nutrients
                - normalized: Whether normalized
                - window_days: Rolling window size
        """
        return {
            "total_features": len(self.feature_columns),
            "feature_names": self.feature_columns,
            "pregnancy_nutrients": PREGNANCY_NUTRIENTS,
            "tracking_features": TRACKING_FEATURES,
            "normalized": self.normalize,
            "window_days": self.window_days,
            "has_norm_params": bool(self.norm_params)
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def build_chronos_input(
    raw_data: List[Dict],
    nutrient: str,
    min_context: int = 10
) -> Optional[np.ndarray]:
    """
    Build Chronos-ready input for a single nutrient forecast.

    Args:
        raw_data: Raw daily data from DataExtractor.
        nutrient: Nutrient to forecast (e.g., "protein_g").
        min_context: Minimum data points needed.

    Returns:
        1D numpy array if sufficient data, None otherwise.
    """
    values = [day.get(nutrient, 0.0) for day in raw_data]
    
    if len(values) < min_context:
        logger.warning(f"Insufficient data for {nutrient}: {len(values)} < {min_context}")
        return None
    
    return np.array(values, dtype=np.float32)


def get_pregnancy_nutrient_names() -> List[str]:
    """Return list of pregnancy nutrient column names."""
    return PREGNANCY_NUTRIENTS.copy()


# =============================================================================
# Testing
# =============================================================================

def test_feature_builder():
    """Test function to demonstrate FeatureBuilder usage."""
    print("\n" + "=" * 80)
    print("FEATURE BUILDER - TEST RUN")
    print("=" * 80)
    
    # Create sample data
    sample_data = [
        {
            "date": "2026-01-05",
            "protein_g": 45.5,
            "fiber_g": 12.3,
            "iron_g": 0.015,
            "vitamin_d_mcg": 8.5,
            "omega_3_g": 2.1,
            "omega_3_epa_g": 0.8,
            "omega_3_dha_g": 1.2,
            "meal_count": 3,
            "water_intake_ml": 1800.0,
            "total_amount_g": 850.0,
            "water_percentage": 72.0
        },
        {
            "date": "2026-01-06",
            "protein_g": 52.0,
            "fiber_g": 15.0,
            "iron_g": 0.018,
            "vitamin_d_mcg": 10.0,
            "omega_3_g": 2.5,
            "omega_3_epa_g": 1.0,
            "omega_3_dha_g": 1.5,
            "meal_count": 4,
            "water_intake_ml": 2200.0,
            "total_amount_g": 950.0,
            "water_percentage": 88.0
        },
        {
            "date": "2026-01-07",
            "protein_g": 48.0,
            "fiber_g": 14.0,
            "iron_g": 0.012,
            "vitamin_d_mcg": 7.0,
            "omega_3_g": 1.8,
            "omega_3_epa_g": 0.7,
            "omega_3_dha_g": 1.0,
            "meal_count": 3,
            "water_intake_ml": 2000.0,
            "total_amount_g": 800.0,
            "water_percentage": 80.0
        },
    ]
    
    print(f"\nSample data: {len(sample_data)} days")
    
    # Test 1: Build with normalization
    print("\n[TEST 1] Building normalized feature matrix...")
    builder_norm = FeatureBuilder(normalize=True, window_days=3)
    matrix_norm = builder_norm.build_feature_matrix(sample_data)
    
    print(f"✓ Matrix shape: {matrix_norm.shape}")
    print(f"  Features: {len(builder_norm.feature_columns)}")
    
    # Test 2: Build without normalization
    print("\n[TEST 2] Building raw feature matrix...")
    builder_raw = FeatureBuilder(normalize=False, window_days=3)
    matrix_raw = builder_raw.build_feature_matrix(sample_data)
    
    print(f"✓ Matrix shape: {matrix_raw.shape}")
    
    # Test 3: Extract single nutrient
    print("\n[TEST 3] Extracting single nutrient time series...")
    protein_ts = builder_raw.extract_single_nutrient(sample_data, "protein_g")
    print(f"✓ Protein series: {protein_ts}")
    
    # Test 4: Extract all nutrients
    print("\n[TEST 4] Extracting all pregnancy nutrients...")
    all_nutrients = builder_raw.extract_all_nutrients(sample_data)
    for name, values in all_nutrients.items():
        print(f"  {name}: {values}")
    
    # Test 5: Feature summary
    print("\n[TEST 5] Feature summary...")
    summary = builder_norm.get_feature_summary()
    print(f"✓ Total features: {summary['total_features']}")
    print(f"  Pregnancy nutrients: {len(summary['pregnancy_nutrients'])}")
    print(f"  Normalized: {summary['normalized']}")
    
    print("\n" + "=" * 80)
    print("FEATURE BUILDER TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_feature_builder()