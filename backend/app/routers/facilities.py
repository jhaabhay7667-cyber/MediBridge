from math import asin, cos, radians, sin, sqrt
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..auth import current_user
from ..database import get_db
from ..models import Facility
from ..schemas import FacilityOut

router = APIRouter(prefix="/api/facilities", tags=["facilities"], dependencies=[Depends(current_user)])


def haversine_km(lat1, lon1, lat2, lon2):
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


def _nearby(db, lat, lon, radius_km, type_, emergency_only, city=None):
    q = db.query(Facility)
    if type_: q = q.filter(Facility.type.ilike(type_))
    if city: q = q.filter(Facility.city.ilike(city))
    if emergency_only: q = q.filter(Facility.emergency_available.is_(True))
    out = []
    for f in q.all():
        d = haversine_km(lat, lon, f.latitude, f.longitude)
        if d <= radius_km:
            item = FacilityOut.model_validate(f); item.distance_km = round(d, 2); out.append(item)
    return sorted(out, key=lambda x: x.distance_km)


@router.get("", response_model=list[FacilityOut])
def list_facilities(type: Optional[str] = None, city: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Facility)
    if type: q = q.filter(Facility.type.ilike(type))
    if city: q = q.filter(Facility.city.ilike(city))
    return q.order_by(Facility.name).all()


@router.get("/nearby", response_model=list[FacilityOut])
def nearby(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
           radius_km: float = Query(25, gt=0, le=500), db: Session = Depends(get_db)):
    return _nearby(db, lat, lon, radius_km, None, False)


@router.get("/nearby/search", response_model=list[FacilityOut])
def nearby_search(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
                  radius_km: float = Query(25, gt=0, le=500), type: Optional[str] = None,
                  city: Optional[str] = None, emergency_only: bool = False,
                  db: Session = Depends(get_db)):
    return _nearby(db, lat, lon, radius_km, type, emergency_only, city)
