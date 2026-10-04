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
