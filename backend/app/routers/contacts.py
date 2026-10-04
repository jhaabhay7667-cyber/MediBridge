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
