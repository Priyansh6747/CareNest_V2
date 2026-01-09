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