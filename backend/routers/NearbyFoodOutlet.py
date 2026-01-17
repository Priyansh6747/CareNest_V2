"""
Nearby Food Outlet Router - Find healthy food options near user location

Features:
- Find nearby restaurants, grocery stores, organic food shops
- Filter by food categories relevant to maternal health
- Provide personalized recommendations based on nutrient needs
"""
import os
from typing import Optional, List

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

load_dotenv()

router = APIRouter(prefix="/food", tags=["Food Outlets"])


# =============================================================================
# Request/Response Models
# =============================================================================

class FoodLocationRequest(BaseModel):
    """Request for finding nearby food outlets."""
    lat: float
    lng: float
    radius: Optional[int] = 3000  # meters (default 3km)
    limit: Optional[int] = 10
    category: Optional[str] = "all"  # all, restaurant, grocery, organic, cafe
    priority_nutrients: Optional[List[str]] = None  # nutrients user needs more of


class FoodOutlet(BaseModel):
    """A food outlet result."""
    name: str
    address: str
    category: str
    location: dict
    distance_meters: Optional[float] = None
    nutrient_match: Optional[List[str]] = None  # Which priority nutrients this place may help with
    recommendation: Optional[str] = None  # Why this place is recommended


# Category mapping to Geoapify categories
CATEGORY_MAPPING = {
    "all": "catering",  # All food-related places
    "restaurant": "catering.restaurant",
    "grocery": "commercial.supermarket,commercial.marketplace",
    "organic": "commercial.health_and_beauty.organic,commercial.supermarket.organic",
    "cafe": "catering.cafe",
    "fast_food": "catering.fast_food",
    "bakery": "catering.bakery",
    "health_food": "commercial.health_and_beauty.organic",
}

# Nutrient to food type recommendations for pregnancy
NUTRIENT_FOOD_SUGGESTIONS = {
    "iron": {
        "keywords": ["meat", "spinach", "lentils", "beans", "tofu"],
        "places": ["restaurant", "grocery"],
        "tip": "Look for places serving leafy greens, legumes, or iron-fortified foods"
    },
    "calcium": {
        "keywords": ["dairy", "milk", "cheese", "yogurt", "paneer"],
        "places": ["grocery", "cafe"],
        "tip": "Dairy shops, cafes with smoothies, or grocery stores with fortified products"
    },
    "folic_acid": {
        "keywords": ["leafy greens", "citrus", "beans", "fortified"],
        "places": ["grocery", "restaurant"],
        "tip": "Look for salad bars, vegetarian restaurants, or stores with fresh produce"
    },
    "folate": {
        "keywords": ["leafy greens", "citrus", "beans", "fortified"],
        "places": ["grocery", "restaurant"],
        "tip": "Look for salad bars, vegetarian restaurants, or stores with fresh produce"
    },
    "protein": {
        "keywords": ["eggs", "chicken", "fish", "paneer", "dal", "legumes"],
        "places": ["restaurant", "grocery"],
        "tip": "Look for protein-rich meal options or grocery stores with quality protein sources"
    },
    "omega_3": {
        "keywords": ["fish", "walnuts", "flaxseed", "salmon"],
        "places": ["restaurant", "grocery"],
        "tip": "Seafood restaurants or stores with omega-3 rich foods like fatty fish and nuts"
    },
    "vitamin_d": {
        "keywords": ["fortified foods", "fish", "eggs", "mushrooms"],
        "places": ["grocery", "restaurant"],
        "tip": "Look for fortified dairy products or vitamin D rich foods"
    },
    "fiber": {
        "keywords": ["whole grains", "vegetables", "fruits", "beans"],
        "places": ["grocery", "restaurant", "organic"],
        "tip": "Health food stores, vegetarian restaurants, or places with whole grain options"
    },
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_food_recommendations(priority_nutrients: List[str]) -> dict:
    """Get food recommendations based on priority nutrients."""
    recommendations = {
        "suggested_categories": set(),
        "food_tips": [],
        "keywords": set(),
    }
    
    for nutrient in priority_nutrients:
        # Clean nutrient name (remove _mg, _g, etc.)
        clean_nutrient = nutrient.lower().replace("_mg", "").replace("_g", "").replace("_iu", "").replace("_mcg", "")
        
        if clean_nutrient in NUTRIENT_FOOD_SUGGESTIONS:
            info = NUTRIENT_FOOD_SUGGESTIONS[clean_nutrient]
            recommendations["suggested_categories"].update(info["places"])
            recommendations["food_tips"].append(f"{clean_nutrient.title()}: {info['tip']}")
            recommendations["keywords"].update(info["keywords"])
    
    return {
        "suggested_categories": list(recommendations["suggested_categories"]),
        "food_tips": recommendations["food_tips"],
        "keywords": list(recommendations["keywords"]),
    }


def match_outlet_to_nutrients(outlet_name: str, outlet_category: str, priority_nutrients: List[str]) -> List[str]:
    """Check which priority nutrients an outlet might help with."""
    matches = []
    outlet_name_lower = outlet_name.lower()
    
    for nutrient in priority_nutrients:
        clean_nutrient = nutrient.lower().replace("_mg", "").replace("_g", "").replace("_iu", "").replace("_mcg", "")
        
        if clean_nutrient in NUTRIENT_FOOD_SUGGESTIONS:
            keywords = NUTRIENT_FOOD_SUGGESTIONS[clean_nutrient]["keywords"]
            # Check if any keyword matches the outlet name
            if any(keyword in outlet_name_lower for keyword in keywords):
                matches.append(clean_nutrient.title())
    
    return matches


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/nearby-outlets",
    summary="Find nearby food outlets",
    description="""
    Find nearby food outlets including restaurants, grocery stores, cafes, and health food shops.
    
    Optionally provide priority_nutrients to get personalized recommendations based on 
    what nutrients you need more of (from insights).
    """,
)
async def find_nearby_food_outlets(request: FoodLocationRequest):
    """Find nearby food outlets with optional nutrient-based recommendations."""
    api_key = os.getenv("GEOAPIFY_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key not configured")

    try:
        # Determine category filter
        category = request.category or "all"
        geoapify_category = CATEGORY_MAPPING.get(category, "catering")
        
        # If priority nutrients provided, we might want to search multiple categories
        if request.priority_nutrients:
            food_recs = get_food_recommendations(request.priority_nutrients)
            # Could potentially expand the search to include more relevant categories
        else:
            food_recs = None

        # Make request to Geoapify
        url = "https://api.geoapify.com/v2/places"
        params = {
            "categories": geoapify_category,
            "filter": f"circle:{request.lng},{request.lat},{request.radius}",
            "limit": request.limit,
            "apiKey": api_key
        }

        response = requests.get(url, params=params)
        data = response.json()

        # Process results
        outlets = []
        for place in data.get("features", []):
            props = place.get("properties", {})
            
            # Determine outlet category
            categories = props.get("categories", [])
            outlet_category = "restaurant"  # default
            if any("supermarket" in c or "marketplace" in c for c in categories):
                outlet_category = "grocery"
            elif any("cafe" in c for c in categories):
                outlet_category = "cafe"
            elif any("bakery" in c for c in categories):
                outlet_category = "bakery"
            elif any("organic" in c or "health" in c for c in categories):
                outlet_category = "organic"
            
            outlet = {
                "name": props.get("name", "Food Outlet"),
                "address": props.get("formatted", ""),
                "category": outlet_category,
                "location": {
                    "lat": place["geometry"]["coordinates"][1],
                    "lng": place["geometry"]["coordinates"][0]
                },
                "distance_meters": props.get("distance"),
            }
            
            # Add nutrient matching if priority nutrients provided
            if request.priority_nutrients:
                nutrient_matches = match_outlet_to_nutrients(
                    outlet["name"], 
                    outlet_category, 
                    request.priority_nutrients
                )
                if nutrient_matches:
                    outlet["nutrient_match"] = nutrient_matches
                    outlet["recommendation"] = f"Good for: {', '.join(nutrient_matches)}"
            
            outlets.append(outlet)

        result = {
            "outlets": outlets,
            "count": len(outlets),
            "search_radius_meters": request.radius,
        }
        
        # Add personalized recommendations if nutrients provided
        if food_recs:
            result["nutrient_recommendations"] = food_recs
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/nutrient-food-tips",
    summary="Get food tips for specific nutrients",
    description="Get suggestions for what types of food outlets to visit based on nutrients you need.",
)
async def get_nutrient_food_tips(
    nutrients: str = Query(..., description="Comma-separated list of nutrients (e.g., 'iron,calcium,protein')")
):
    """Get food recommendations based on nutrients."""
    nutrient_list = [n.strip() for n in nutrients.split(",")]
    recommendations = get_food_recommendations(nutrient_list)
    
    return {
        "nutrients": nutrient_list,
        "recommendations": recommendations
    }
