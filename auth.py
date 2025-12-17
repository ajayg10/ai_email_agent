# auth.py
import os
from urllib import request
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi import Request, HTTPException, Depends
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from db import SessionLocal
from models import User

load_dotenv()

router = APIRouter()

SCOPES = [
    "openid",
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
def google_callback(request: Request , db: Session = Depends(get_db)):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
    )

    flow.fetch_token(code=code)
    creds = flow.credentials

    # Fetch user info
    userinfo_response = request.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {creds.token}"},
    )
    user_info = userinfo_response.json()

    google_id = user_info.get("id")
    email = user_info.get("email")

    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Invalid Google user info")

    # Find or create user
    user = db.query(User).filter(User.google_id == google_id).first()

    if not user:
        user = User(
            google_id=google_id,
            email=email,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_expiry=creds.expiry,
        )
        db.add(user)
    else:
        user.access_token = creds.token
        user.refresh_token = creds.refresh_token
        user.token_expiry = creds.expiry

    db.commit()

    return RedirectResponse(url="/docs")

