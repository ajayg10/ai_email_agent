from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from db import Base, engine, SessionLocal
from models import User, EmailSummary
from auth import router as auth_router
from email_service import process_new_emails

# -----------------------
# APP
# -----------------------
app = FastAPI(title="Email Summarizer & Replier", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# -----------------------
# DB
# -----------------------
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------
# ROUTES
# -----------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/fetch_emails")
def fetch_emails(db: Session = Depends(get_db)):
    rows = db.query(EmailSummary).order_by(EmailSummary.created_at.desc()).all()
    return {
        "emails": [
            {
                "from": r.sender,
                "subject": r.subject,
                "summary": r.summary,
                "tag": r.tag,
                "suggested_reply": r.suggested_reply,
            }
            for r in rows
        ]
    }

@app.get("/run_summary_once")
def run_summary_once(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found")

    summaries = process_new_emails()

    from models import EmailSummary

    for e in summaries:
        exists = db.query(EmailSummary).filter(
            EmailSummary.message_id == e["message_id"]
        ).first()

        if exists:
            continue

        db.add(
            EmailSummary(
                user_id=user.id,
                message_id=e["message_id"],
                sender=e["from"],
                subject=e["subject"],
                snippet=e["snippet"],
                summary=e["summary"],
                tag=e["tag"],
                suggested_reply=e["suggested_reply"],
            )
        )

    db.commit()
    return {"status": "summarized", "count": len(summaries)}



@app.get("/my/summaries")
def get_my_summaries(db: Session = Depends(get_db)):
    rows = (
        db.query(EmailSummary)
        .order_by(EmailSummary.created_at.desc())
        .all()
    )

    return [
        {
            "from": r.sender,
            "subject": r.subject,
            "summary": r.summary,
            "tag": r.tag,
            "reply": r.suggested_reply,
        }
        for r in rows
    ]
