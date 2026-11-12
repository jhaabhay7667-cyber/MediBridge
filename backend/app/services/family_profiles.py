
from ..services.health_data_crypto import (
    encrypt_health_text,
    decrypt_health_text
)


PROFILE_FIELDS = {
    "full_name": "encrypted_full_name",
    "relationship": "encrypted_relationship",
    "date_of_birth": "encrypted_date_of_birth",
    "blood_group": "encrypted_blood_group",
    "allergies": "encrypted_allergies",
    "emergency_notes": "encrypted_emergency_notes",
}


def encrypt_optional(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return encrypt_health_text(value)


def decrypt_optional(value):
    if not value:
        return ""

    return decrypt_health_text(value)


def encrypt_profile_fields(data):
    encrypted = {}

    for field, column in PROFILE_FIELDS.items():
        value = data.get(field)

        if field in ("full_name", "relationship"):
            value = str(value or "").strip()

            if len(value) < 2:
                raise ValueError(
                    f"{field} must contain at least 2 characters"
                )

            encrypted[column] = encrypt_health_text(value)

        else:
            encrypted[column] = encrypt_optional(value)

    return encrypted


def serialize_family_profile(profile):
    return {
        "id": profile.id,
        "full_name": decrypt_optional(
            profile.encrypted_full_name
        ),
        "relationship": decrypt_optional(
            profile.encrypted_relationship
        ),
        "date_of_birth": decrypt_optional(
            profile.encrypted_date_of_birth
        ),
        "blood_group": decrypt_optional(
            profile.encrypted_blood_group
        ),
        "allergies": decrypt_optional(
            profile.encrypted_allergies
        ),
        "emergency_notes": decrypt_optional(
            profile.encrypted_emergency_notes
        ),
        "created_at": (
            profile.created_at.isoformat()
            if profile.created_at else None
        ),
        "updated_at": (
            profile.updated_at.isoformat()
            if profile.updated_at else None
        ),
    }
