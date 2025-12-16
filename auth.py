# auth.py
import os
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from db import SessionLocal
from models import User

load_dotenv()

router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.modify",
]

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


"""
OAuth routes for Google login.
Handles user authentication and token persistence.
"""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        

@router.get("/auth/google")
def google_login():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )

    return RedirectResponse(authorization_url)




@router.get("/auth/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    flow.fetch_token(code=code)
    creds = flow.credentials

    oauth2_service = build("oauth2", "v2", credentials=creds)
    user_info = oauth2_service.userinfo().v2().me().get().execute()

    user = db.query(User).filter(User.google_id == user_info["id"]).first()

    if not user:
        user = User(
            email=user_info["email"],
            google_id=user_info["id"],
        )
        db.add(user)

    user.access_token = creds.token
    user.refresh_token = creds.refresh_token
    user.token_expiry = creds.expiry

    db.commit()

    return {"message": "Google login successful"}
