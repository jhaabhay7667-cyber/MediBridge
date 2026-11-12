
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import current_user
from ..database import get_db
from ..models import SymptomAssessment, User
from ..services.health_data_crypto import (
    encrypt_health_text,
    decrypt_health_text
)
from ..services.symptom_checker import analyze_symptoms


router = APIRouter(
    prefix="/api/symptoms",
    tags=["AI Symptom Checker"]
)


class SymptomRequest(BaseModel):
    symptoms: str = Field(min_length=10, max_length=3000)
    age: Optional[int] = Field(default=None, ge=0, le=120)
    duration: str = Field(default="Not provided", max_length=100)
    severity: int = Field(ge=1, le=10)
    language: str = Field(default="English", min_length=2, max_length=30)


def get_owned_assessment(
    db: Session,
    assessment_id: int,
    user_id: int
):
    record = (
        db.query(SymptomAssessment)
        .filter(
            SymptomAssessment.id == assessment_id,
            SymptomAssessment.user_id == user_id
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Symptom assessment not found."
        )

    return record


@router.post("/check", status_code=201)
async def check_symptoms(
    payload: SymptomRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    try:
        result = await analyze_symptoms(
            symptoms=payload.symptoms,
            age=payload.age,
            duration=payload.duration,
            severity=payload.severity,
            language=payload.language
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        ) from exc

    input_data = payload.model_dump()

    record = SymptomAssessment(
        user_id=user.id,
        encrypted_input=encrypt_health_text(
            json.dumps(input_data, ensure_ascii=False)
        ),
        encrypted_result=encrypt_health_text(
            json.dumps(result, ensure_ascii=False)
        ),
        urgency=result["urgency"],
        created_at=datetime.now(timezone.utc)
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save symptom assessment."
        ) from exc

    return {
        "id": record.id,
        "created_at": record.created_at,
        "result": result
    }


@router.get("")
def get_my_assessments(
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    records = (
        db.query(SymptomAssessment)
        .filter(SymptomAssessment.user_id == user.id)
        .order_by(SymptomAssessment.created_at.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": record.id,
            "urgency": record.urgency,
            "created_at": record.created_at
        }
        for record in records
    ]


@router.get("/{assessment_id}")
def get_assessment_details(
    assessment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    record = get_owned_assessment(
        db,
        assessment_id,
        user.id
    )

    try:
        input_data = json.loads(
            decrypt_health_text(record.encrypted_input)
        )
        result = json.loads(
            decrypt_health_text(record.encrypted_result)
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not read saved assessment."
        ) from exc

    return {
        "id": record.id,
        "created_at": record.created_at,
        "input": input_data,
        "result": result
    }


@router.delete("/{assessment_id}", status_code=204)
def delete_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    record = get_owned_assessment(
        db,
        assessment_id,
        user.id
    )

    db.delete(record)
    db.commit()

    return None
