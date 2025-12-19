from sqlalchemy.orm import Session
from db import SessionLocal
from models import User

db: Session = SessionLocal()

users = db.query(User).all()

print("Users in DB:")
for u in users:
    print({
        "id": u.id,
        "google_id": u.google_id,
        "email": u.email,
        "access_token": bool(u.access_token),
        "refresh_token": bool(u.refresh_token),
        "created_at": u.created_at
    })

db.close()
