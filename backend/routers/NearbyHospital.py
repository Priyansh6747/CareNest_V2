import os
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

load_dotenv()

locRouter = APIRouter()


@locRouter.get("/")
async def read_root():
    return {"message": "Welcome to FastAPI!"}



class Location(BaseModel):
    lat: float
    lng: float
    radius: Optional[int] = 5000  # meters
    limit: Optional[int] = 5


@locRouter.post("/nearby-hospitals")
def find_hospitals(location: Location):
    """Find nearby hospitals using Geoapify"""
    api_key = os.getenv("GEOAPIFY_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key not configured")

    try:
        # Make request to Geoapify
        url = "https://api.geoapify.com/v2/places"
        params = {
            "categories": "healthcare.hospital",
            "filter": f"circle:{location.lng},{location.lat},{location.radius}",
            "limit": location.limit,
            "apiKey": api_key
        }

        response = requests.get(url, params=params)
        data = response.json()


        # Process results
        hospitals = []
        for place in data.get("features", []):
            props = place.get("properties", {})
            hospitals.append({
                "name": props.get("name", "Hospital"),
                "address": props.get("formatted", ""),
                "location": {
                    "lat": place["geometry"]["coordinates"][1],
                    "lng": place["geometry"]["coordinates"][0]
                },
                # Omit distance if it's not part of the response
                # Add more relevant fields based on the actual response
            })

        return {"hospitals": hospitals}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
