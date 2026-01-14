"""
PyramidManager.py - Context Pyramid Orchestrator

Manages a 5-layer hierarchical context system:
- Layer 0 (Base): User profile info
- Layer 1: Nutrient trends
- Layer 2: Recent symptoms
- Layer 3: Allergies and conditions
- Layer 4 (Top): Past message history
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import IntEnum
import logging

from .RetrieveData import RetrieveData

logger = logging.getLogger(__name__)


# =============================================================================
# Layer Definitions
# =============================================================================

class ContextLayer(IntEnum):
    """Context pyramid layer identifiers."""
    USER_INFO = 0       # Base layer - static user data
    NUTRIENT_TRENDS = 1 # Recent nutrient insights
    SYMPTOMS = 2        # Recently reported symptoms
    ALLERGIES = 3       # Allergies and conditions
    MESSAGE_HISTORY = 4 # Past conversation context


@dataclass
class LayerContent:
    """Content for a single context layer."""
    layer: ContextLayer
    name: str
    data: Dict[str, Any]
    relevance_score: float = 1.0  # 0.0-1.0, how relevant to current query
    token_estimate: int = 0       # Estimated tokens for this layer
    
    def to_dict(self) -> dict:
        return {
            "layer": self.layer.value,
            "name": self.name,
            "data": self.data,
            "relevance_score": round(self.relevance_score, 2),
            "token_estimate": self.token_estimate,
        }
    
    def to_context_string(self) -> str:
        """Convert layer to LLM-friendly string."""
        lines = [f"### {self.name}"]
        
        for key, value in self.data.items():
            if isinstance(value, list):
                if value:
                    lines.append(f"- {key}: {', '.join(str(v) for v in value[:5])}")
            elif isinstance(value, dict):
                lines.append(f"- {key}:")
                for k, v in list(value.items())[:5]:
                    lines.append(f"  - {k}: {v}")
            elif value is not None:
                lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)


@dataclass
class ContextPyramid:
    """Complete context pyramid with all layers."""
    user_id: str
    generated_at: datetime
    layers: List[LayerContent]
    total_tokens: int
    query_context: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "generated_at": self.generated_at.isoformat(),
            "query_context": self.query_context,
            "total_tokens": self.total_tokens,
            "layer_count": len(self.layers),
            "layers": [l.to_dict() for l in self.layers],
        }
    
    def to_context_string(self, max_tokens: int = 2000) -> str:
        """
        Generate LLM-ready context string.
        
        Args:
            max_tokens: Maximum tokens (approximate)
            
        Returns:
            Formatted context string
        """
        lines = ["## User Context"]
        current_tokens = 10
        
        # Build layers from bottom to top (most stable first)
        sorted_layers = sorted(self.layers, key=lambda l: l.layer.value)
        
        for layer in sorted_layers:
            layer_content = layer.to_context_string()
            layer_tokens = len(layer_content) // 4  # Rough token estimate
            
            if current_tokens + layer_tokens > max_tokens:
                break
            
            lines.append("")
            lines.append(layer_content)
            current_tokens += layer_tokens
        
        return "\n".join(lines)
    
    def get_layer(self, layer: ContextLayer) -> Optional[LayerContent]:
        """Get a specific layer by type."""
        for l in self.layers:
            if l.layer == layer:
                return l
        return None


# =============================================================================
# Pyramid Manager
# =============================================================================

class PyramidManager:
    """
    Orchestrates the context pyramid construction.
    
    Builds and caches layers, applies relevance scoring
    based on query, and produces LLM-ready context.
    """
    
    # Token budget defaults
    DEFAULT_MAX_TOKENS = 2000
    
    # Layer token allocations (approximate)
    LAYER_BUDGETS = {
        ContextLayer.USER_INFO: 200,
        ContextLayer.NUTRIENT_TRENDS: 300,
        ContextLayer.SYMPTOMS: 400,
        ContextLayer.ALLERGIES: 200,
        ContextLayer.MESSAGE_HISTORY: 600,
    }
    
    def __init__(self, user_id: str):
        """
        Initialize the pyramid manager.
        
        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
        self.data_retriever = RetrieveData(user_id)
        self._layer_cache: Dict[ContextLayer, LayerContent] = {}
    
    def clear_cache(self) -> None:
        """Clear all cached layers."""
        self._layer_cache.clear()
        self.data_retriever.clear_cache()
    
    # =========================================================================
    # Layer Builders
    # =========================================================================
    
    def _build_user_info_layer(self) -> LayerContent:
        """Build Layer 0: User profile info."""
        user = self.data_retriever.get_user_profile()
        maternal = self.data_retriever.get_maternal_profile()
        baby = self.data_retriever.get_baby_profile()
        
        data = {}
        
        if maternal:
            data["age"] = maternal.age
            data["pregnancy_stage"] = maternal.stage
            data["risk_level"] = maternal.risk_level
            data["language"] = maternal.language
            
            # Calculate gestational info
            if maternal.expected_delivery_date:
                edd = maternal.expected_delivery_date
                # Handle string dates from Firestore
                if isinstance(edd, str):
                    try:
                        from dateutil.parser import parse
                        edd = parse(edd)
                    except:
                        edd = None
                if edd:
                    now = datetime.now(timezone.utc)
                    if edd.tzinfo is None:
                        edd = edd.replace(tzinfo=timezone.utc)
                    days_until = (edd - now).days
                    if days_until > 0:
                        data["days_until_delivery"] = days_until
                        data["weeks_pregnant"] = 40 - (days_until // 7)
        
        if baby:
            data["baby_name"] = baby.name
            data["baby_feeding"] = baby.feeding_type
            # Calculate baby age - handle string dates
            dob = baby.date_of_birth
            if isinstance(dob, str):
                try:
                    from dateutil.parser import parse
                    dob = parse(dob)
                except:
                    dob = datetime.now(timezone.utc)
            if dob.tzinfo is None:
                dob = dob.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - dob).days
            data["baby_age_months"] = max(0, age_days // 30)
        
        return LayerContent(
            layer=ContextLayer.USER_INFO,
            name="User Profile",
            data=data,
            token_estimate=len(str(data)) // 4,
        )
    
    def _build_nutrient_layer(self, days: int = 7) -> LayerContent:
        """Build Layer 1: Nutrient trends."""
        trends = self.data_retriever.get_nutrient_trends(days)
        
        data = {}
        if "error" not in trends:
            data["period"] = f"Last {trends.get('period_days', days)} days"
            data["tracking_days"] = trends.get("days_with_data", 0)
            
            averages = trends.get("averages", {})
            if averages:
                data["daily_averages"] = averages
        else:
            data["status"] = "No nutrition data available"
        
        return LayerContent(
            layer=ContextLayer.NUTRIENT_TRENDS,
            name="Nutrient Trends",
            data=data,
            token_estimate=len(str(data)) // 4,
        )
    
    async def _build_symptom_layer(self, days: int = 7) -> LayerContent:
        """Build Layer 2: Recent symptoms."""
        symptoms = await self.data_retriever.get_recent_symptoms(days)
        
        # Summarize symptoms
        symptom_counts: Dict[str, int] = {}
        max_severities: Dict[str, int] = {}
        
        for s in symptoms:
            name = s.get("symptom", "unknown")
            symptom_counts[name] = symptom_counts.get(name, 0) + 1
            max_severities[name] = max(max_severities.get(name, 0), s.get("severity", 1))
        
        data = {
            "period": f"Last {days} days",
            "total_reports": len(symptoms),
        }
        
        if symptom_counts:
            data["symptoms"] = [
                {"name": name, "count": count, "max_severity": max_severities.get(name, 1)}
                for name, count in sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
            ][:5]  # Top 5
        else:
            data["symptoms"] = []
            data["status"] = "No symptoms reported"
        
        return LayerContent(
            layer=ContextLayer.SYMPTOMS,
            name="Recent Symptoms",
            data=data,
            token_estimate=len(str(data)) // 4,
        )
    
    def _build_allergy_layer(self) -> LayerContent:
        """Build Layer 3: Allergies and conditions."""
        allergy_data = self.data_retriever.get_allergies_and_conditions()
        
        data = {}
        
        if allergy_data.get("allergies"):
            data["allergies"] = allergy_data["allergies"]
        
        if allergy_data.get("conditions"):
            data["medical_conditions"] = allergy_data["conditions"]
        
        if allergy_data.get("diet_type"):
            data["diet_preference"] = allergy_data["diet_type"]
        
        if not data:
            data["status"] = "No allergies or conditions on record"
        
        return LayerContent(
            layer=ContextLayer.ALLERGIES,
            name="Allergies & Conditions",
            data=data,
            token_estimate=len(str(data)) // 4,
        )
    
    async def _build_message_layer(self, limit: int = 10) -> LayerContent:
        """Build Layer 4: Message history."""
        messages = await self.data_retriever.get_message_history(limit)
        
        # Summarize recent conversation
        data = {
            "recent_messages": len(messages),
        }
        
        if messages:
            # Get last few exchanges
            recent = messages[-6:]  # Last 3 exchanges (user + assistant)
            data["conversation_summary"] = [
                {"role": m.get("role"), "preview": m.get("content", "")[:100]}
                for m in recent
            ]
        else:
            data["status"] = "No previous conversation"
        
        return LayerContent(
            layer=ContextLayer.MESSAGE_HISTORY,
            name="Conversation History",
            data=data,
            token_estimate=len(str(data)) // 4,
        )
    
    # =========================================================================
    # Relevance Scoring
    # =========================================================================
    
    def _score_relevance(
        self,
        layer: LayerContent,
        query: Optional[str] = None
    ) -> float:
        """
        Score layer relevance based on query.
        
        Args:
            layer: The layer to score
            query: Optional query for context-aware scoring
            
        Returns:
            Relevance score 0.0-1.0
        """
        # Base scores by layer type (more volatile = higher base)
        base_scores = {
            ContextLayer.USER_INFO: 0.9,      # Always relevant
            ContextLayer.ALLERGIES: 0.85,     # Almost always relevant
            ContextLayer.SYMPTOMS: 0.8,       # Usually relevant
            ContextLayer.NUTRIENT_TRENDS: 0.7,
            ContextLayer.MESSAGE_HISTORY: 0.6,
        }
        
        score = base_scores.get(layer.layer, 0.5)
        
        # Query-based boosting
        if query:
            query_lower = query.lower()
            
            # Boost symptoms if query mentions health/symptoms
            if any(kw in query_lower for kw in ["symptom", "pain", "feel", "hurt", "sick"]):
                if layer.layer == ContextLayer.SYMPTOMS:
                    score = min(1.0, score + 0.2)
            
            # Boost nutrition if query mentions food/diet
            if any(kw in query_lower for kw in ["food", "eat", "diet", "nutrient", "vitamin"]):
                if layer.layer == ContextLayer.NUTRIENT_TRENDS:
                    score = min(1.0, score + 0.2)
            
            # Boost allergies if query mentions allergies
            if any(kw in query_lower for kw in ["allergy", "allergic", "avoid", "safe"]):
                if layer.layer == ContextLayer.ALLERGIES:
                    score = min(1.0, score + 0.15)
        
        return score
    
    # =========================================================================
    # Main Build Methods
    # =========================================================================
    
    async def build_pyramid(
        self,
        query: Optional[str] = None,
        include_layers: Optional[List[ContextLayer]] = None
    ) -> ContextPyramid:
        """
        Build the complete context pyramid.
        
        Args:
            query: Optional query for relevance scoring
            include_layers: Optional list of specific layers to include
            
        Returns:
            ContextPyramid with all layers
        """
        if include_layers is None:
            include_layers = list(ContextLayer)
        
        layers = []
        
        # Build each requested layer
        for layer_type in include_layers:
            try:
                if layer_type == ContextLayer.USER_INFO:
                    layer = self._build_user_info_layer()
                elif layer_type == ContextLayer.NUTRIENT_TRENDS:
                    layer = self._build_nutrient_layer()
                elif layer_type == ContextLayer.SYMPTOMS:
                    layer = await self._build_symptom_layer()
                elif layer_type == ContextLayer.ALLERGIES:
                    layer = self._build_allergy_layer()
                elif layer_type == ContextLayer.MESSAGE_HISTORY:
                    layer = await self._build_message_layer()
                else:
                    continue
                
                # Score relevance
                layer.relevance_score = self._score_relevance(layer, query)
                layers.append(layer)
                
            except Exception as e:
                logger.error(f"Failed to build layer {layer_type.name}: {e}")
        
        # Calculate total tokens
        total_tokens = sum(l.token_estimate for l in layers)
        
        return ContextPyramid(
            user_id=self.user_id,
            generated_at=datetime.now(timezone.utc),
            layers=layers,
            total_tokens=total_tokens,
            query_context=query,
        )
    
    async def get_context_for_query(
        self,
        query: str,
        max_tokens: int = None
    ) -> str:
        """
        Get optimized context string for a query.
        
        Args:
            query: The user's query
            max_tokens: Maximum tokens to use
            
        Returns:
            LLM-ready context string
        """
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        
        pyramid = await self.build_pyramid(query)
        
        # Sort layers by relevance
        sorted_layers = sorted(
            pyramid.layers,
            key=lambda l: l.relevance_score,
            reverse=True
        )
        
        # Build context string respecting token budget
        lines = ["## Context"]
        current_tokens = 10
        
        for layer in sorted_layers:
            if layer.relevance_score < 0.5:
                continue  # Skip low relevance layers
            
            layer_str = layer.to_context_string()
            layer_tokens = layer.token_estimate
            
            if current_tokens + layer_tokens > max_tokens:
                continue  # Skip if over budget
            
            lines.append("")
            lines.append(layer_str)
            current_tokens += layer_tokens
        
        return "\n".join(lines)
    
    async def get_layer(self, layer_type: ContextLayer) -> Optional[LayerContent]:
        """Get a specific layer."""
        pyramid = await self.build_pyramid(include_layers=[layer_type])
        return pyramid.get_layer(layer_type)
