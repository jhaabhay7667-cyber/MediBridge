import base64
import json
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile
)
from sqlalchemy.orm import Session

from ..auth import current_user
from ..database import get_db
from ..models import MedicalReport, User

from ..services.health_data_crypto import (
    encrypt_health_text,
    decrypt_health_text
)

from ..services.report_analyzer import (
    extract_report_text,
    analyze_with_gemini
)


router = APIRouter(
    prefix="/api/reports",
    tags=["Medical Reports"]
)


MAX_UPLOAD_SIZE = 12 * 1024 * 1024

ALLOWED_FILES = {
    ".pdf": ("application/pdf", b"%PDF-"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n")
}


def get_owned_report(
    db: Session,
    report_id: int,
    user_id: int
):

    report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.user_id == user_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Medical report not found."
        )

    return report


@router.post("/analyze", status_code=201)
async def upload_and_analyze_report(
    file: UploadFile = File(...),
    language: str = Form("English"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):

    filename = (
        file.filename or "medical-report"
    ).replace("\\", "/").split("/")[-1][:255]

    extension = (
        "." + filename.rsplit(".", 1)[-1].lower()
        if "." in filename else ""
    )

    if extension not in ALLOWED_FILES:
        raise HTTPException(
            status_code=415,
            detail="Upload only PDF, JPG, JPEG or PNG files."
        )

    content = await file.read(MAX_UPLOAD_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Maximum upload size is 12 MB."
        )

    content_type, signature = ALLOWED_FILES[extension]

    if not content.startswith(signature):
        raise HTTPException(
            status_code=415,
            detail="File content does not match its extension."
        )

    try:
        extracted_text = extract_report_text(
            content,
            content_type
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=415,
            detail=str(exc)
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        ) from exc

    if len(extracted_text.strip()) < 15:
        raise HTTPException(
            status_code=422,
            detail="Not enough readable text was found in this report."
        )

    try:
        analysis = await analyze_with_gemini(
            extracted_text,
            language[:30]
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        ) from exc

    encrypted_file = encrypt_health_text(
        base64.b64encode(content).decode("ascii")
    )

    encrypted_text = encrypt_health_text(
        extracted_text
    )

    encrypted_analysis = encrypt_health_text(
        json.dumps(
            analysis,
            ensure_ascii=False
        )
    )

    report = MedicalReport(
        user_id=user.id,
        original_filename=filename,
        content_type=content_type,
        file_size=len(content),
        encrypted_file=encrypted_file,
        encrypted_extracted_text=encrypted_text,
        encrypted_analysis=encrypted_analysis,
        created_at=datetime.now(timezone.utc)
    )

    try:
        db.add(report)
        db.commit()
        db.refresh(report)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save the report."
        )

    return {
        "id": report.id,
        "filename": report.original_filename,
        "created_at": report.created_at,
        "analysis": analysis,
        "disclaimer": (
            "AI-generated information only. "
            "This is not a medical diagnosis. "
            "Please consult a qualified doctor."
        )
    }


@router.get("")
def get_my_reports(
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):

    reports = (
        db.query(MedicalReport)
        .filter(MedicalReport.user_id == user.id)
        .order_by(MedicalReport.created_at.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": report.id,
            "filename": report.original_filename,
            "content_type": report.content_type,
            "file_size": report.file_size,
            "created_at": report.created_at
        }
        for report in reports
    ]


@router.get("/{report_id}")
def get_report_details(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):

    report = get_owned_report(
        db,
        report_id,
        user.id
    )

    analysis_text = decrypt_health_text(
        report.encrypted_analysis
    )

    analysis = json.loads(analysis_text)

    return {
        "id": report.id,
        "filename": report.original_filename,
        "content_type": report.content_type,
        "created_at": report.created_at,
        "analysis": analysis
    }


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):

    report = get_owned_report(
        db,
        report_id,
        user.id
    )

    db.delete(report)
    db.commit()

    return None