# auth.py
import os
import requests

from dotenv import load_dotenv

load_dotenv()

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow

from db import SessionLocal
from models import User

from auth_utils import create_access_token
from fastapi.responses import JSONResponse

router = APIRouter()

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.modify",
]

CLIENT_SECRETS_FILE = "credentials.json"
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/auth/google")
def google_login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )

    return RedirectResponse(authorization_url)


@router.get("/auth/google/callback")
def google_callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    flow.fetch_token(code=code)
    creds = flow.credentials

    # ✅ FIX: use requests, not request.get
    userinfo_response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {creds.token}"},
    )
    user_info = userinfo_response.json()

    google_id = user_info.get("id")
    email = user_info.get("email")

    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Invalid Google user info")

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

    
    db.refresh(user)

    # 🔐 Create JWT
    token = create_access_token({
        "user_id": user.id,
        "email": user.email
    })

    return JSONResponse({
        "access_token": token,
        "token_type": "bearer",
        "email": user.email
    })
