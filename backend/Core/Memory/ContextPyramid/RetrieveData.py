"""
RetrieveData.py - Central Firestore Data Gateway

Provides a unified interface to fetch all user data needed
for the context pyramid layers.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from config import (
    firestoreDB,
    users_collection,
    maternal_profiles_collection,
    baby_profiles_collection,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class UserProfile:
    """Complete user profile data."""
    user_id: str
    phone: Optional[str]
    email: Optional[str]
    role: str
    created_at: datetime


@dataclass
class MaternalProfileData:
    """Maternal profile data."""
    profile_id: str
    user_id: str
    # Personal
    age: int
    height_cm: float
    weight_kg: float
    language: str
    # Pregnancy
    stage: str
    expected_delivery_date: Optional[datetime]
    risk_level: str
    known_conditions: List[str]
    # Diet
    diet_type: str
    allergies: List[str]


@dataclass
class BabyProfileData:
    """Baby profile data."""
    profile_id: str
    maternal_id: str
    name: str
    date_of_birth: datetime
    gender: Optional[str]
    birth_weight_kg: float
    feeding_type: str


# =============================================================================
# Data Retrieval Class
# =============================================================================

class RetrieveData:
    """
    Central data gateway for the context pyramid.
    
    Fetches user data from Firestore and provides
    normalized interfaces for each data type.
    """
    
    def __init__(self, user_id: str):
        """
        Initialize the data retriever.
        
        Args:
            user_id: The user's Firestore document ID
        """
        self.user_id = user_id
        self._cache: Dict[str, Any] = {}
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if available."""
        return self._cache.get(key)
    
    def _set_cached(self, key: str, value: Any) -> None:
        """Cache data for reuse."""
        self._cache[key] = value
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
    
    # =========================================================================
    # User Profile (Layer 0)
    # =========================================================================
    
    def get_user_profile(self) -> Optional[UserProfile]:
        """
        Fetch user profile from Firestore.
        
        Returns:
            UserProfile or None if not found
        """
        cached = self._get_cached("user_profile")
        if cached:
            return cached
        
        try:
            doc = users_collection.document(self.user_id).get()
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            profile = UserProfile(
                user_id=self.user_id,
                phone=data.get("phone"),
                email=data.get("email"),
                role=data.get("role", "mother"),
                created_at=data.get("created_at", datetime.now(timezone.utc)),
            )
            
            self._set_cached("user_profile", profile)
            return profile
            
        except Exception as e:
            logger.error(f"Failed to fetch user profile: {e}")
            return None
    
    def get_maternal_profile(self) -> Optional[MaternalProfileData]:
        """
        Fetch maternal profile from Firestore.
        
        Returns:
            MaternalProfileData or None if not found
        """
        cached = self._get_cached("maternal_profile")
        if cached:
            return cached
        
        try:
            query = maternal_profiles_collection.where("user_id", "==", self.user_id).limit(1)
            docs = list(query.stream())
            
            if not docs:
                return None
            
            doc = docs[0]
            data = doc.to_dict()
            
            personal = data.get("personal", {})
            pregnancy = data.get("pregnancy", {})
            diet = data.get("diet", {})
            
            profile = MaternalProfileData(
                profile_id=doc.id,
                user_id=self.user_id,
                age=personal.get("age", 0),
                height_cm=personal.get("height_cm", 0),
                weight_kg=personal.get("weight_kg", 0),
                language=personal.get("language", "en"),
                stage=pregnancy.get("stage", "trimester_1"),
                expected_delivery_date=pregnancy.get("expected_delivery_date"),
                risk_level=pregnancy.get("risk_level", "low"),
                known_conditions=pregnancy.get("known_conditions", []),
                diet_type=diet.get("type", diet.get("diet_type", "mixed")),
                allergies=diet.get("allergies", []),
            )
            
            self._set_cached("maternal_profile", profile)
            return profile
            
        except Exception as e:
            logger.error(f"Failed to fetch maternal profile: {e}")
            return None
    
    def get_baby_profile(self) -> Optional[BabyProfileData]:
        """
        Fetch baby profile from Firestore.
        
        Returns:
            BabyProfileData or None if not found
        """
        cached = self._get_cached("baby_profile")
        if cached:
            return cached
        
        try:
            maternal = self.get_maternal_profile()
            if not maternal:
                return None
            
            query = baby_profiles_collection.where("maternal_id", "==", maternal.profile_id).limit(1)
            docs = list(query.stream())
            
            if not docs:
                return None
            
            doc = docs[0]
            data = doc.to_dict()
            
            profile_data = data.get("profile", {})
            feeding_data = data.get("feeding", {})
            
            baby = BabyProfileData(
                profile_id=doc.id,
                maternal_id=maternal.profile_id,
                name=profile_data.get("name", "Baby"),
                date_of_birth=profile_data.get("date_of_birth", datetime.now(timezone.utc)),
                gender=profile_data.get("gender"),
                birth_weight_kg=profile_data.get("birth_weight_kg", 0),
                feeding_type=feeding_data.get("type", feeding_data.get("feeding_type", "breastfed")),
            )
            
            self._set_cached("baby_profile", baby)
            return baby
            
        except Exception as e:
            logger.error(f"Failed to fetch baby profile: {e}")
            return None
    
    # =========================================================================
    # Nutrient Trends (Layer 1)
    # =========================================================================
    
    def get_nutrient_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Fetch recent nutrient intake trends.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with nutrient averages and trends
        """
        try:
            from Core.Insights.DataExtractor import DataExtractor
            
            extractor = DataExtractor(self.user_id)
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date - timedelta(days=days)
            
            # Use sync version if available, otherwise return empty
            try:
                raw_data = extractor.build_raw_data_sync(start_date, end_date)
            except AttributeError:
                # Fallback: fetch meals directly from Firestore
                raw_data = self._fetch_nutrition_from_firestore(start_date, end_date)
            
            if not raw_data:
                return {"error": "no_data", "days": days}
            
            # Calculate averages
            nutrients = ["protein_g", "fiber_g", "iron_mg", "vitamin_d_iu", "omega_3_g"]
            averages = {}
            
            for nutrient in nutrients:
                values = [d.get(nutrient, 0) for d in raw_data if d.get(nutrient, 0) > 0]
                if values:
                    averages[nutrient] = round(sum(values) / len(values), 2)
                else:
                    averages[nutrient] = 0
            
            # Water average
            water_values = [d.get("water_intake_ml", 0) for d in raw_data]
            averages["water_ml"] = round(sum(water_values) / len(water_values), 0) if water_values else 0
            
            return {
                "period_days": days,
                "days_with_data": len([d for d in raw_data if d.get("meal_count", 0) > 0]),
                "averages": averages,
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch nutrient trends: {e}")
            return {"error": str(e)}
    
    def _fetch_nutrition_from_firestore(self, start_date, end_date) -> List[Dict]:
        """Fallback: fetch nutrition data directly from Firestore."""
        try:
            meals_collection = firestoreDB.collection("users").document(self.user_id).collection("meals")
            
            from datetime import datetime as dt
            start_dt = dt.combine(start_date, dt.min.time()).replace(tzinfo=timezone.utc)
            end_dt = dt.combine(end_date, dt.max.time()).replace(tzinfo=timezone.utc)
            
            query = meals_collection.where("created_at", ">=", start_dt).where("created_at", "<=", end_dt)
            
            # Group by date
            daily_data = {}
            for doc in query.stream():
                data = doc.to_dict()
                created = data.get("created_at")
                if created:
                    date_key = created.strftime("%Y-%m-%d") if hasattr(created, 'strftime') else str(created)[:10]
                    if date_key not in daily_data:
                        daily_data[date_key] = {"meal_count": 0, "protein_g": 0, "fiber_g": 0}
                    daily_data[date_key]["meal_count"] += 1
                    analysis = data.get("analysis", {})
                    daily_data[date_key]["protein_g"] += analysis.get("protein", 0)
                    daily_data[date_key]["fiber_g"] += analysis.get("fiber", 0)
            
            return list(daily_data.values())
        except Exception as e:
            logger.warning(f"Fallback nutrition fetch failed: {e}")
            return []
    
    # =========================================================================
    # Recent Symptoms (Layer 2)
    # =========================================================================
    
    async def get_recent_symptoms(self, days: int = 7) -> List[Dict]:
        """
        Fetch recently reported symptoms.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of symptom records
        """
        try:
            from Core.Memory.SymptomMapper import get_recent_medic_stones
            
            stones = await get_recent_medic_stones(self.user_id, days=days)
            
            return [
                {
                    "symptom": s.symptom_name,
                    "severity": s.severity,
                    "reported_at": s.reported_at.isoformat(),
                    "context": s.context,
                }
                for s in stones
            ]
            
        except Exception as e:
            logger.error(f"Failed to fetch recent symptoms: {e}")
            return []
    
    # =========================================================================
    # Allergies and Conditions (Layer 3)
    # =========================================================================
    
    def get_allergies_and_conditions(self) -> Dict[str, List[str]]:
        """
        Fetch allergies and known medical conditions.
        
        Returns:
            Dict with allergies and conditions lists
        """
        maternal = self.get_maternal_profile()
        
        if not maternal:
            return {"allergies": [], "conditions": []}
        
        return {
            "allergies": maternal.allergies,
            "conditions": maternal.known_conditions,
            "diet_type": maternal.diet_type,
            "risk_level": maternal.risk_level,
        }
    
    # =========================================================================
    # Message History (Layer 4)
    # =========================================================================
    
    async def get_message_history(self, limit: int = 20) -> List[Dict]:
        """
        Fetch past message history for context.
        
        Args:
            limit: Maximum messages to retrieve
            
        Returns:
            List of message records
        """
        try:
            # Get messages subcollection
            messages_collection = firestoreDB.collection("users").document(self.user_id).collection("messages")
            
            query = (
                messages_collection
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
            )
            
            messages = []
            for doc in query.stream():
                data = doc.to_dict()
                messages.append({
                    "id": doc.id,
                    "role": data.get("role", "user"),
                    "content": data.get("content", ""),
                    "created_at": data.get("created_at", datetime.now(timezone.utc)).isoformat(),
                })
            
            # Reverse to get chronological order
            messages.reverse()
            return messages
            
        except Exception as e:
            logger.error(f"Failed to fetch message history: {e}")
            return []
    
    # =========================================================================
    # Aggregate Methods
    # =========================================================================
    
    async def get_full_context(self) -> Dict[str, Any]:
        """
        Fetch all context data in one call.
        
        Returns:
            Complete context dictionary
        """
        user = self.get_user_profile()
        maternal = self.get_maternal_profile()
        baby = self.get_baby_profile()
        nutrients = self.get_nutrient_trends()
        symptoms = await self.get_recent_symptoms()
        allergies = self.get_allergies_and_conditions()
        messages = await self.get_message_history()
        
        return {
            "user": {
                "id": user.user_id if user else None,
                "role": user.role if user else None,
            } if user else None,
            "maternal": {
                "age": maternal.age,
                "stage": maternal.stage,
                "risk_level": maternal.risk_level,
            } if maternal else None,
            "baby": {
                "name": baby.name,
                "age_months": self._calculate_baby_age_months(baby),
            } if baby else None,
            "nutrients": nutrients,
            "recent_symptoms": symptoms[:5],
            "allergies": allergies,
            "message_count": len(messages),
        }
    
    def _calculate_baby_age_months(self, baby: BabyProfileData) -> int:
        """Calculate baby's age in months."""
        if not baby:
            return 0
        
        now = datetime.now(timezone.utc)
        dob = baby.date_of_birth
        if dob.tzinfo is None:
            dob = dob.replace(tzinfo=timezone.utc)
        
        age_days = (now - dob).days
        return max(0, age_days // 30)
