import math

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/places", tags=["places"])

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": "MediBridge/1.0 (educational healthcare coordination project)"
}


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance in kilometres."""
    earth_radius = 6371.0

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(p1) * math.cos(p2)
        * math.sin(delta_lon / 2) ** 2
    )

    return 2 * earth_radius * math.asin(math.sqrt(a))


@router.get("/hospitals")
async def nearby_hospitals(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: int = Query(5, ge=5, le=20),
):
    radius_m = radius_km * 1000

    query = f"""
    [out:json][timeout:25];
    (
      nwr["amenity"="hospital"](around:{radius_m},{lat},{lon});
      nwr["healthcare"="hospital"](around:{radius_m},{lat},{lon});
    );
    out center tags;
    """

    try:
        async with httpx.AsyncClient(timeout=35.0, headers=HEADERS) as client:
            response = await client.post(
                OVERPASS_URL,
                data={"data": query},
            )
            response.raise_for_status()
            payload = response.json()

    except (httpx.HTTPError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="Hospital map data is temporarily unavailable. Please try again later.",
        )

    hospitals = []
    seen = set()

    for item in payload.get("elements", []):
        tags = item.get("tags", {})
        name = tags.get("name") or tags.get("name:en")

        # Do not invent names for unnamed map entries.
        if not name:
            continue

        item_key = f"{item.get('type')}:{item.get('id')}"
        if item_key in seen:
            continue
        seen.add(item_key)

        center = item.get("center", {})
        hospital_lat = item.get("lat", center.get("lat"))
        hospital_lon = item.get("lon", center.get("lon"))

        if hospital_lat is None or hospital_lon is None:
            continue

        distance = calculate_distance(
            lat, lon, hospital_lat, hospital_lon
        )

        if distance > radius_km:
            continue

        address_parts = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:suburb"),
            tags.get("addr:city"),
            tags.get("addr:postcode"),
        ]
        address = ", ".join(str(x) for x in address_parts if x)

        phone = (
            tags.get("phone")
            or tags.get("contact:phone")
            or None
        )

        hospitals.append({
            "osm_type": item.get("type"),
            "osm_id": item.get("id"),
            "name": name,
            "latitude": hospital_lat,
            "longitude": hospital_lon,
            "distance_km": round(distance, 2),
            "address": address or None,
            "phone": phone,
            "website": tags.get("website") or tags.get("contact:website"),
            "emergency_tag": tags.get("emergency"),
            "source": "OpenStreetMap",
        })

    hospitals.sort(key=lambda x: x["distance_km"])

    return {
        "count": len(hospitals),
        "radius_km": radius_km,
        "origin": {"latitude": lat, "longitude": lon},
        "source": "OpenStreetMap",
        "notice": (
            "Map information may be incomplete or outdated. "
            "Hospital availability, emergency capacity and services "
            "have not been independently verified."
        ),
        "hospitals": hospitals[:100],
    }


@router.get("/geocode")
async def search_location(
    q: str = Query(..., min_length=2, max_length=180),
):
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
            response = await client.get(
                NOMINATIM_URL,
                params={
                    "q": q,
                    "format": "jsonv2",
                    "limit": 5,
                    "addressdetails": 1,
                },
            )
            response.raise_for_status()
            results = response.json()

    except (httpx.HTTPError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="Location search is temporarily unavailable.",
        )

    return {
        "results": [
            {
                "name": item.get("display_name"),
                "latitude": float(item["lat"]),
                "longitude": float(item["lon"]),
            }
            for item in results
            if item.get("lat") and item.get("lon")
        ]
    }