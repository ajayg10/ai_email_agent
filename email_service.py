# email_service.py
import os
import pickle
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from google.oauth2.credentials import Credentials

from models import EmailSummary
from sqlalchemy.orm import Session


# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Gmail API scope (use modify to mark as read)
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Initialize LangChain model (keep temperature low for deterministic output)
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.2, openai_api_key=OPENAI_API_KEY)


# Reconstructs OAuth credentials

# Uses refresh token automatically if access token expired

# Returns a user-specific Gmail client
def get_gmail_service_for_user(user):
    creds = Credentials(
        token=user.access_token,
        refresh_token=user.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    )

    return build("gmail", "v1", credentials=creds)

def gmail_authenticate():
    """Authenticate Gmail and return service object"""
    creds = None
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def get_unread_emails(service, max_results=10):
    """
    Fetch unread emails only from the Primary inbox.
    Adds message_id for dedupe. Optionally marks messages read here.
    """
    query = "category:primary is:unread"
    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])
    emails = []

    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        headers = msg_data.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h.get('name') == 'Subject'), "No Subject")
        sender = next((h['value'] for h in headers if h.get('name') == 'From'), "Unknown Sender")
        snippet = msg_data.get('snippet', "")

        # Optionally mark as read to avoid reprocessing (recommended)
        try:
            service.users().messages().modify(
                userId='me',
                id=msg['id'],
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except Exception:
            # non-fatal: continue even if marking read fails
            pass

        emails.append({
            "message_id": msg['id'],
            "from": sender,
            "subject": subject,
            "snippet": snippet
        })

    return emails


def summarize_email(email_text: str):
    """
    Ask the LLM for strict JSON: {"summary":"...","tag":"..."}.
    Returns a dict with keys 'summary' and 'tag' (always strings).
    Robust to code fences and non-JSON outputs.
    """
    prompt = (
        "Summarize this email in 3 short lines and give the email a tag with which the user can "
        "understand what the mail is about. Return ONLY valid JSON exactly like:\n"
        '{"summary":"...","tag":"..."}\n\n'
        f"Email:\n{email_text}"
    )

    resp = llm.invoke(prompt)
    raw = getattr(resp, "content", str(resp)).strip()

    # If model wrapped JSON in code fences or extra text, try to extract JSON block
    if raw.startswith("```"):
        # remove code fences
        raw = raw.strip("` \n")
        # extract {...}
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start:end+1]

    try:
        data = json.loads(raw)
        summary = (data.get("summary") or "").strip()
        tag = (data.get("tag") or "").strip()
        if not summary:
            summary = "No summary."
        if not tag:
            tag = "Uncategorized"
        return {"summary": summary, "tag": tag}
    except Exception:
        # fallback: use first ~300 chars as summary and default tag
        text = raw.replace("\n", " ").strip()
        return {"summary": (text[:300] or "No summary."), "tag": "Uncategorized"}


def generate_reply(email_text: str):
    """
    Generate a short, polite reply string using the LLM.
    Defensive: normalize output to string.
    """
    prompt = f"Write a short, polite, professional email reply to this:\n\n{email_text}"
    resp = llm.invoke(prompt)
    return getattr(resp, "content", str(resp)).strip()


def process_new_emails(max_results=10):
    """
    Fetch unread emails, summarize+tag, generate reply.
    ALWAYS return a list of dicts with keys:
      message_id, from, subject, snippet, summary, tag, suggested_reply
    """
    service = gmail_authenticate()
    raw_emails = get_unread_emails(service, max_results=max_results)

    processed = []
    for item in raw_emails:
        msg_id = item.get("message_id")
        snippet = item.get("snippet", "") or ""
        st = summarize_email(snippet)
        reply = generate_reply(snippet)
        processed.append({
            "message_id": msg_id,
            "from": item.get("from"),
            "subject": item.get("subject"),
            "snippet": snippet,
            "summary": st["summary"],
            "tag": st["tag"],
            "suggested_reply": reply
        })

    return processed


def fetch_and_summarize_for_user(
    service,
    db: Session,
    user,
    max_results: int = 5,
):
    """
    Fetch unread emails for a logged-in user,
    summarize them using LLM,
    store results in DB,
    return summaries.
    """

    results = service.users().messages().list(
        userId="me",
        q="is:unread category:primary",
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    summaries = []

    for msg in messages:
        msg_id = msg["id"]

        # 🚫 Deduplication
        exists = db.query(EmailSummary).filter(
            EmailSummary.message_id == msg_id,
            EmailSummary.user_id == user.id
        ).first()
        if exists:
            continue

        msg_data = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full"
        ).execute()

        headers = msg_data.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        snippet = msg_data.get("snippet", "")

        # 🧠 LLM summary
        summary_data = summarize_email(snippet)

        email_row = EmailSummary(
            user_id=user.id,
            message_id=msg_id,
            sender=sender,
            subject=subject,
            snippet=snippet,
            summary=summary_data["summary"],
            tag=summary_data["tag"],
        )

        db.add(email_row)

        summaries.append({
            "from": sender,
            "subject": subject,
            "summary": summary_data["summary"],
            "tag": summary_data["tag"],
        })

    db.commit()
    return summaries
