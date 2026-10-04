from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Priority(str, Enum):
    LOW = "LOW"; MEDIUM = "MEDIUM"; HIGH = "HIGH"; CRITICAL = "CRITICAL"


class IncidentType(str, Enum):
    ACCIDENT = "Accident"; MEDICAL = "Medical Emergency"; FIRE = "Fire"; INJURY = "Injury"
    UNCONSCIOUS = "Unconscious Person"; CARDIAC = "Cardiac Emergency"
    BREATHING = "Breathing Problem"; OTHER = "Other"


class AmbulanceStatus(str, Enum):
    SEARCHING = "SEARCHING"; REQUESTED = "REQUESTED"; ASSIGNED = "ASSIGNED"
    EN_ROUTE = "EN_ROUTE"; ARRIVED = "ARRIVED"; COMPLETED = "COMPLETED"; UNAVAILABLE = "UNAVAILABLE"


class HospitalStatus(str, Enum):
    SEARCHING = "SEARCHING"; REQUESTED = "REQUESTED"; PENDING = "PENDING"; ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"; READY = "READY"; ARRIVED = "ARRIVED"; COMPLETED = "COMPLETED"


class EmergencyStatus(str, Enum):
    ACTIVE = "ACTIVE"; RESOLVED = "RESOLVED"; CANCELLED = "CANCELLED"


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=130)
    blood_group: Optional[str] = Field(None, max_length=5)
    address: Optional[str] = None

    @field_validator("password")
    @classmethod
    def strong(cls, v):
        if not (any(c.isalpha() for c in v) and any(c.isdigit() for c in v)):
            raise ValueError("Password must contain letters and digits")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORM):
    id: int; email: EmailStr; full_name: str
    phone: Optional[str] = None; age: Optional[int] = None
    blood_group: Optional[str] = None; address: Optional[str] = None
    allergies: Optional[str] = None; medical_notes: Optional[str] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ContactIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    relationship: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    priority: int = Field(1, ge=1, le=10)
    is_primary: bool = False


class ContactOut(ORM):
    id: int; name: str; relationship: Optional[str] = None
    phone: Optional[str] = None; email: Optional[str] = None
    priority: int; is_primary: bool


class EmergencyIn(BaseModel):
    incident_type: IncidentType
    patient_name: Optional[str] = None      # defaults to the logged-in user
    patient_age: Optional[int] = Field(None, ge=0, le=130)
    blood_group: Optional[str] = None
    condition: Optional[str] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None
    location_text: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    priority: Priority = Priority.HIGH


class EmergencyPatch(BaseModel):
    condition: Optional[str] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None
    location_text: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    priority: Optional[Priority] = None
    status: Optional[EmergencyStatus] = None


class TimelineOut(ORM):
    id: int; event: str; actor: Optional[str] = None
    status: Optional[str] = None; created_at: datetime


class NotificationOut(ORM):
    id: int; type: str; channel: str; recipient: Optional[str] = None
    status: str; error: Optional[str] = None; attempts: int
    is_read: bool; created_at: datetime


class AmbulanceOut(ORM):
    status: str; provider: Optional[str] = None; eta_minutes: Optional[int] = None
    notes: Optional[str] = None; requested_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None


class HospitalOut(ORM):
    status: str; facility_id: Optional[int] = None; notes: Optional[str] = None


class EmergencyOut(ORM):
    id: int; code: str; incident_type: str; patient_name: str
    patient_age: Optional[int] = None; blood_group: Optional[str] = None
    condition: Optional[str] = None; symptoms: Optional[str] = None; notes: Optional[str] = None
    location_text: Optional[str] = None; latitude: Optional[float] = None
    longitude: Optional[float] = None; priority: str; status: str
    created_at: datetime; resolved_at: Optional[datetime] = None
    ambulance: Optional[AmbulanceOut] = None
    hospital: Optional[HospitalOut] = None


class CoordinationIn(BaseModel):
    ambulance_status: Optional[AmbulanceStatus] = None
    ambulance_provider: Optional[str] = None
    ambulance_eta_minutes: Optional[int] = Field(None, ge=0)
    hospital_status: Optional[HospitalStatus] = None
    facility_id: Optional[int] = None
    notes: Optional[str] = None


class FacilityOut(ORM):
    id: int; name: str; type: str; city: Optional[str] = None
    address: Optional[str] = None; phone: Optional[str] = None
    latitude: float; longitude: float
    emergency_available: bool; ambulance_available: bool; blood_available: bool
    is_demo: bool
    distance_km: Optional[float] = None
