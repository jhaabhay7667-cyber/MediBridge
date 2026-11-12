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
# =====================================================
# PHASE 2 - MEDICAL REPORT ANALYZER
# =====================================================

class MedicalReport(Base):

    __tablename__ = "medical_reports"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    original_filename = Column(
        String(255),
        nullable=False
    )

    content_type = Column(
        String(80),
        nullable=False
    )

    file_size = Column(
        Integer,
        nullable=False
    )

    encrypted_file = Column(
        Text,
        nullable=False
    )

    encrypted_extracted_text = Column(
        Text,
        nullable=False
    )

    encrypted_analysis = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=now,
        nullable=False
    )

    # =====================================================
# PHASE 3 - AI SYMPTOM CHECKER
# =====================================================

class SymptomAssessment(Base):
    __tablename__ = "symptom_assessments"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    encrypted_input = Column(Text, nullable=False)
    encrypted_result = Column(Text, nullable=False)

    urgency = Column(String(20), nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=now,
        nullable=False
    )


# =====================================================
# PHASE 4 - AI HEALTH CHATBOT
# =====================================================

class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    title = Column(String(160), default="New conversation", nullable=False)

    language = Column(String(30), default="English", nullable=False)

    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)

    conversation_id = Column(
        Integer,
        ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    role = Column(String(20), nullable=False)  # user / assistant

    encrypted_content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), default=now, nullable=False)

class WoundAssessment(Base):
    __tablename__ = "wound_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)

    # Encrypted image bytes (stored as base64 text).
    encrypted_image = Column(Text, nullable=False)

    # Encrypted AI observation text.
    encrypted_result = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=now,
        nullable=False,
    )

class FamilyProfile(Base):
    __tablename__ = "family_profiles"

    id = Column(Integer, primary_key=True, index=True)

    owner_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Sensitive profile fields are encrypted before database storage.
    encrypted_full_name = Column(Text, nullable=False)
    encrypted_relationship = Column(Text, nullable=False)
    encrypted_date_of_birth = Column(Text, nullable=True)
    encrypted_blood_group = Column(Text, nullable=True)
    encrypted_allergies = Column(Text, nullable=True)
    encrypted_emergency_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=now,
        onupdate=now,
        nullable=False
    )


class FamilyProfileShare(Base):
    __tablename__ = "family_profile_shares"

    id = Column(Integer, primary_key=True, index=True)

    profile_id = Column(
        Integer,
        ForeignKey("family_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    owner_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    invited_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    status = Column(String(20), default="pending", nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)
