Directory structure:
└── jhaabhay7667-cyber-medibridge/
    ├── README.md
    ├── render.yaml
    ├── backend/
    │   ├── requirements-prod.txt
    │   ├── requirements.txt
    │   ├── .env.example
    │   ├── app/
    │   │   ├── __init__.py
    │   │   ├── auth.py
    │   │   ├── database.py
    │   │   ├── main.py
    │   │   ├── models.py
    │   │   ├── schemas.py
    │   │   ├── seed_facilities.py
    │   │   ├── routers/
    │   │   │   ├── __init__.py
    │   │   │   ├── auth.py
    │   │   │   ├── contacts.py
    │   │   │   ├── emergencies.py
    │   │   │   └── facilities.py
    │   │   └── services/
    │   │       ├── __init__.py
    │   │       └── notify.py
    │   └── tests/
    │       ├── __init__.py
    │       ├── conftest.py
    │       └── test_api.py
    └── frontend/
        ├── app.js
        ├── auth.js
        ├── config.js
        ├── contacts.html
        ├── contacts.js
        ├── dashboard.html
        ├── dashboard.js
        ├── emergency.html
        ├── emergency.js
        ├── facilities.html
        ├── facilities.js
        ├── history.html
        ├── history.js
        ├── index.html
        ├── login.html
        ├── register.html
        └── style.css


Files Content:

================================================
FILE: README.md
================================================
# MediBridge — Emergency Coordination Platform

Phase 1 (backend core). Coordination and information only; it does not contact government
emergency services, dispatch ambulances, or provide medical advice. Seeded facilities are
**demo data**, not verified live availability.

## Run (Windows PowerShell)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then set SECRET_KEY (and SMTP_* for real email)
python -m app.seed_facilities
uvicorn app.main:app --reload
pytest
```
Swagger docs: http://127.0.0.1:8000/docs

## Render
Build: `pip install -r requirements.txt` — Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
Set SECRET_KEY, DATABASE_URL (PostgreSQL), CORS_ORIGINS (your Netlify URL), FRONTEND_URL, SMTP_*.

## Status
Done: auth, emergencies + timeline, contacts, facilities (haversine search), SMTP notify with
per-contact status/retry, ambulance/hospital coordination, tests.
Frontend (Phase 2): login/register, dashboard with press-and-hold SOS, emergency page (contacts, email alerts,
ambulance/hospital status, nearby facilities, timeline, print/PDF), contacts, facilities search, history filters,
light/dark theme, English/Hindi/Bengali nav and safety text.
Not yet: profile page, AI layer, rate limiting, full string translation, PWA, in-app notification center page.

## Frontend
```powershell
cd frontend
python -m http.server 5500
```
Open http://localhost:5500/login.html. For production set `API_BASE` in `frontend/config.js` to your Render URL,
deploy `frontend/` to Netlify, and add the Netlify URL to `CORS_ORIGINS` on Render.



================================================
FILE: render.yaml
================================================
services:
  - type: web
    name: medibridge-api
    runtime: python
    plan: free
    rootDir: backend
    buildCommand: pip install -r requirements-prod.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/health
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.7
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase: {name: medibridge-db, property: connectionString}
      - key: CORS_ORIGINS
        sync: false
      - key: FRONTEND_URL
        sync: false
      - key: BREVO_API_KEY
        sync: false
      - key: SMTP_FROM_EMAIL
        sync: false
      - key: SMTP_FROM_NAME
        value: MediBridge Emergency Coordination
databases:
  - name: medibridge-db
    plan: free



================================================
FILE: backend/requirements-prod.txt
================================================
-r requirements.txt
psycopg2-binary>=2.9.11



================================================
FILE: backend/requirements.txt
================================================
fastapi>=0.115
uvicorn[standard]>=0.30
sqlalchemy>=2.0.43
pydantic[email]>=2.12
PyJWT>=2.9
python-dotenv>=1.0
pytest>=8.3
httpx>=0.27



================================================
FILE: backend/.env.example
================================================
SECRET_KEY=change-me-to-a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=sqlite:///./medibridge.db
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
FRONTEND_URL=http://localhost:5500

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=MediBridge Emergency Coordination

# Free-hosting email (Render free blocks SMTP). Brevo HTTPS API; SMTP_FROM_EMAIL must be a verified Brevo sender.
BREVO_API_KEY=



================================================
FILE: backend/app/__init__.py
================================================
[Empty file]


================================================
FILE: backend/app/auth.py
================================================
import hashlib, hmac, os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

ALGO = "HS256"
bearer = HTTPBearer(auto_error=False)


def _secret() -> str:
    key = os.getenv("SECRET_KEY")
    if not key:
        raise RuntimeError("SECRET_KEY environment variable is not set")
    return key


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200_000)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except ValueError:
        return False


def create_token(user_id: int) -> str:
    minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode({"sub": str(user_id), "exp": exp}, _secret(), algorithm=ALGO)


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer),
                 db: Session = Depends(get_db)) -> User:
    unauthorized = HTTPException(401, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    if creds is None:
        raise unauthorized
    try:
        payload = jwt.decode(creds.credentials, _secret(), algorithms=[ALGO])
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized
    if user is None:
        raise unauthorized
    return user



================================================
FILE: backend/app/database.py
================================================
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medibridge.db")

# Render gives postgres:// ; force the psycopg2 driver that requirements-prod.txt installs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL[len("postgresql://"):]

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


================================================
FILE: backend/app/main.py
================================================
import logging, os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .database import Base, engine
from . import models  # noqa: F401
from .routers import auth, contacts, emergencies, facilities

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("medibridge")
Base.metadata.create_all(bind=engine)
try:  # idempotent demo-facility seed so a fresh database is usable
    from .seed_facilities import run as _seed
    _seed()
except Exception:  # noqa: BLE001
    log.exception("Demo seed failed")

app = FastAPI(title="MediBridge API", description="Emergency coordination platform. "
              "Informational/coordination use only; not a substitute for emergency services.")
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5500").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, contacts.router, emergencies.router, facilities.router):
    app.include_router(r)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}



================================================
FILE: backend/app/models.py
================================================
from datetime import datetime, timezone
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship
from .database import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    phone = Column(String(30))
    age = Column(Integer)
    blood_group = Column(String(5))
    address = Column(String(255))
    allergies = Column(Text)
    medical_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=now)
    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
    emergencies = relationship("Emergency", back_populates="user", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(120), nullable=False)
    relationship_ = Column("relationship", String(60))
    phone = Column(String(30))
    email = Column(String(255))
    priority = Column(Integer, default=1)
    is_primary = Column(Boolean, default=False)
    user = relationship("User", back_populates="contacts")


class Emergency(Base):
    __tablename__ = "emergencies"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, index=True)  # e.g. MB-2026-001
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    incident_type = Column(String(40), nullable=False)
    patient_name = Column(String(120), nullable=False)
    patient_age = Column(Integer)
    blood_group = Column(String(5))
    condition = Column(String(255))
    symptoms = Column(Text)
    notes = Column(Text)
    location_text = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    priority = Column(String(10), default="HIGH")
    status = Column(String(20), default="ACTIVE")  # ACTIVE / RESOLVED / CANCELLED
    created_at = Column(DateTime(timezone=True), default=now)
    resolved_at = Column(DateTime(timezone=True))
    user = relationship("User", back_populates="emergencies")
    timeline = relationship("TimelineEvent", back_populates="emergency",
                            cascade="all, delete-orphan", order_by="TimelineEvent.id")
    notifications = relationship("Notification", back_populates="emergency",
                                 cascade="all, delete-orphan", order_by="Notification.id")
    ambulance = relationship("AmbulanceRequest", uselist=False, back_populates="emergency",
                             cascade="all, delete-orphan")
    hospital = relationship("HospitalCoordination", uselist=False, back_populates="emergency",
                            cascade="all, delete-orphan")


class Facility(Base):
    __tablename__ = "facilities"
    id = Column(Integer, primary_key=True)
    name = Column(String(160), nullable=False, unique=True)
    type = Column(String(40), nullable=False)
    city = Column(String(80))
    address = Column(String(255))
    phone = Column(String(30))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    emergency_available = Column(Boolean, default=False)
    ambulance_available = Column(Boolean, default=False)
    blood_available = Column(Boolean, default=False)
    is_demo = Column(Boolean, default=True)  # seeded data is NOT verified live availability


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    emergency_id = Column(Integer, ForeignKey("emergencies.id"), index=True, nullable=False)
    type = Column(String(40), nullable=False)
    channel = Column(String(20), default="EMAIL")
    recipient = Column(String(255))
    contact_id = Column(Integer)
    status = Column(String(20), nullable=False)  # SENT / FAILED
    error = Column(Text)
    attempts = Column(Integer, default=1)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=now)
    emergency = relationship("Emergency", back_populates="notifications")


class TimelineEvent(Base):
    __tablename__ = "timeline"
    id = Column(Integer, primary_key=True)
    emergency_id = Column(Integer, ForeignKey("emergencies.id"), index=True, nullable=False)
    event = Column(String(255), nullable=False)
    actor = Column(String(80), default="system")
    status = Column(String(30))
    created_at = Column(DateTime(timezone=True), default=now)
    emergency = relationship("Emergency", back_populates="timeline")


class AmbulanceRequest(Base):
    __tablename__ = "ambulance_requests"
    id = Column(Integer, primary_key=True)
    emergency_id = Column(Integer, ForeignKey("emergencies.id"), unique=True, nullable=False)
    status = Column(String(20), default="SEARCHING")
    provider = Column(String(120))
    eta_minutes = Column(Integer)
    notes = Column(Text)
    requested_at = Column(DateTime(timezone=True))
    assigned_at = Column(DateTime(timezone=True))
    emergency = relationship("Emergency", back_populates="ambulance")


class HospitalCoordination(Base):
    __tablename__ = "hospital_coordination"
    id = Column(Integer, primary_key=True)
    emergency_id = Column(Integer, ForeignKey("emergencies.id"), unique=True, nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"))
    status = Column(String(20), default="SEARCHING")
    notes = Column(Text)
    updated_at = Column(DateTime(timezone=True), default=now, onupdate=now)
    emergency = relationship("Emergency", back_populates="hospital")
    facility = relationship("Facility")



================================================
FILE: backend/app/schemas.py
================================================
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



================================================
FILE: backend/app/seed_facilities.py
================================================
"""Idempotent seed of DEMO facilities. Not verified; not live availability."""
from .database import Base, SessionLocal, engine
from .models import Facility

DEMO = [
    ("Demo General Hospital (Kolkata)", "Hospital", "Kolkata", "Demo address, Kolkata", "000-000-0001", 22.5726, 88.3639, True, True, True),
    ("Demo Emergency Medical Center", "Emergency Medical Center", "Kolkata", "Demo address, Kolkata", "000-000-0002", 22.5448, 88.3426, True, False, False),
    ("Demo Ambulance Service", "Ambulance Service", "Kolkata", "Demo address, Kolkata", "000-000-0003", 22.5958, 88.2636, False, True, False),
    ("Demo Blood Bank", "Blood Bank", "Kolkata", "Demo address, Kolkata", "000-000-0004", 22.5675, 88.3700, False, False, True),
    ("Demo Community Clinic", "Clinic", "Kolkata", "Demo address, Kolkata", "000-000-0005", 22.5100, 88.3500, False, False, False),
]


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    added = 0
    for n, t, c, a, p, la, lo, e, am, b in DEMO:
        if not db.query(Facility).filter(Facility.name == n).first():
            db.add(Facility(name=n, type=t, city=c, address=a, phone=p, latitude=la, longitude=lo,
                            emergency_available=e, ambulance_available=am, blood_available=b, is_demo=True))
            added += 1
    db.commit(); db.close()
    print(f"Seeded {added} demo facilities (labelled is_demo=True).")


if __name__ == "__main__":
    run()



================================================
FILE: backend/app/routers/__init__.py
================================================
[Empty file]


================================================
FILE: backend/app/routers/auth.py
================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..auth import create_token, current_user, hash_password, verify_password
from ..database import get_db
from ..models import User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists")
    user = User(email=email, password_hash=hash_password(data.password),
                **data.model_dump(exclude={"email", "password"}))
    db.add(user); db.commit(); db.refresh(user)
    return TokenOut(access_token=create_token(user.id), user=user)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return TokenOut(access_token=create_token(user.id), user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user



================================================
FILE: backend/app/routers/contacts.py
================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..auth import current_user
from ..database import get_db
from ..models import Contact, User
from ..schemas import ContactIn, ContactOut

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


def _own(db, user, cid):
    c = db.query(Contact).filter(Contact.id == cid, Contact.user_id == user.id).first()
    if not c:
        raise HTTPException(404, "Contact not found")
    return c


def _single_primary(db, user, keep_id):
    db.query(Contact).filter(Contact.user_id == user.id, Contact.id != keep_id).update({"is_primary": False})


@router.get("", response_model=list[ContactOut])
def list_contacts(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.query(Contact).filter(Contact.user_id == user.id).order_by(Contact.priority).all()


@router.post("", response_model=ContactOut, status_code=201)
def add_contact(data: ContactIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not data.phone and not data.email:
        raise HTTPException(422, "Provide a phone number or an email")
    c = Contact(user_id=user.id, name=data.name, relationship_=data.relationship, phone=data.phone,
                email=data.email, priority=data.priority, is_primary=data.is_primary)
    db.add(c); db.flush()
    if c.is_primary:
        _single_primary(db, user, c.id)
    db.commit(); db.refresh(c)
    return ContactOut(id=c.id, name=c.name, relationship=c.relationship_, phone=c.phone,
                      email=c.email, priority=c.priority, is_primary=c.is_primary)


@router.put("/{cid}", response_model=ContactOut)
def update_contact(cid: int, data: ContactIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = _own(db, user, cid)
    c.name, c.relationship_, c.phone, c.email = data.name, data.relationship, data.phone, data.email
    c.priority, c.is_primary = data.priority, data.is_primary
    if c.is_primary:
        _single_primary(db, user, c.id)
    db.commit(); db.refresh(c)
    return ContactOut(id=c.id, name=c.name, relationship=c.relationship_, phone=c.phone,
                      email=c.email, priority=c.priority, is_primary=c.is_primary)


@router.delete("/{cid}", status_code=204)
def delete_contact(cid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    db.delete(_own(db, user, cid)); db.commit()



================================================
FILE: backend/app/routers/emergencies.py
================================================
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..auth import current_user
from ..database import get_db
from ..models import (AmbulanceRequest, Contact, Emergency, Facility, HospitalCoordination,
                      Notification, TimelineEvent, User)
from ..schemas import (CoordinationIn, EmergencyIn, EmergencyOut, EmergencyPatch,
                       NotificationOut, TimelineOut)
from ..services.notify import send_email

router = APIRouter(prefix="/api/emergencies", tags=["emergencies"])


def _own(db: Session, user: User, eid: int) -> Emergency:
    em = db.query(Emergency).filter(Emergency.id == eid, Emergency.user_id == user.id).first()
    if not em:  # 404 (not 403) so other users' record IDs are not revealed
        raise HTTPException(404, "Emergency not found")
    return em


def _log(db, em, event, status=None, actor="system"):
    db.add(TimelineEvent(emergency_id=em.id, event=event, status=status, actor=actor))


def _next_code(db) -> str:
    year = datetime.now(timezone.utc).year
    n = db.query(Emergency).filter(Emergency.code.like(f"MB-{year}-%")).count() + 1
    return f"MB-{year}-{n:03d}"


@router.post("", response_model=EmergencyOut, status_code=201)
def create(data: EmergencyIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    em = Emergency(
        code=_next_code(db), user_id=user.id, incident_type=data.incident_type.value,
        patient_name=data.patient_name or user.full_name,
        patient_age=data.patient_age if data.patient_age is not None else user.age,
        blood_group=data.blood_group or user.blood_group,
        condition=data.condition, symptoms=data.symptoms, notes=data.notes,
        location_text=data.location_text, latitude=data.latitude, longitude=data.longitude,
        priority=data.priority.value)
    db.add(em); db.flush()
    em.ambulance = AmbulanceRequest(status="SEARCHING")
    em.hospital = HospitalCoordination(status="SEARCHING")
    _log(db, em, "Emergency created", "ACTIVE", user.full_name)
    if em.latitude is not None and em.longitude is not None:
        _log(db, em, "Location captured", "OK")
    db.add(Notification(emergency_id=em.id, type="EMERGENCY_CREATED", channel="IN_APP", status="SENT"))
    db.commit(); db.refresh(em)
    return em


@router.get("", response_model=list[EmergencyOut])
def list_(status: str | None = None, priority: str | None = None, incident_type: str | None = None,
          code: str | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = db.query(Emergency).filter(Emergency.user_id == user.id)
    if status: q = q.filter(Emergency.status == status.upper())
    if priority: q = q.filter(Emergency.priority == priority.upper())
    if incident_type: q = q.filter(Emergency.incident_type == incident_type)
    if code: q = q.filter(Emergency.code.ilike(f"%{code}%"))
    return q.order_by(Emergency.id.desc()).all()


@router.get("/{eid}", response_model=EmergencyOut)
def get(eid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _own(db, user, eid)


@router.patch("/{eid}", response_model=EmergencyOut)
def patch(eid: int, data: EmergencyPatch, db: Session = Depends(get_db), user: User = Depends(current_user)):
    em = _own(db, user, eid)
    changes = data.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(em, k, v.value if hasattr(v, "value") else v)
    if "status" in changes:
        if em.status == "RESOLVED":
            em.resolved_at = datetime.now(timezone.utc)
            db.add(Notification(emergency_id=em.id, type="EMERGENCY_RESOLVED", channel="IN_APP", status="SENT"))
        _log(db, em, f"Emergency status set to {em.status}", em.status, user.full_name)
    else:
        _log(db, em, "Emergency details updated", None, user.full_name)
    db.commit(); db.refresh(em)
    return em


@router.delete("/{eid}", status_code=204)
def delete(eid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    db.delete(_own(db, user, eid)); db.commit()


@router.post("/{eid}/notify")
def notify(eid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    em = _own(db, user, eid)
    contacts = (db.query(Contact).filter(Contact.user_id == user.id, Contact.email.isnot(None))
                .order_by(Contact.priority).all())
    if not contacts:
        raise HTTPException(400, "No trusted contacts with an email address. Add one first.")
    _log(db, em, "Family notification initiated", "PENDING", user.full_name)
    results = []
    for c in contacts:
        ok, err, attempts = send_email(em, c.email)
        db.add(Notification(emergency_id=em.id, type="FAMILY_NOTIFIED" if ok else "FAMILY_NOTIFICATION_FAILED",
                            channel="EMAIL", recipient=c.email, contact_id=c.id,
                            status="SENT" if ok else "FAILED", error=err, attempts=attempts))
        _log(db, em, f"Email {'sent to' if ok else 'FAILED for'} {c.name}", "SENT" if ok else "FAILED")
        results.append({"contact": c.name, "email": c.email, "status": "SENT" if ok else "FAILED", "error": err})
    db.commit()
    if not any(r["status"] == "SENT" for r in results):
        raise HTTPException(502, {"message": "No notification could be delivered", "results": results})
    return {"results": results}


@router.get("/{eid}/notifications", response_model=list[NotificationOut])
def notifications(eid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _own(db, user, eid).notifications


@router.get("/{eid}/timeline", response_model=list[TimelineOut])
def timeline(eid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _own(db, user, eid).timeline


@router.post("/{eid}/ambulance", response_model=EmergencyOut)
def request_ambulance(eid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Records a request only. No ambulance provider is integrated, so nothing is dispatched."""
    em = _own(db, user, eid)
    em.ambulance.status = "REQUESTED"
    em.ambulance.requested_at = datetime.now(timezone.utc)
    em.ambulance.notes = "Request recorded in MediBridge. No provider integration: contact an ambulance service directly."
    _log(db, em, "Ambulance requested (recorded only, not dispatched)", "REQUESTED", user.full_name)
    db.commit(); db.refresh(em)
    return em


@router.post("/{eid}/hospital", response_model=EmergencyOut)
def request_hospital(eid: int, facility_id: int = Query(...), db: Session = Depends(get_db),
                     user: User = Depends(current_user)):
    em = _own(db, user, eid)
    fac = db.get(Facility, facility_id)
    if not fac:
        raise HTTPException(404, "Facility not found")
    em.hospital.facility_id, em.hospital.status = fac.id, "REQUESTED"
    _log(db, em, f"Facility selected: {fac.name}", "REQUESTED", user.full_name)
    db.add(Notification(emergency_id=em.id, type="FACILITY_SELECTED", channel="IN_APP", status="SENT"))
    db.commit(); db.refresh(em)
    return em


@router.patch("/{eid}/coordination", response_model=EmergencyOut)
def coordination(eid: int, data: CoordinationIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    em = _own(db, user, eid)
    now = datetime.now(timezone.utc)
    if data.ambulance_status:
        em.ambulance.status = data.ambulance_status.value
        if data.ambulance_status.value == "ASSIGNED":
            em.ambulance.assigned_at = now
        if data.ambulance_provider is not None: em.ambulance.provider = data.ambulance_provider
        if data.ambulance_eta_minutes is not None: em.ambulance.eta_minutes = data.ambulance_eta_minutes
        _log(db, em, f"Ambulance status: {em.ambulance.status}", em.ambulance.status, user.full_name)
        db.add(Notification(emergency_id=em.id, type="AMBULANCE_STATUS_CHANGE", channel="IN_APP", status="SENT"))
    if data.hospital_status:
        if data.facility_id is not None:
            if not db.get(Facility, data.facility_id):
                raise HTTPException(404, "Facility not found")
            em.hospital.facility_id = data.facility_id
        em.hospital.status = data.hospital_status.value
        if data.notes is not None: em.hospital.notes = data.notes
        _log(db, em, f"Hospital status: {em.hospital.status}", em.hospital.status, user.full_name)
        db.add(Notification(emergency_id=em.id, type="HOSPITAL_RESPONSE", channel="IN_APP", status="SENT"))
    db.commit(); db.refresh(em)
    return em



================================================
FILE: backend/app/routers/facilities.py
================================================
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



================================================
FILE: backend/app/services/__init__.py
================================================
[Empty file]


================================================
FILE: backend/app/services/notify.py
================================================
import json, logging, os, smtplib, urllib.error, urllib.request
from email.message import EmailMessage

log = logging.getLogger("medibridge.notify")


def brevo_configured() -> bool:
    return bool(os.getenv("BREVO_API_KEY") and os.getenv("SMTP_FROM_EMAIL"))


def smtp_configured() -> bool:
    return all(os.getenv(k) for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_FROM_EMAIL"))


def email_configured() -> bool:
    return brevo_configured() or smtp_configured()


def build_email(em, to_addr: str) -> EmailMessage:
    front = os.getenv("FRONTEND_URL", "http://localhost:5500")
    msg = EmailMessage()
    msg["Subject"] = f"[MediBridge] {em.priority} emergency {em.code}"
    msg["From"] = f'{os.getenv("SMTP_FROM_NAME", "MediBridge")} <{os.getenv("SMTP_FROM_EMAIL")}>'
    msg["To"] = to_addr
    coords = f"{em.latitude}, {em.longitude}" if em.latitude is not None else "not captured"
    msg.set_content(
        f"Emergency ID: {em.code}\nPatient: {em.patient_name}\nIncident: {em.incident_type}\n"
        f"Condition: {em.condition or '-'}\nPriority: {em.priority}\nTime: {em.created_at}\n"
        f"Location: {em.location_text or '-'} ({coords})\nSymptoms: {em.symptoms or '-'}\n"
        f"Notes: {em.notes or '-'}\n\nDetails: {front}/emergency.html?id={em.id}\n\n"
        "This message is for coordination and informational purposes. It does not replace "
        "professional medical or emergency-service advice. In a genuine emergency, contact "
        "your local emergency services."
    )
    return msg


def _send_brevo(em, to_addr: str):
    """HTTPS API (port 443): works on hosts that block SMTP ports, e.g. Render free."""
    msg = build_email(em, to_addr)
    payload = {"sender": {"name": os.getenv("SMTP_FROM_NAME", "MediBridge"), "email": os.getenv("SMTP_FROM_EMAIL")},
               "to": [{"email": to_addr}], "subject": msg["Subject"], "textContent": msg.get_content()}
    req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(payload).encode(), method="POST",
                                 headers={"api-key": os.getenv("BREVO_API_KEY"), "Content-Type": "application/json",
                                          "accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Brevo HTTP {e.code}: {e.read().decode(errors='ignore')[:200]}") from None


def _send_smtp(em, to_addr: str):
    with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT")), timeout=15) as s:
        if os.getenv("SMTP_USE_TLS", "true").lower() == "true":
            s.starttls()
        if os.getenv("SMTP_USERNAME"):
            s.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD", ""))
        s.send_message(build_email(em, to_addr))


def send_email(em, to_addr: str, retries: int = 2):
    """Returns (ok, error, attempts). Never raises; never logs credentials."""
    if not email_configured():
        return False, "Email is not configured on the server", 0
    send = _send_brevo if brevo_configured() else _send_smtp
    last = None
    for attempt in range(1, retries + 2):
        try:
            send(em, to_addr)
            return True, None, attempt
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
            log.warning("Email attempt %s to %s failed: %s", attempt, to_addr, last[:120])
    return False, last, retries + 1



================================================
FILE: backend/tests/__init__.py
================================================
[Empty file]


================================================
FILE: backend/tests/conftest.py
================================================
import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["SECRET_KEY"] = "test-secret"
for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_FROM_EMAIL", "BREVO_API_KEY"):
    os.environ[k] = ""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import seed_facilities


@pytest.fixture(scope="session")
def client():
    seed_facilities.run()
    return TestClient(app)


def make_user(client, email):
    r = client.post("/api/auth/register", json={"full_name": "Test User", "email": email, "password": "Passw0rdX"})
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def auth(client, request):
    return make_user(client, f"{request.node.name}@example.com")



================================================
FILE: backend/tests/test_api.py
================================================
import jwt, os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from .conftest import make_user

EM = {"incident_type": "Accident", "patient_name": "Test Patient", "priority": "CRITICAL",
      "latitude": 22.57, "longitude": 88.36}


def test_register_login_me(client):
    h = make_user(client, "a@example.com")
    assert client.get("/api/auth/me", headers=h).json()["email"] == "a@example.com"
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": "Passw0rdX"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/register", json={"full_name": "x", "email": "a@example.com", "password": "Passw0rdX"}).status_code == 409


def test_protected_and_bad_tokens(client):
    assert client.get("/api/emergencies").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401
    expired = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, "test-secret", algorithm="HS256")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_emergency_crud_and_isolation(client, auth):
    r = client.post("/api/emergencies", json=EM, headers=auth)
    assert r.status_code == 201 and r.json()["code"].startswith("MB-")
    eid = r.json()["id"]
    assert client.patch(f"/api/emergencies/{eid}", json={"status": "RESOLVED"}, headers=auth).json()["status"] == "RESOLVED"
    events = [e["event"] for e in client.get(f"/api/emergencies/{eid}/timeline", headers=auth).json()]
    assert "Emergency created" in events
    other = make_user(client, "other@example.com")
    assert client.get(f"/api/emergencies/{eid}", headers=other).status_code == 404
    assert client.delete(f"/api/emergencies/{eid}", headers=auth).status_code == 204
    assert client.get(f"/api/emergencies/{eid}", headers=auth).status_code == 404


def test_invalid_input(client, auth):
    assert client.post("/api/emergencies", json={**EM, "latitude": 999}, headers=auth).status_code == 422
    assert client.post("/api/emergencies", json={**EM, "incident_type": "Nope"}, headers=auth).status_code == 422


def test_contacts_and_notify(client, auth):
    em = client.post("/api/emergencies", json=EM, headers=auth).json()
    assert client.post(f"/api/emergencies/{em['id']}/notify", headers=auth).status_code == 400  # no contacts
    c = client.post("/api/contacts", json={"name": "Rahul", "email": "r@example.com", "is_primary": True}, headers=auth)
    assert c.status_code == 201
    cid = c.json()["id"]
    assert client.put(f"/api/contacts/{cid}", json={"name": "Rahul K", "email": "r@example.com"}, headers=auth).json()["name"] == "Rahul K"
    # SMTP not configured -> honest 502 and a FAILED notification record
    assert client.post(f"/api/emergencies/{em['id']}/notify", headers=auth).status_code == 502
    notes = client.get(f"/api/emergencies/{em['id']}/notifications", headers=auth).json()
    assert any(n["status"] == "FAILED" for n in notes)
    # SMTP success (mocked)
    with patch("app.routers.emergencies.send_email", return_value=(True, None, 1)):
        assert client.post(f"/api/emergencies/{em['id']}/notify", headers=auth).status_code == 200
    assert client.delete(f"/api/contacts/{cid}", headers=auth).status_code == 204


def test_facilities(client, auth):
    assert len(client.get("/api/facilities", headers=auth).json()) >= 5
    near = client.get("/api/facilities/nearby?lat=22.57&lon=88.36&radius_km=10", headers=auth).json()
    assert near and near == sorted(near, key=lambda f: f["distance_km"])
    assert client.get("/api/facilities/nearby?lat=200&lon=0", headers=auth).status_code == 422
    assert client.get("/api/facilities/nearby/search?lat=22.57&lon=88.36&type=Blood%20Bank", headers=auth).status_code == 200


def test_coordination(client, auth):
    em = client.post("/api/emergencies", json=EM, headers=auth).json()
    fid = client.get("/api/facilities", headers=auth).json()[0]["id"]
    assert client.post(f"/api/emergencies/{em['id']}/hospital?facility_id={fid}", headers=auth).json()["hospital"]["status"] == "REQUESTED"
    r = client.patch(f"/api/emergencies/{em['id']}/coordination", json={"ambulance_status": "ASSIGNED"}, headers=auth)
    assert r.json()["ambulance"]["status"] == "ASSIGNED"
    assert client.patch(f"/api/emergencies/{em['id']}/coordination", json={"hospital_status": "BOGUS"}, headers=auth).status_code == 422


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}



================================================
FILE: frontend/app.js
================================================
[Binary file]


================================================
FILE: frontend/auth.js
================================================
const reg = !!$("#full_name");
$("#f").onsubmit = async e => {
  e.preventDefault(); const btn = $("button[type=submit]"); btn.disabled = true; $("#err").textContent = "";
  try {
    const body = {email: $("#email").value.trim(), password: $("#pw").value};
    if (reg) { body.full_name = $("#full_name").value.trim(); for (const k of ["phone", "blood_group"]) if ($("#" + k).value) body[k] = $("#" + k).value; if ($("#age").value) body.age = +$("#age").value; }
    const d = await api(reg ? "/api/auth/register" : "/api/auth/login", {method: "POST", body});
    localStorage.setItem("mb_token", d.access_token); location.href = "dashboard.html";
  } catch (er) { $("#err").textContent = er.message; btn.disabled = false; }
};



================================================
FILE: frontend/config.js
================================================
   window.MB_CONFIG = { API_BASE: "https://medibridge-qedv.onrender.com" };


================================================
FILE: frontend/contacts.html
================================================
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Trusted contacts – MediBridge</title><link rel="stylesheet" href="style.css"></head>
<body><main id="main"><h1>Trusted contacts</h1><div id="content"></div></main>
<script src="config.js"></script><script src="app.js"></script><script src="contacts.js"></script></body></html>



================================================
FILE: frontend/contacts.js
================================================
(async () => {
  if (!await shell("contacts")) return;
  const c = $("#content");
  c.innerHTML = `<div class="row"><button class="primary" id="add">Add contact</button></div><div id="list"></div>
  <dialog id="dlg"><form method="dialog" id="cf"><h2 id="dt">Contact</h2>
   <label for="n">Name</label><input id="n" required><label for="r">Relationship</label><input id="r">
   <label for="p">Phone</label><input id="p" type="tel"><label for="e">Email (needed for email alerts)</label><input id="e" type="email">
   <label for="pr">Priority (1 = first)</label><input id="pr" type="number" min="1" max="10" value="1">
   <label><input id="pm" type="checkbox" style="width:auto;min-height:0"> Primary contact</label>
   <div class="row" style="margin-top:1rem"><button class="primary" value="save">Save</button><button value="cancel">Cancel</button></div></form></dialog>`;
  let editing = null, data = [];
  async function load() {
    loading($("#list"));
    try { data = await api("/api/contacts"); } catch (e) { $("#list").innerHTML = ""; return toast(e.message, true); }
    $("#list").innerHTML = data.length ? data.map(k => `<div class="card"><b>${esc(k.name)}</b> ${k.is_primary ? '<span class="badge">★ Primary</span>' : ""}<br>${esc(k.relationship || "")}<br>${esc(k.phone || "")} ${esc(k.email || "")}
      <div class="row" style="margin-top:.5rem"><button data-e="${k.id}">Edit</button><button class="danger" data-d="${k.id}">Delete</button></div></div>`).join("")
      : '<p class="card">No trusted contacts yet. Add someone who should be told in an emergency.</p>';
    document.querySelectorAll("[data-e]").forEach(b => b.onclick = () => open(data.find(x => x.id == b.dataset.e)));
    document.querySelectorAll("[data-d]").forEach(b => b.onclick = async () => { if (!confirm("Delete this contact?")) return; try { await api("/api/contacts/" + b.dataset.d, {method: "DELETE"}); toast("Contact deleted"); } catch (e) { toast(e.message, true); } load(); });
  }
  function open(k) { editing = k; $("#dt").textContent = k ? "Edit contact" : "Add contact";
    $("#n").value = k?.name || ""; $("#r").value = k?.relationship || ""; $("#p").value = k?.phone || ""; $("#e").value = k?.email || ""; $("#pr").value = k?.priority || 1; $("#pm").checked = !!k?.is_primary; $("#dlg").showModal(); }
  $("#add").onclick = () => open(null);
  $("#cf").onsubmit = async e => {
    if (e.submitter.value !== "save") return; e.preventDefault();
    const body = {name: $("#n").value.trim(), relationship: $("#r").value || null, phone: $("#p").value || null, email: $("#e").value || null, priority: +$("#pr").value, is_primary: $("#pm").checked};
    try { await api(editing ? "/api/contacts/" + editing.id : "/api/contacts", {method: editing ? "PUT" : "POST", body}); $("#dlg").close(); toast("Contact saved"); load(); }
    catch (er) { toast(er.message, true); }
  };
  load();
})();



================================================
FILE: frontend/dashboard.html
================================================
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dashboard – MediBridge</title><link rel="stylesheet" href="style.css"></head>
<body><main id="main"><h1>Dashboard</h1><div id="content"></div></main>
<script src="config.js"></script><script src="app.js"></script><script src="dashboard.js"></script></body></html>



================================================
FILE: frontend/dashboard.js
================================================
(async () => {
  if (!await shell("dashboard")) return;
  const c = $("#content"); loading(c);
  let list = [], contacts = [], facs = [];
  try { [list, contacts, facs] = await Promise.all([api("/api/emergencies"), api("/api/contacts"), api("/api/facilities")]); }
  catch (e) { c.innerHTML = ""; return toast(e.message, true); }
  const active = list.filter(e => e.status === "ACTIVE"), resolved = list.filter(e => e.status === "RESOLVED");
  const stat = (n, l) => `<div class="card stat"><b>${n}</b>${l}</div>`;
  const act = active[0];
  c.innerHTML = `
    <div class="grid">${stat(active.length, "Active emergencies")}${stat(resolved.length, "Resolved")}${stat(contacts.length, "Trusted contacts")}${stat(facs.length, "Facilities (demo data)")}</div>
    ${act ? `<section class="card" aria-labelledby="ae"><h2 id="ae">Active emergency</h2>
      <p><b>${esc(act.code)}</b> ${pBadge(act.priority)} ${sBadge(act.status)}</p>
      <p>Patient: ${esc(act.patient_name)}<br>Incident: ${esc(act.incident_type)}<br>Location: ${esc(act.location_text || (act.latitude != null ? act.latitude + ", " + act.longitude : "not captured"))}</p>
      <p>Ambulance: ${esc(act.ambulance?.status)} · Hospital: ${esc(act.hospital?.status)}</p>
      <a class="btn primary" href="emergency.html?id=${act.id}">Open emergency</a></section>` : `<p class="card">No active emergency. Press and hold SOS if you need to start one.</p>`}
    <section class="card sos-wrap" id="sos-sec" aria-labelledby="st"><h2 id="st">Start an emergency</h2>
      <button id="sos" type="button" aria-describedby="sh">SOS<small>hold 3 s</small></button>
      <p id="sh" class="muted">Press and hold for 3 seconds (or hold Space/Enter). This creates a record and lets you alert your trusted contacts. It does not call emergency services.</p></section>
    <dialog id="dlg"><form method="dialog" id="cf"><h2>Confirm emergency</h2>
      <label for="inc">Incident type</label><select id="inc">${["Medical Emergency", "Accident", "Cardiac Emergency", "Breathing Problem", "Unconscious Person", "Injury", "Fire", "Other"].map(i => `<option>${i}</option>`).join("")}</select>
      <label for="pri">Priority</label><select id="pri"><option>CRITICAL</option><option selected>HIGH</option><option>MEDIUM</option><option>LOW</option></select>
      <label for="loc">Location (used if device location is unavailable)</label><input id="loc" placeholder="Area, city">
      <div class="row" style="margin-top:1rem"><button class="primary" id="go" value="go">Confirm emergency</button><button value="cancel">Cancel</button></div></form></dialog>`;
  const btn = $("#sos"), dlg = $("#dlg"); let start = 0, raf = 0;
  const stop = () => { cancelAnimationFrame(raf); start = 0; btn.style.setProperty("--p", 0); };
  const tick = () => { const p = Math.min((performance.now() - start) / 3000, 1); btn.style.setProperty("--p", p);
    if (p >= 1) { stop(); dlg.showModal(); } else raf = requestAnimationFrame(tick); };
  const down = () => { if (!start) { start = performance.now(); tick(); } };
  btn.addEventListener("pointerdown", down);
  ["pointerup", "pointerleave", "pointercancel"].forEach(ev => btn.addEventListener(ev, stop));
  btn.addEventListener("keydown", e => { if ((e.key === " " || e.key === "Enter") && !e.repeat) { e.preventDefault(); down(); } });
  btn.addEventListener("keyup", stop);
  btn.addEventListener("contextmenu", e => e.preventDefault());
  $("#cf").onsubmit = async e => {
    if (e.submitter.value !== "go") return;
    e.preventDefault(); $("#go").disabled = true;
    const body = {incident_type: $("#inc").value, priority: $("#pri").value, location_text: $("#loc").value || null};
    try { const p = await getPosition(); body.latitude = p.latitude; body.longitude = p.longitude; }
    catch (er) { toast(er.message + " Emergency will be created without coordinates.", true); }
    try { const em = await api("/api/emergencies", {method: "POST", body}); location.href = "emergency.html?id=" + em.id; }
    catch (er) { toast(er.message, true); $("#go").disabled = false; }
  };
  if (location.hash === "#sos") btn.focus();
})();



================================================
FILE: frontend/emergency.html
================================================
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Emergency – MediBridge</title><link rel="stylesheet" href="style.css"></head>
<body><main id="main"><h1>Emergency</h1><div id="content"></div></main>
<script src="config.js"></script><script src="app.js"></script><script src="emergency.js"></script></body></html>



================================================
FILE: frontend/emergency.js
================================================
(async () => {
  if (!await shell("")) return;
  const id = new URLSearchParams(location.search).get("id"), c = $("#content");
  if (!id) { c.innerHTML = '<p class="card">No emergency selected. <a href="history.html">View history</a></p>'; return; }
  const AMB = ["SEARCHING", "REQUESTED", "ASSIGNED", "EN_ROUTE", "ARRIVED", "COMPLETED", "UNAVAILABLE"];
  const HOS = ["SEARCHING", "REQUESTED", "PENDING", "ACCEPTED", "REJECTED", "READY", "ARRIVED", "COMPLETED"];
  let facMap = {}, nearby = null;
  const opts = (a, v) => a.map(x => `<option ${x === v ? "selected" : ""}>${x}</option>`).join("");
  async function run(fn, ok) { try { await fn(); if (ok) toast(ok); } catch (e) { toast(e.message, true); } await load(); }

  async function load() {
    loading(c);
    let em, tl, nt, cts;
    try {
      [em, tl, nt, cts] = await Promise.all([api(`/api/emergencies/${id}`), api(`/api/emergencies/${id}/timeline`), api(`/api/emergencies/${id}/notifications`), api("/api/contacts")]);
      if (!Object.keys(facMap).length) (await api("/api/facilities")).forEach(f => facMap[f.id] = f);
    } catch (e) { c.innerHTML = `<p class="card">${esc(e.message)} <a href="history.html">Back to history</a></p>`; return; }
    const hasLoc = em.latitude != null, active = em.status === "ACTIVE", fac = facMap[em.hospital?.facility_id];
    c.innerHTML = `
    <section class="card"><h2>${esc(em.code)} ${pBadge(em.priority)} ${sBadge(em.status)}</h2>
      <p>Patient: <b>${esc(em.patient_name)}</b>${em.patient_age != null ? ", " + em.patient_age : ""} · Blood group: ${esc(em.blood_group || "–")}<br>
      Incident: ${esc(em.incident_type)} · Condition: ${esc(em.condition || "–")}<br>Symptoms: ${esc(em.symptoms || "–")}<br>Notes: ${esc(em.notes || "–")}<br>
      Time: ${fmt(em.created_at)}<br>Location: ${esc(em.location_text || "–")} (${hasLoc ? em.latitude.toFixed(5) + ", " + em.longitude.toFixed(5) : "coordinates not captured"})
      ${hasLoc ? `· <a href="https://www.google.com/maps?q=${em.latitude},${em.longitude}" target="_blank" rel="noopener">Open map</a>` : ""}</p>
      <div class="row noprint"><button id="print">Print / save as PDF</button>
      ${active ? `<button class="danger" id="resolve">Mark resolved</button>` : ""}</div></section>
    <section class="card"><h2>Trusted contacts</h2>${cts.length ? "<ul>" + cts.map(k => `<li>${esc(k.name)} (${esc(k.relationship || "contact")}) ${esc(k.phone || "")} ${esc(k.email || "")} ${k.is_primary ? "★ primary" : ""}</li>`).join("") + "</ul>" : '<p>No contacts yet. <a href="contacts.html">Add a contact</a></p>'}
      <button class="primary noprint" id="notify" ${cts.some(k => k.email) ? "" : "disabled"}>Email trusted contacts</button></section>
    <section class="card"><h2>Ambulance</h2><p>Status: ${sBadge(em.ambulance.status)} ${em.ambulance.provider ? esc(em.ambulance.provider) : ""} ${em.ambulance.eta_minutes != null ? "ETA " + em.ambulance.eta_minutes + " min" : ""}</p>
      <p class="muted">${esc(em.ambulance.notes || "No ambulance provider is connected. Requests are recorded here only; call an ambulance service directly.")}</p>
      <div class="row noprint"><button id="amb">Record ambulance request</button><label class="muted" for="as" style="margin:0">Status</label><select id="as" style="width:auto">${opts(AMB, em.ambulance.status)}</select><button id="asu">Update</button></div></section>
    <section class="card"><h2>Hospital</h2><p>Status: ${sBadge(em.hospital.status)} · Facility: ${fac ? esc(fac.name) + (fac.is_demo ? " (demo data)" : "") : "not selected"}</p>
      <div class="row noprint"><label class="muted" for="hs" style="margin:0">Status</label><select id="hs" style="width:auto">${opts(HOS, em.hospital.status)}</select><button id="hsu">Update</button>
      <button id="near" ${hasLoc ? "" : "disabled"}>Find nearby facilities</button></div>
      ${hasLoc ? "" : '<p class="muted">Add coordinates to search nearby.</p>'}
      <div id="nearby">${nearby ? nearby.map(f => `<div class="card"><b>${esc(f.name)}</b> ${f.is_demo ? '<span class="badge">DEMO</span>' : ""}<br>${f.distance_km} km · ${esc(f.type)} · ${esc(f.address || "")}<br>
        <a class="btn" href="tel:${esc(f.phone)}">Call</a> <a class="btn" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=${f.latitude},${f.longitude}">Directions</a>
        <button data-f="${f.id}" class="pick noprint">Select facility</button></div>`).join("") || "<p>No facilities within 25 km.</p>" : ""}</div></section>
    <section class="card"><h2>Notifications</h2>${nt.length ? `<table class="resp"><tbody>${nt.map(n => `<tr><td>${fmt(n.created_at)}</td><td>${esc(n.type)}</td><td>${esc(n.channel)} ${esc(n.recipient || "")}</td><td>${sBadge(n.status)} ${esc(n.error || "")}</td></tr>`).join("")}</tbody></table>` : "<p>None yet.</p>"}</section>
    <section class="card"><h2>Timeline</h2><ul class="tl">${tl.map(e => `<li><b>${fmt(e.created_at)}</b> ${esc(e.event)} <span class="muted">— ${esc(e.actor || "system")}${e.status ? ", " + esc(e.status) : ""}</span></li>`).join("")}</ul></section>`;
    $("#print").onclick = () => print();
    $("#resolve") && ($("#resolve").onclick = () => confirm("Mark this emergency as resolved?") && run(() => api(`/api/emergencies/${id}`, {method: "PATCH", body: {status: "RESOLVED"}}), "Emergency resolved"));
    $("#notify").onclick = () => run(async () => { const r = await api(`/api/emergencies/${id}/notify`, {method: "POST"}); const bad = r.results.filter(x => x.status === "FAILED"); if (bad.length) toast(`${bad.length} email(s) failed: ${bad.map(b => b.contact).join(", ")}`, true); }, "Contacts emailed");
    $("#amb").onclick = () => run(() => api(`/api/emergencies/${id}/ambulance`, {method: "POST"}), "Request recorded (not dispatched)");
    $("#asu").onclick = () => run(() => api(`/api/emergencies/${id}/coordination`, {method: "PATCH", body: {ambulance_status: $("#as").value}}), "Ambulance status updated");
    $("#hsu").onclick = () => run(() => api(`/api/emergencies/${id}/coordination`, {method: "PATCH", body: {hospital_status: $("#hs").value}}), "Hospital status updated");
    $("#near").onclick = async () => { try { nearby = await api(`/api/facilities/nearby?lat=${em.latitude}&lon=${em.longitude}&radius_km=25`); } catch (e) { return toast(e.message, true); } load(); };
    document.querySelectorAll(".pick").forEach(b => b.onclick = () => run(() => api(`/api/emergencies/${id}/hospital?facility_id=${b.dataset.f}`, {method: "POST"}), "Facility selected"));
  }
  load();
})();



================================================
FILE: frontend/facilities.html
================================================
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nearby facilities – MediBridge</title><link rel="stylesheet" href="style.css"></head>
<body><main id="main"><h1>Nearby facilities</h1><div id="content"></div></main>
<script src="config.js"></script><script src="app.js"></script><script src="facilities.js"></script></body></html>



================================================
FILE: frontend/facilities.js
================================================
(async () => {
  if (!await shell("facilities")) return;
  const c = $("#content");
  const CATS = [["Hospital", "Hospitals"], ["Blood Bank", "Blood banks"], ["Ambulance Service", "Ambulances"],
                ["Emergency Medical Center", "Emergency centers"], ["Clinic", "Clinics"], ["Pharmacy", "Pharmacies"]];
  let coords = null, current = null;
  c.innerHTML = `<p class="notice">Facilities shown here are demo data and are not verified live availability. Call before travelling.</p>
  <section class="card"><h2>What do you need nearby?</h2>
   <div class="row" role="group" aria-label="Facility type" id="cats">${CATS.map(([v, l]) => `<button type="button" class="cat" data-t="${v}" aria-pressed="false">${l}</button>`).join("")}</div>
   <div class="row" style="margin-top:.8rem"><label for="rad" style="margin:0">Search within</label>
    <select id="rad" style="width:auto"><option value="10">10 km</option><option value="25" selected>25 km</option><option value="50">50 km</option><option value="100">100 km</option><option value="200">200 km</option></select>
    <label style="margin:0"><input id="eo" type="checkbox" style="width:auto;min-height:0"> Emergency care only</label>
    <button type="button" id="loc">Refresh my location</button></div>
   <p id="status" role="status" class="muted"></p>
   <details id="manual"><summary>Enter location manually</summary><form id="mf" class="row" style="margin-top:.5rem">
    <div><label for="lat">Latitude</label><input id="lat" type="number" step="any" min="-90" max="90" required></div>
    <div><label for="lon">Longitude</label><input id="lon" type="number" step="any" min="-180" max="180" required></div>
    <button class="primary" type="submit">Search here</button></form></details></section><div id="res"></div>`;

  const status = m => { $("#status").textContent = m; };
  const valid = (la, lo) => Number.isFinite(la) && Number.isFinite(lo) && Math.abs(la) <= 90 && Math.abs(lo) <= 180;

  async function getCoords(force) {
    if (coords && !force) return coords;
    status("Finding your location…");
    try { const p = await getPosition(); coords = {lat: p.latitude, lon: p.longitude}; $("#lat").value = coords.lat.toFixed(5); $("#lon").value = coords.lon.toFixed(5); return coords; }
    catch (e) {
      const la = parseFloat($("#lat").value), lo = parseFloat($("#lon").value);
      if (valid(la, lo)) { coords = {lat: la, lon: lo}; return coords; }
      $("#manual").open = true; status(e.message + " Enter your coordinates below.");
      throw e;
    }
  }

  const query = (type, radius) => {
    const q = new URLSearchParams({lat: coords.lat, lon: coords.lon, radius_km: radius, type, emergency_only: $("#eo").checked});
    return api("/api/facilities/nearby/search?" + q);
  };

  async function search(type) {
    current = type;
    document.querySelectorAll(".cat").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.t === type)));
    loading($("#res"));
    try { await getCoords(false); } catch { $("#res").innerHTML = ""; return; }
    const label = (CATS.find(x => x[0] === type) || [, type])[1].toLowerCase();
    let radius = +$("#rad").value, list;
    try {
      list = await query(type, radius);
      if (!list.length && radius < 200) { radius = 200; list = await query(type, radius); if (list.length) status(`None within ${$("#rad").value} km. Showing the nearest within 200 km.`); }
      else status(`Showing ${label} within ${radius} km of ${coords.lat.toFixed(3)}, ${coords.lon.toFixed(3)}. Accuracy depends on your device.`);
    } catch (er) { $("#res").innerHTML = ""; return toast(er.message, true); }
    $("#res").innerHTML = list.length ? list.map(f => `<div class="card"><b>${esc(f.name)}</b> ${f.is_demo ? '<span class="badge">DEMO</span>' : ""}<br>${f.distance_km} km away · ${esc(f.type)}<br>${esc(f.address || "")}<br>
      Emergency: ${f.emergency_available ? "yes" : "no"} · Ambulance: ${f.ambulance_available ? "yes" : "no"} · Blood: ${f.blood_available ? "yes" : "no"} <span class="muted">(unverified)</span>
      <div class="row" style="margin-top:.5rem"><a class="btn primary" href="tel:${esc(f.phone)}">Call ${esc(f.phone)}</a>
      <a class="btn" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=${f.latitude},${f.longitude}">Directions</a></div></div>`).join("")
      : `<p class="card">No ${esc(label)} found within 200 km in the demo data. Try another category, or call your local emergency number.</p>`;
  }

  document.querySelectorAll(".cat").forEach(b => b.onclick = () => search(b.dataset.t));
  $("#loc").onclick = async () => { coords = null; try { await getCoords(true); status("Location updated."); if (current) search(current); } catch {} };
  $("#rad").onchange = $("#eo").onchange = () => current && search(current);
  $("#mf").onsubmit = e => { e.preventDefault(); const la = parseFloat($("#lat").value), lo = parseFloat($("#lon").value);
    if (!valid(la, lo)) return toast("Enter valid coordinates.", true); coords = {lat: la, lon: lo}; search(current || "Hospital"); };
})();


================================================
FILE: frontend/history.html
================================================
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Emergency history – MediBridge</title><link rel="stylesheet" href="style.css"></head>
<body><main id="main"><h1>Emergency history</h1><div id="content"></div></main>
<script src="config.js"></script><script src="app.js"></script><script src="history.js"></script></body></html>



================================================
FILE: frontend/history.js
================================================
(async () => {
  if (!await shell("history")) return;
  const c = $("#content");
  c.innerHTML = `<form class="card" id="ff"><div class="grid">
   <div><label for="q">Emergency ID</label><input id="q" placeholder="MB-2026-001"></div>
   <div><label for="st">Status</label><select id="st"><option value="">Any</option><option>ACTIVE</option><option>RESOLVED</option><option>CANCELLED</option></select></div>
   <div><label for="pr">Priority</label><select id="pr"><option value="">Any</option><option>CRITICAL</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></div>
   <div><label for="it">Incident</label><select id="it"><option value="">Any</option>${["Accident", "Medical Emergency", "Fire", "Injury", "Unconscious Person", "Cardiac Emergency", "Breathing Problem", "Other"].map(x => `<option>${x}</option>`).join("")}</select></div>
   <div><label for="df">From date</label><input id="df" type="date"></div></div>
   <button class="primary" style="margin-top:.8rem" type="submit">Apply filters</button></form><div id="res"></div>`;
  async function load() {
    loading($("#res"));
    const q = new URLSearchParams(); [["code", "q"], ["status", "st"], ["priority", "pr"], ["incident_type", "it"]].forEach(([k, i]) => $("#" + i).value && q.set(k, $("#" + i).value));
    try {
      let r = await api("/api/emergencies?" + q);
      if ($("#df").value) r = r.filter(e => new Date(e.created_at) >= new Date($("#df").value));
      $("#res").innerHTML = r.length ? `<table class="resp"><thead><tr><th>ID</th><th>Date</th><th>Incident</th><th>Condition</th><th>Priority</th><th>Status</th></tr></thead><tbody>${r.map(e =>
        `<tr><td><a href="emergency.html?id=${e.id}">${esc(e.code)}</a></td><td>${fmt(e.created_at)}</td><td>${esc(e.incident_type)}</td><td>${esc(e.condition || "–")}</td><td>${pBadge(e.priority)}</td><td>${sBadge(e.status)}</td></tr>`).join("")}</tbody></table>`
        : '<p class="card">No emergencies match these filters.</p>';
    } catch (er) { $("#res").innerHTML = ""; toast(er.message, true); }
  }
  $("#ff").onsubmit = e => { e.preventDefault(); load(); };
  load();
})();



================================================
FILE: frontend/index.html
================================================
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=dashboard.html"><title>MediBridge</title></head><body><a href="dashboard.html">Open MediBridge</a></body></html>



================================================
FILE: frontend/login.html
================================================
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Log in – MediBridge</title><link rel="stylesheet" href="style.css"></head>
<body><main class="auth"><h1>MediBridge</h1><form class="card" id="f"><h2>Log in</h2>
<label for="email">Email</label><input id="email" type="email" autocomplete="email" required>
<label for="pw">Password</label><input id="pw" type="password" autocomplete="current-password" required>
<p id="err" role="alert" class="s-FAILED"></p><button class="primary" type="submit">Log in</button>
<p>No account? <a href="register.html">Create one</a></p></form></main>
<script src="config.js"></script><script src="app.js"></script><script src="auth.js"></script></body></html>



================================================
FILE: frontend/register.html
================================================
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Register – MediBridge</title><link rel="stylesheet" href="style.css"></head>
<body><main class="auth"><h1>MediBridge</h1><form class="card" id="f"><h2>Create account</h2>
<label for="full_name">Full name</label><input id="full_name" required>
<label for="email">Email</label><input id="email" type="email" autocomplete="email" required>
<label for="pw">Password (8+ characters, letters and digits)</label><input id="pw" type="password" autocomplete="new-password" minlength="8" required>
<label for="phone">Phone (optional)</label><input id="phone" type="tel">
<label for="age">Age (optional)</label><input id="age" type="number" min="0" max="130">
<label for="blood_group">Blood group (optional)</label><input id="blood_group" maxlength="5">
<p class="muted">We collect only what is needed to coordinate an emergency. Medical details stay private to your account.</p>
<p id="err" role="alert" class="s-FAILED"></p><button class="primary" type="submit">Create account</button>
<p>Have an account? <a href="login.html">Log in</a></p></form></main>
<script src="config.js"></script><script src="app.js"></script><script src="auth.js"></script></body></html>



================================================
FILE: frontend/style.css
================================================
:root{--ink:#14213d;--bg:#f4f6f8;--card:#fff;--line:#d5dbe3;--muted:#55627a;--teal:#0b6e66;--teal-ink:#fff;--sos:#b3261e;--warn:#8a5a00;--ok:#1b6b3a;--r:10px}
:root[data-theme=dark]{--ink:#e7ecf4;--bg:#0f1622;--card:#182233;--line:#2c3a52;--muted:#9fb0c9;--teal:#3fb5a8;--teal-ink:#06201d;--sos:#ff6b5f;--warn:#f0b24a;--ok:#5fcf8a}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 "Atkinson Hyperlegible",system-ui,sans-serif;background:var(--bg);color:var(--ink)}
a{color:var(--teal)}h1{font-size:1.5rem;margin:.2rem 0 1rem}h2{font-size:1.1rem;margin:0 0 .6rem}
:focus-visible{outline:3px solid var(--teal);outline-offset:2px}
header{display:flex;flex-wrap:wrap;gap:.6rem;align-items:center;padding:.6rem 1rem;background:var(--card);border-bottom:1px solid var(--line)}
.brand{font-weight:700;font-size:1.15rem;margin-right:auto;text-decoration:none;color:var(--ink)}
nav{display:flex;gap:.25rem;overflow-x:auto;padding:.4rem 1rem;background:var(--card);border-bottom:1px solid var(--line)}
nav a{padding:.55rem .9rem;border-radius:var(--r);text-decoration:none;color:var(--ink);white-space:nowrap;min-height:44px;display:flex;align-items:center}
nav a[aria-current=page]{background:var(--teal);color:var(--teal-ink);font-weight:700}
nav a.sos-link{border:2px solid var(--sos);color:var(--sos);font-weight:700}
main{max-width:1000px;margin:0 auto;padding:1rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:1rem;margin-bottom:1rem}
.grid{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
.stat b{display:block;font-size:2rem;line-height:1.1}.muted{color:var(--muted);font-size:.9rem}
button,.btn{font:inherit;min-height:44px;padding:.5rem 1rem;border-radius:var(--r);border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:.4rem}
button.primary,.btn.primary{background:var(--teal);color:var(--teal-ink);border-color:var(--teal);font-weight:700}
button.danger{border-color:var(--sos);color:var(--sos)}button:disabled{opacity:.55;cursor:not-allowed}
label{display:block;font-weight:700;margin:.6rem 0 .2rem}
input,select,textarea{font:inherit;width:100%;min-height:44px;padding:.45rem .6rem;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)}
.row{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center}.row>*{flex:0 0 auto}
.badge{display:inline-block;padding:.1rem .55rem;border-radius:999px;border:2px solid currentColor;font-weight:700;font-size:.85rem}
.p-CRITICAL{color:var(--sos)}.p-HIGH{color:var(--warn)}.p-MEDIUM,.p-LOW{color:var(--muted)}.s-SENT,.s-RESOLVED{color:var(--ok)}.s-FAILED{color:var(--sos)}
.sos-wrap{display:grid;place-items:center;padding:1rem}
#sos{--p:0;width:200px;height:200px;border-radius:50%;border:0;padding:0;font-size:2.4rem;font-weight:800;color:#fff;justify-content:center;touch-action:none;user-select:none;
 background:radial-gradient(circle,var(--sos) 62%,transparent 63%),conic-gradient(var(--ink) calc(var(--p)*360deg),var(--line) 0)}
#sos small{display:block;font-size:.8rem;font-weight:400}
ul.tl{list-style:none;margin:0;padding:0 0 0 1rem;border-left:3px solid var(--line)}ul.tl li{margin:0 0 .7rem;padding-left:.6rem}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:.5rem;border-bottom:1px solid var(--line)}
.toasts{position:fixed;bottom:1rem;left:1rem;right:1rem;display:grid;gap:.5rem;z-index:20;pointer-events:none}
.toast{background:var(--ink);color:var(--bg);padding:.7rem 1rem;border-radius:var(--r);max-width:560px;margin:auto;pointer-events:auto}
.toast.err{background:var(--sos);color:#fff}
dialog{border:1px solid var(--line);border-radius:var(--r);background:var(--card);color:var(--ink);max-width:480px;width:calc(100% - 2rem)}
.notice{border-left:4px solid var(--warn);padding:.5rem .8rem;background:var(--card);margin-bottom:1rem;font-size:.9rem}
.auth{max-width:420px;margin:3rem auto}
@media(max-width:600px){table.resp thead{display:none}table.resp td{display:block;border:0;padding:.15rem .5rem}table.resp tr{display:block;border-bottom:1px solid var(--line);padding:.4rem 0}}
@media print{header,nav,.noprint,.toasts{display:none!important}body{background:#fff;color:#000}.card{border:1px solid #999}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}


