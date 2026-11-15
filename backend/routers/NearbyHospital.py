import math
import os
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

load_dotenv()

locRouter = APIRouter()

# Free, keyless OpenStreetMap endpoint used when GEOAPIFY_API_KEY is absent.
OVERPASS_URL = os.getenv("OVERPASS_API_URL", "https://overpass-api.de/api/interpreter")


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in kilometres."""
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def _find_hospitals_overpass(location: "Location"):
    """
    Query OpenStreetMap directly. No API key required, so nearby hospitals
    keep working before a Geoapify account is configured.
    """
    radius = int(location.radius or 5000)
    # Cap the returned elements; unbounded queries can be slow and time out.
    max_results = max(int(location.limit or 5) * 6, 30)
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:{radius},{location.lat},{location.lng});
      way["amenity"="hospital"](around:{radius},{location.lat},{location.lng});
      node["amenity"="clinic"](around:{radius},{location.lat},{location.lng});
      way["amenity"="clinic"](around:{radius},{location.lat},{location.lng});
    );
    out center tags {max_results};
    """

    response = requests.post(
        OVERPASS_URL,
        data={"data": query},
        # Overpass rejects requests without an identifying User-Agent (406).
        headers={
            "User-Agent": "CareNest/2.0 (maternal health app)",
            "Accept": "application/json",
        },
        timeout=45,
    )
    response.raise_for_status()
    elements = response.json().get("elements", [])

    hospitals = []
    for element in elements:
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        lat = element.get("lat") or element.get("center", {}).get("lat")
        lng = element.get("lon") or element.get("center", {}).get("lon")
        if lat is None or lng is None:
            continue

        address = ", ".join(
            part for part in [
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:city"),
            ] if part
        )

        hospitals.append({
            "name": name,
            "address": address or tags.get("addr:full", "") or "Address not listed",
            "location": {"lat": lat, "lng": lng},
            "distance_km": round(_haversine_km(location.lat, location.lng, lat, lng), 2),
            "type": tags.get("amenity", "hospital"),
        })

    hospitals.sort(key=lambda h: h["distance_km"])
    return hospitals[: (location.limit or 5)]


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
    """Find nearby hospitals using Geoapify, falling back to OpenStreetMap."""
    api_key = os.getenv("GEOAPIFY_API_KEY")

    if not api_key:
        try:
            return {"hospitals": _find_hospitals_overpass(location), "source": "openstreetmap"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=(
                    "No GEOAPIFY_API_KEY configured and the OpenStreetMap fallback "
                    f"failed ({e}). Add a free key from https://myprojects.geoapify.com"
                ),
            )

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
