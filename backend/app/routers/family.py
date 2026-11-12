
from datetime import datetime, timezone
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import current_user
from ..database import get_db
from ..models import User, FamilyProfile, FamilyProfileShare
from ..services.health_data_crypto import encrypt_health_text
from ..services.family_profiles import (
    encrypt_optional,
    encrypt_profile_fields,
    decrypt_optional,
    serialize_family_profile,
)


router = APIRouter(
    prefix="/api/family",
    tags=["Family Health Profiles"]
)


# =====================================================
# REQUEST SCHEMAS
# =====================================================

class FamilyProfileCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    relationship: str = Field(min_length=2, max_length=50)
    date_of_birth: str | None = Field(default=None, max_length=20)
    blood_group: str | None = Field(default=None, max_length=10)
    allergies: str | None = Field(default=None, max_length=2000)
    emergency_notes: str | None = Field(default=None, max_length=2000)


class FamilyProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    relationship: str | None = Field(default=None, min_length=2, max_length=50)
    date_of_birth: str | None = Field(default=None, max_length=20)
    blood_group: str | None = Field(default=None, max_length=10)
    allergies: str | None = Field(default=None, max_length=2000)
    emergency_notes: str | None = Field(default=None, max_length=2000)


class ShareInvitation(BaseModel):
    email: str = Field(min_length=5, max_length=254)


class ShareResponse(BaseModel):
    decision: str


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def get_owned_profile(db, profile_id, user_id):
    """Return a profile only if the current user owns it."""

    profile = db.query(FamilyProfile).filter(
        FamilyProfile.id == profile_id,
        FamilyProfile.owner_user_id == user_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Family profile not found"
        )

    return profile


def get_readable_profile(db, profile_id, user_id):
    """Return a profile to its owner or an accepted share recipient."""

    profile = db.query(FamilyProfile).filter(
        FamilyProfile.id == profile_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Family profile not found"
        )

    if profile.owner_user_id == user_id:
        return profile

    share = db.query(FamilyProfileShare).filter(
        FamilyProfileShare.profile_id == profile_id,
        FamilyProfileShare.owner_user_id == profile.owner_user_id,
        FamilyProfileShare.invited_user_id == user_id,
        FamilyProfileShare.status == "accepted"
    ).first()

    if not share:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return profile


def validate_profile_text(value, field_name):
    """Validate required profile text after trimming whitespace."""

    value = str(value or "").strip()

    if len(value) < 2:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must contain at least 2 characters"
        )

    return value


def get_share_for_owner(db, profile_id, share_id, user_id):
    """Find a sharing record belonging to the profile owner."""

    share = db.query(FamilyProfileShare).filter(
        FamilyProfileShare.id == share_id,
        FamilyProfileShare.profile_id == profile_id,
        FamilyProfileShare.owner_user_id == user_id
    ).first()

    if not share:
        raise HTTPException(
            status_code=404,
            detail="Share not found"
        )

    return share


# =====================================================
# CREATE FAMILY PROFILE
# =====================================================

@router.post("/profiles")
def create_family_profile(
    payload: FamilyProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    data = payload.dict()

    data["full_name"] = validate_profile_text(
        data["full_name"],
        "Full name"
    )

    data["relationship"] = validate_profile_text(
        data["relationship"],
        "Relationship"
    )

    encrypted = encrypt_profile_fields(data)

    profile = FamilyProfile(
        owner_user_id=user.id,
        **encrypted
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "message": "Family profile created successfully",
        "profile": serialize_family_profile(profile)
    }


# =====================================================
# LIST OWN FAMILY PROFILES
# =====================================================

@router.get("/profiles")
def list_family_profiles(
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    profiles = db.query(FamilyProfile).filter(
        FamilyProfile.owner_user_id == user.id
    ).order_by(
        FamilyProfile.created_at.desc()
    ).all()

    return {
        "profiles": [
            serialize_family_profile(profile)
            for profile in profiles
        ]
    }


# =====================================================
# LIST PROFILES SHARED WITH CURRENT USER
# =====================================================

@router.get("/shared-with-me")
def list_shared_profiles(
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    shares = db.query(FamilyProfileShare).filter(
        FamilyProfileShare.invited_user_id == user.id,
        FamilyProfileShare.status == "accepted"
    ).all()

    results = []

    for share in shares:
        profile = db.query(FamilyProfile).filter(
            FamilyProfile.id == share.profile_id,
            FamilyProfile.owner_user_id == share.owner_user_id
        ).first()

        if profile:
            results.append({
                "share_id": share.id,
                "owner_user_id": share.owner_user_id,
                "profile": serialize_family_profile(profile)
            })

    return {"profiles": results}


# =====================================================
# GET SINGLE FAMILY PROFILE
# =====================================================

@router.get("/profiles/{profile_id}")
def get_family_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    profile = get_readable_profile(
        db,
        profile_id,
        user.id
    )

    return {
        "profile": serialize_family_profile(profile),
        "read_only": profile.owner_user_id != user.id
    }


# =====================================================
# UPDATE FAMILY PROFILE
# =====================================================

@router.put("/profiles/{profile_id}")
def update_family_profile(
    profile_id: int,
    payload: FamilyProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    profile = get_owned_profile(
        db,
        profile_id,
        user.id
    )

    data = payload.dict(exclude_unset=True)

    allowed_fields = {
        "full_name": "encrypted_full_name",
        "relationship": "encrypted_relationship",
        "date_of_birth": "encrypted_date_of_birth",
        "blood_group": "encrypted_blood_group",
        "allergies": "encrypted_allergies",
        "emergency_notes": "encrypted_emergency_notes"
    }

    for field, value in data.items():

        if field not in allowed_fields:
            continue

        if field in ("full_name", "relationship"):
            value = validate_profile_text(
                value,
                field.replace("_", " ").title()
            )

            encrypted_value = encrypt_health_text(value)

        else:
            encrypted_value = encrypt_optional(value)

        setattr(
            profile,
            allowed_fields[field],
            encrypted_value
        )

    profile.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(profile)

    return {
        "message": "Family profile updated successfully",
        "profile": serialize_family_profile(profile)
    }


# =====================================================
# DELETE FAMILY PROFILE
# =====================================================

@router.delete("/profiles/{profile_id}")
def delete_family_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    profile = get_owned_profile(
        db,
        profile_id,
        user.id
    )

    db.delete(profile)
    db.commit()

    return {
        "message": "Family profile deleted successfully"
    }


# =====================================================
# SEND PROFILE SHARING INVITATION
# =====================================================

@router.post("/profiles/{profile_id}/shares")
def invite_user_to_share(
    profile_id: int,
    payload: ShareInvitation,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    profile = get_owned_profile(
        db,
        profile_id,
        user.id
    )

    email = payload.email.strip().lower()

    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        email
    ):
        raise HTTPException(
            status_code=422,
            detail="Invalid email address"
        )

    target_user = db.query(User).filter(
        User.email == email
    ).first()

    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="No registered MediBridge user found with this email"
        )

    if target_user.id == user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot share a profile with yourself"
        )

    existing = db.query(FamilyProfileShare).filter(
        FamilyProfileShare.profile_id == profile.id,
        FamilyProfileShare.invited_user_id == target_user.id
    ).first()

    if existing and existing.status in ("pending", "accepted"):
        raise HTTPException(
            status_code=409,
            detail="An invitation already exists for this user"
        )

    if existing:
        existing.status = "pending"
        existing.owner_user_id = user.id
        existing.created_at = datetime.now(timezone.utc)
        existing.responded_at = None

        share = existing

    else:
        share = FamilyProfileShare(
            profile_id=profile.id,
            owner_user_id=user.id,
            invited_user_id=target_user.id,
            status="pending"
        )

        db.add(share)

    db.commit()
    db.refresh(share)

    return {
        "message": "Sharing invitation created",
        "share_id": share.id,
        "status": share.status
    }


# =====================================================
# LIST INCOMING INVITATIONS
# =====================================================

@router.get("/invitations")
def get_invitations(
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    shares = db.query(FamilyProfileShare).filter(
        FamilyProfileShare.invited_user_id == user.id,
        FamilyProfileShare.status == "pending"
    ).all()

    results = []

    for share in shares:
        profile = db.query(FamilyProfile).filter(
            FamilyProfile.id == share.profile_id,
            FamilyProfile.owner_user_id == share.owner_user_id
        ).first()

        if profile:
            results.append({
                "share_id": share.id,
                "owner_user_id": share.owner_user_id,
                "profile": {
                    "id": profile.id,
                    "full_name": decrypt_optional(
                        profile.encrypted_full_name
                    )
                },
                "created_at": (
                    share.created_at.isoformat()
                    if share.created_at else None
                )
            })

    return {"invitations": results}


# =====================================================
# ACCEPT OR REJECT INVITATION
# =====================================================

@router.post("/invitations/{share_id}/respond")
def respond_to_invitation(
    share_id: int,
    payload: ShareResponse,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    if payload.decision not in ("accepted", "rejected"):
        raise HTTPException(
            status_code=422,
            detail="Decision must be accepted or rejected"
        )

    share = db.query(FamilyProfileShare).filter(
        FamilyProfileShare.id == share_id,
        FamilyProfileShare.invited_user_id == user.id,
        FamilyProfileShare.status == "pending"
    ).first()

    if not share:
        raise HTTPException(
            status_code=404,
            detail="Pending invitation not found"
        )

    profile = db.query(FamilyProfile).filter(
        FamilyProfile.id == share.profile_id,
        FamilyProfile.owner_user_id == share.owner_user_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Family profile no longer exists"
        )

    share.status = payload.decision
    share.responded_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": f"Invitation {payload.decision}",
        "status": share.status
    }


# =====================================================
# LIST SHARES FOR A FAMILY PROFILE
# =====================================================

@router.get("/profiles/{profile_id}/shares")
def list_profile_shares(
    profile_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    get_owned_profile(
        db,
        profile_id,
        user.id
    )

    shares = db.query(FamilyProfileShare).filter(
        FamilyProfileShare.profile_id == profile_id,
        FamilyProfileShare.owner_user_id == user.id
    ).all()

    results = []

    for share in shares:
        target = db.query(User).filter(
            User.id == share.invited_user_id
        ).first()

        results.append({
            "share_id": share.id,
            "email": target.email if target else None,
            "status": share.status,
            "created_at": (
                share.created_at.isoformat()
                if share.created_at else None
            ),
            "responded_at": (
                share.responded_at.isoformat()
                if share.responded_at else None
            )
        })

    return {"shares": results}


# =====================================================
# REVOKE PROFILE SHARING
# =====================================================

@router.delete("/profiles/{profile_id}/shares/{share_id}")
def revoke_profile_share(
    profile_id: int,
    share_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    get_owned_profile(
        db,
        profile_id,
        user.id
    )

    share = get_share_for_owner(
        db,
        profile_id,
        share_id,
        user.id
    )

    db.delete(share)
    db.commit()

    return {
        "message": "Profile sharing revoked"
    }
