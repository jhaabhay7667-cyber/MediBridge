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
