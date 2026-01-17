from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator

# Represents a MongoDB ObjectId as a string in the model
PyObjectId = Annotated[str, BeforeValidator(str)]

class BaseMongoModel(BaseModel):
    """Base model to handle MongoDB's _id and datetime serialization"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "id": "64b1f... (hex string)"
            }
        }
    )



#Enums
class UserRole(str, Enum):
    mother = "mother"
    health_worker = "health_worker"
    doctor = "doctor"

class PregnancyStage(str, Enum):
    trimester_1 = "trimester_1"
    trimester_2 = "trimester_2"
    trimester_3 = "trimester_3"
    postpartum = "postpartum"

class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class DietType(str, Enum):
    veg = "veg"
    non_veg = "non_veg"
    mixed = "mixed"

class DeliveryType(str, Enum):
    normal = "normal"
    c_section = "c_section"

class FeedingType(str, Enum):
    breastfed = "breastfed"
    formula = "formula"
    mixed = "mixed"



#Models
class User(BaseMongoModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    firebase_uid: Optional[str] = None
    phone: Optional[str] = Field(..., pattern=r"^\+?1?\d{9,15}$")
    email: Optional[str] = None
    role: UserRole
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

#Maternal
class PersonalData(BaseModel):
    age: int
    height_cm: float
    weight_kg: float
    language: str = "en"

class PregnancyData(BaseModel):
    stage: PregnancyStage
    expected_delivery_date: datetime
    gravida: int
    para: int
    known_conditions: List[str] = []
    risk_level: RiskLevel

class DietData(BaseModel):
    diet_type: DietType = Field(alias="type")
    allergies: List[str] = []

class MaternalProfile(BaseMongoModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId = Field(...)
    personal: PersonalData
    pregnancy: PregnancyData
    diet: DietData
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

#Baby
class BabyInfo(BaseModel):
    name: Optional[str] = "Baby"
    date_of_birth: datetime
    gender: Optional[str] = None
    birth_weight_kg: float
    delivery_type: DeliveryType

class FeedingData(BaseModel):
    feeding_type: FeedingType = Field(alias="type")

class BabyProfile(BaseMongoModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    maternal_id: PyObjectId = Field(...)
    profile: BabyInfo
    feeding: FeedingData
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

#utils
class OnboardingSteps(BaseModel):
    maternal_profile: bool = False
    baby_profile: bool = False
    consent: bool = False

class OnboardingStatus(BaseMongoModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId = Field(...)
    steps: OnboardingSteps
    completed_at: Optional[datetime] = None

class Consents(BaseModel):
    data_usage: bool = False
    medical_disclaimer: bool = False

class UserConsent(BaseMongoModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId = Field(...)
    consents: Consents
    accepted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== INPUT MODELS (Client-safe) ====================
# These prevent clients from injecting _id, created_at, etc.

class UserCreate(BaseModel):
    """Client input for creating a User"""
    firebase_uid: Optional[str] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?1?\d{9,15}$")
    email: Optional[str] = None
    role: UserRole = UserRole.mother

class MaternalProfileCreate(BaseModel):
    """Client input for creating a MaternalProfile"""
    personal: PersonalData
    pregnancy: PregnancyData
    diet: DietData

class BabyProfileCreate(BaseModel):
    """Client input for creating a BabyProfile"""
    profile: BabyInfo
    feeding: FeedingData

class UserConsentCreate(BaseModel):
    """Client input for creating UserConsent"""
    consents: Consents


# ==================== ONBOARDING REQUEST/RESPONSE ====================

class OnboardingInitRequest(BaseModel):
    """Request body for POST /onboarding/init"""
    user: UserCreate
    maternal: MaternalProfileCreate
    consent: UserConsentCreate
    baby: Optional[BabyProfileCreate] = None

class OnboardingInitResponse(BaseModel):
    """Response from POST /onboarding/init"""
    user_id: PyObjectId
    maternal_id: PyObjectId
    baby_id: Optional[PyObjectId] = None
    onboarding_status_id: PyObjectId
    consent_id: PyObjectId
    steps: OnboardingSteps
    completed: bool
    next_action: str


# ==================== INSIGHT ENGINE MODELS ====================

class NutrientStatus(BaseModel):
    """Status for a single nutrient (current intake vs RDA)."""
    name: str
    current_intake: float
    recommended: float
    unit: str
    gap: float  # positive = deficit, negative = surplus
    percentage_met: float


class NutrientForecast(BaseModel):
    """Forecast for a single nutrient's future values."""
    values: List[float]      # One value per forecast day
    dates: List[str]         # ISO date strings
    trend: str               # "increasing", "decreasing", "stable", "unknown"


class StreakData(BaseModel):
    """User's tracking streak information."""
    meal_streak: int = 0
    water_streak: int = 0
    longest_meal_streak: int = 0
    longest_water_streak: int = 0


class WaterForecast(BaseModel):
    """Forecast for water intake."""
    values: List[float]
    dates: List[str]
    trend: str
    predicted_avg_ml: float


class WaterTrends(BaseModel):
    """Comprehensive water intake trends and hydration status."""
    current_intake_ml: float
    weekly_average_ml: float
    goal_ml: float
    today_goal_percentage: float
    weekly_goal_percentage: float
    hydration_status: str      # "excellent", "good", "fair", "needs_improvement"
    days_meeting_goal: int
    water_consistency_score: float
    forecast: WaterForecast
    recommendations: List[str]


class NutritionInsights(BaseModel):
    """Complete nutrition insights response from InsightEngine."""
    user_id: str
    trimester: PregnancyStage
    generated_at: datetime
    
    # Current status
    current_nutrients: List[NutrientStatus]
    today_intake: dict
    
    # Forecasts
    nutrient_forecasts: dict  # Dict[str, NutrientForecast]
    forecast_horizon_days: int
    
    # Recommendations
    priority_nutrients: List[str]  # Top nutrients with biggest gaps
    dietary_recommendations: List[str]
    
    # Trends and consistency
    consistency_score: float  # 0-100 score for tracking consistency
    streak_data: StreakData
    
    # Water trends (new feature)
    water_trends: WaterTrends
    
    # Metadata
    context_days_used: int
    forecaster_type: str  # "ChronosForecaster" or "SimpleForecaster"
    error: Optional[str] = None