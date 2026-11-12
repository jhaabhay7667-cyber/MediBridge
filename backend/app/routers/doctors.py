
import math
import re
import httpx

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import current_user
from ..models import User


router = APIRouter(
    prefix="/api/doctors",
    tags=["Doctor Finder"]
)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

SPECIALTY_ALIASES = {
    "general": [
        "general", "general practice", "general practitioner",
        "family medicine", "primary care", "physician", "gp"
    ],
    "cardiology": ["cardiology", "cardiologist"],
    "dermatology": ["dermatology", "dermatologist", "skin"],
    "neurology": ["neurology", "neurologist"],
    "orthopedics": [
        "orthopedic", "orthopaedic", "orthopedics",
        "orthopaedics"
    ],
    "pediatrics": [
        "pediatrics", "paediatrics", "pediatric",
        "paediatric", "child"
    ],
    "gynecology": [
        "gynecology", "gynaecology", "obstetrics",
        "gynecologist", "gynaecologist"
    ],
    "ent": [
        "otorhinolaryngology", "otolaryngology",
        "ear nose throat", "ent"
    ],
}


def distance_km(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance using the Haversine formula."""

    earth_radius = 6371.0

    lat1, lon1, lat2, lon2 = map(
        math.radians,
        [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * earth_radius * math.asin(
        math.sqrt(min(1, value))
    )


def safe_external_url(value):
    if not value:
        return None

    value = str(value).strip()

    if not value:
        return None

    if not re.match(r"^https?://", value, re.IGNORECASE):
        value = "https://" + value

    if re.match(r"^https?://[^/\s]+", value, re.IGNORECASE):
        return value

    return None


def get_element_coordinates(element):
    if element.get("lat") is not None and element.get("lon") is not None:
        return element["lat"], element["lon"]

    center = element.get("center") or {}

    if center.get("lat") is not None and center.get("lon") is not None:
        return center["lat"], center["lon"]

    return None, None


def get_address(tags):
    address_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city") or tags.get("addr:town"),
        tags.get("addr:state"),
        tags.get("addr:postcode"),
        tags.get("addr:country"),
    ]

    parts = [
        str(part).strip()
        for part in address_parts
        if part and str(part).strip()
    ]

    return ", ".join(dict.fromkeys(parts)) or None


def matches_specialty(tags, specialty):
    if specialty == "any":
        return True

    aliases = SPECIALTY_ALIASES.get(specialty)

    if not aliases:
        return False

    specialty_text = " ".join(
        str(tags.get(key, ""))
        for key in (
            "healthcare:speciality",
            "healthcare:specialty",
            "speciality",
            "specialty",
            "medical_specialty",
        )
    ).lower()

    return any(alias in specialty_text for alias in aliases)


def serialize_doctor(element, user_lat, user_lon):
    tags = element.get("tags") or {}

    lat, lon = get_element_coordinates(element)

    if lat is None or lon is None:
        return None

    raw_name = tags.get("name")
    doctor_name = (
        tags.get("doctor:name")
        or tags.get("contact:person")
        or None
    )

    phone = (
        tags.get("contact:phone")
        or tags.get("phone")
        or tags.get("telephone")
    )

    website = safe_external_url(
        tags.get("contact:website")
        or tags.get("website")
    )

    appointment_url = safe_external_url(
        tags.get("contact:booking")
        or tags.get("booking:website")
        or tags.get("appointment")
    )

    specialty = (
        tags.get("healthcare:speciality")
        or tags.get("healthcare:specialty")
        or tags.get("speciality")
        or tags.get("specialty")
        or None
    )

    listing_type = (
        tags.get("healthcare")
        or tags.get("amenity")
        or "healthcare"
    )

    element_type = element.get("type")
    element_id = element.get("id")

    return {
        "id": f"{element_type}-{element_id}",
        "name": raw_name,
        "doctor_name": doctor_name,
        "specialty": specialty,
        "listing_type": listing_type,
        "address": get_address(tags),
        "phone": phone,
        "website": website,
        "appointment_url": appointment_url,
        "latitude": lat,
        "longitude": lon,
        "distance_km": round(
            distance_km(user_lat, user_lon, lat, lon),
            2
        ),
        "source": "OpenStreetMap",
        "source_url": (
            f"https://www.openstreetmap.org/"
            f"{element_type}/{element_id}"
        ),
    }


@router.get("/search")
async def search_doctors(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: int = Query(default=10, ge=5, le=20),
    specialty: str = Query(default="any", max_length=40),
    user: User = Depends(current_user),
):
    allowed_radii = {5, 10, 15, 20}

    if radius_km not in allowed_radii:
        raise HTTPException(
            status_code=422,
            detail="Radius must be 5, 10, 15, or 20 km"
        )

    specialty = specialty.strip().lower()

    if specialty not in ("any", *SPECIALTY_ALIASES.keys()):
        raise HTTPException(
            status_code=422,
            detail="Unsupported specialty filter"
        )

    radius_meters = radius_km * 1000

    query = f"""
    [out:json][timeout:25];
    (
      nwr(around:{radius_meters},{lat},{lon})
        ["healthcare"~"^(doctor|clinic)$"];

      nwr(around:{radius_meters},{lat},{lon})
        ["amenity"~"^(doctors|clinic)$"];
    );
    out center tags;
    """

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "MediBridge-DoctorFinder/1.0"
            }
        ) as client:
            response = await client.post(
                OVERPASS_URL,
                data={"data": query}
            )

            response.raise_for_status()
            payload = response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Doctor search timed out. Please try again."
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="The healthcare listings service is temporarily unavailable."
        )

    except (httpx.RequestError, ValueError):
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve healthcare listings right now."
        )

    results = []
    seen_ids = set()

    for element in payload.get("elements", []):
        element_id = (
            element.get("type"),
            element.get("id")
        )

        if element_id in seen_ids:
            continue

        seen_ids.add(element_id)

        tags = element.get("tags") or {}

        if not matches_specialty(tags, specialty):
            continue

        item = serialize_doctor(
            element,
            lat,
            lon
        )

        if not item:
            continue

        if item["distance_km"] > radius_km:
            continue

        results.append(item)

    results.sort(
        key=lambda item: item["distance_km"]
    )

    return {
        "count": len(results),
        "radius_km": radius_km,
        "specialty": specialty,
        "results": results,
        "source": "OpenStreetMap",
        "notice": (
            "Listings are community-maintained. "
            "Doctor registration, qualifications, appointment "
            "availability and clinical services are not verified "
            "by MediBridge."
        )
    }
