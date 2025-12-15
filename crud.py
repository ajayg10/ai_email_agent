# crud.py
from sqlalchemy.orm import Session
from models import Email
from schemas import EmailCreate
from typing import List, Optional

def create_email(db: Session, data: EmailCreate) -> Email:
    obj = Email(
        sender=data.sender,
        subject=data.subject,
        snippet=data.snippet,
        summary=data.summary,
        tag=data.tag,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_emails(db: Session, skip: int = 0, limit: int = 50) -> List[Email]:
    return db.query(Email).order_by(Email.id.desc()).offset(skip).limit(limit).all()

def get_email(db: Session, email_id: int) -> Optional[Email]:
    return db.query(Email).filter(Email.id == email_id).first()

def delete_email(db: Session, email_id: int) -> bool:
    obj = db.query(Email).filter(Email.id == email_id).first()
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
