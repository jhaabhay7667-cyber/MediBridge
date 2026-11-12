
import base64
import os

import httpx
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from ..auth import current_user
from ..database import get_db
from ..models import WoundAssessment, User
from ..services.health_data_crypto import (
    encrypt_health_text,
    decrypt_health_text,
)
from ..services.wound_analyzer import analyze_wound_image


router = APIRouter(
    prefix="/api/wounds",
    tags=["wound-image-observation"],
)

MAX_IMAGE_SIZE = 5 * 1024 * 1024

ALLOWED_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
}


def validate_image(content: bytes, content_type: str):
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG and PNG images are supported.",
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty.",
        )

    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image must be 5 MB or smaller.",
        )

    is_jpeg = (
        content_type == "image/jpeg"
        and content.startswith(b"\xff\xd8\xff")
    )

    is_png = (
        content_type == "image/png"
        and content.startswith(b"\x89PNG\r\n\x1a\n")
    )

    if not (is_jpeg or is_png):
        raise HTTPException(
            status_code=400,
            detail="The file content does not match a supported image format.",
        )


@router.post("/analyze")
async def create_wound_assessment(
    file: UploadFile = File(...),
    consent: bool = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if not consent:
        raise HTTPException(
            status_code=400,
            detail="Consent is required before image analysis.",
        )

    content_type = (file.content_type or "").lower()

    # Read one byte over the limit to detect oversized files.
    image_bytes = await file.read(MAX_IMAGE_SIZE + 1)

    validate_image(image_bytes, content_type)

    try:
        result = await analyze_wound_image(
            image_bytes,
            content_type,
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="The AI image service returned an error. Please try later.",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="The AI image service is temporarily unavailable.",
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to analyze this image right now.",
        )

    safe_filename = os.path.basename(file.filename or "uploaded-image")
    safe_filename = safe_filename[:255]

    encrypted_image = encrypt_health_text(
        base64.b64encode(image_bytes).decode("utf-8")
    )

    encrypted_result = encrypt_health_text(result)

    record = WoundAssessment(
        user_id=user.id,
        original_filename=safe_filename,
        content_type=content_type,
        encrypted_image=encrypted_image,
        encrypted_result=encrypted_result,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "filename": record.original_filename,
        "result": result,
        "created_at": record.created_at,
        "disclaimer": (
            "AI-generated visual observations are not a diagnosis. "
            "A photograph cannot reliably confirm infection, disease "
            "or wound severity. Seek professional medical advice."
        ),
    }


@router.get("/")
def list_wound_assessments(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    records = (
        db.query(WoundAssessment)
        .filter(WoundAssessment.user_id == user.id)
        .order_by(WoundAssessment.created_at.desc())
        .limit(100)
        .all()
    )

    return {
        "count": len(records),
        "assessments": [
            {
                "id": item.id,
                "filename": item.original_filename,
                "created_at": item.created_at,
            }
            for item in records
        ],
    }


@router.get("/{assessment_id}")
def get_wound_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    record = (
        db.query(WoundAssessment)
        .filter(
            WoundAssessment.id == assessment_id,
            WoundAssessment.user_id == user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Wound assessment not found.",
        )

    return {
        "id": record.id,
        "filename": record.original_filename,
        "result": decrypt_health_text(record.encrypted_result),
        "created_at": record.created_at,
        "disclaimer": (
            "This is an AI-generated visual observation, not a diagnosis."
        ),
    }


@router.delete("/{assessment_id}")
def delete_wound_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    record = (
        db.query(WoundAssessment)
        .filter(
            WoundAssessment.id == assessment_id,
            WoundAssessment.user_id == user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Wound assessment not found.",
        )

    db.delete(record)
    db.commit()

    return {"message": "Wound assessment deleted successfully."}
