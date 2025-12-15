# main.py
from fastapi import FastAPI, Depends, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from email_service import process_new_emails
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uvicorn
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from db import engine, SessionLocal
from models import EmailSummary
from db import Base
from models import User


# -----------------------
# DATABASE CONFIG
# -----------------------
DATABASE_URL = "sqlite:///./emails.db"  # SQLite file (auto-created)

# Required for SQLite + background threads (scheduler)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session factory: every request/job should use a fresh session
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# -----------------------
# ORM MODEL (with message_id for dedupe)
# -----------------------
class EmailSummary(Base):
    __tablename__ = "email_summaries"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), unique=True, index=True, nullable=True)  # NEW: Gmail message id
    sender = Column(String(320), nullable=True)
    subject = Column(String(1024), nullable=True)
    snippet = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    suggested_reply = Column(Text, nullable=True)
    tag = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Create DB file + tables if missing
Base.metadata.create_all(bind=engine)

# -----------------------
# FASTAPI + CORS
# -----------------------
app = FastAPI(title="Email Summarizer & Replier", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # DEV only — restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# DB dependency
# -----------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------
# Scheduler (do NOT start at import time)
# -----------------------
scheduler = BackgroundScheduler()


def scheduled_fetch():
    """
    Fetch unread emails via your email_service and UPSERT into SQLite by message_id.
    - process_new_emails() must include 'message_id' in each returned dict (gmail msg id).
    - This function is resilient to fetch/save errors and will not crash the app.
    """
    print("⏰ scheduled_fetch: checking for new emails...")
    try:
        new_emails = process_new_emails()  # expects list[dict], each dict should include message_id
    except Exception as e:
        print("❌ scheduled_fetch: error fetching emails:", e)
        return

    if not new_emails:
        print("📭 scheduled_fetch: no new emails.")
        return

    print(f"✅ scheduled_fetch: found {len(new_emails)} new email(s). Saving to DB...")

    db = SessionLocal()
    system_user = get_or_create_system_user(db)
    try:
        for e in new_emails:
            # tolerate either key name
            msg_id = e.get("message_id") or e.get("gmail_message_id")
            existing = None
            if msg_id:
                existing = db.query(EmailSummary).filter(EmailSummary.message_id == msg_id).first()

            if existing:
                # update fields (optional - refresh data)
                existing.sender = e.get("from") or existing.sender
                existing.subject = e.get("subject") or existing.subject
                existing.snippet = e.get("snippet") or existing.snippet
                existing.summary = e.get("summary") or existing.summary
                existing.suggested_reply = e.get("suggested_reply") or existing.suggested_reply
                existing.tag = e.get("tag") or existing.tag
            else:
                record = EmailSummary(
                    user_id=system_user.id,
                    message_id=msg_id,
                    sender=e.get("from"),
                    subject=e.get("subject"),
                    snippet=e.get("snippet"),
                    summary=e.get("summary"),
                    suggested_reply=e.get("suggested_reply"),
                    tag=e.get("tag"),
                )
                db.add(record)
        db.commit()
        print("✅ scheduled_fetch: saved/updated emails.")
    except Exception as err:
        db.rollback()
        print("❌ scheduled_fetch: error saving emails:", err)
    finally:
        db.close()



def get_or_create_system_user(db: Session) -> User:
    user = db.query(User).filter(User.email == "system@local").first()
    if not user:
        user = User(email="system@local")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# Startup / Shutdown (start scheduler safely here)

@app.on_event("startup")
def on_startup():
    """
    Seed DB once at startup and start the scheduler here.
    This prevents duplicate schedulers when using auto-reload or multiple processes.
    """
    try:
        scheduled_fetch()  # seed DB immediately
    except Exception as e:
        print("⚠️ on_startup: initial fetch failed:", e)

    # schedule job every 10 minutes (adjust for testing)
    scheduler.add_job(scheduled_fetch, "interval", minutes=10)
    scheduler.start()
    print("🚀 Scheduler started.")


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown(wait=False)
    print("🛑 Scheduler stopped.")



# ROUTES (DB-backed)

@app.get("/fetch_emails")
def fetch_emails(db: Session = Depends(get_db)):
    """
    Return saved email summaries from the DB (newest first).
    NOTE: This reads persistent storage instead of any in-memory cache.
    """
    rows = db.query(EmailSummary).order_by(EmailSummary.id.desc()).all()
    return {
        "emails": [
            {
                "id": r.id,
                "message_id": r.message_id,
                "from": r.sender,
                "subject": r.subject,
                "snippet": r.snippet,
                "summary": r.summary,
                "suggested_reply": r.suggested_reply,
                "tag": r.tag,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


# Run server

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
