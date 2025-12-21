# 📧 Email AI Agent

An **AI-powered Email Summarizer & Reply Generator** that connects to Gmail, automatically fetches unread emails, summarizes them using an LLM, tags them intelligently, and suggests professional replies — all in one clean dashboard.

Built with **FastAPI**, **Google OAuth**, **Gmail API**, **LangChain**, **OpenAI**, **SQLite**, and a **React (Vite) frontend**.

---

## ✨ Features

- 🔐 Google OAuth 2.0 login
- 📥 Fetch unread emails from Gmail (Primary inbox)
- 🧠 AI-powered email summarization
- 🏷️ Smart email tagging (e.g. Work, Finance, Urgent)
- ✍️ AI-generated suggested replies
- 💾 Persistent storage using SQLite
- 🕒 Background scheduler to auto-fetch emails
- 🎨 Modern React frontend UI
- 🧪 Swagger API docs via FastAPI

---

## 🧱 Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- SQLite
- Google OAuth 2.0
- Gmail API
- LangChain
- OpenAI API
- APScheduler

### Frontend
- React (Vite)
- Fetch API
- CSS / modern UI components

---

## 📂 Project Structure

Email AI Agent/
│
├── email-ai-agent/ # Frontend (React)
│ ├── src/
│ │ ├── App.jsx
│ │ ├── index.css
│ │ └── main.jsx
│ ├── index.html
│ └── package.json
│
├── auth.py # Google OAuth logic
├── auth_utils.py # JWT utilities
├── email_service.py # Gmail + AI logic
├── models.py # SQLAlchemy models
├── db.py # Database config
├── main.py # FastAPI app entry
├── credentials.json # Google OAuth credentials
├── .env # Environment variables
└── README.md

---

## 🔐 Environment Variables

Create a `.env` file in the backend root:

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_jwt_secret

▶️ How to Run Locally

1️⃣ Backend Setup
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload


Backend will run at:

http://localhost:8000


Swagger Docs:

http://localhost:8000/docs

2️⃣ Frontend Setup
cd email-ai-agent
npm install
npm run dev


Frontend runs at:

http://localhost:5173

🔄 Authentication Flow

User clicks Login with Google

Redirects to Google OAuth consent screen

Google redirects back to backend callback

Backend:

Fetches Gmail tokens

Stores them securely

Issues a JWT access token

Frontend stores token and fetches summaries


📌 Current Limitations

Gmail Primary inbox only

No pagination yet

Single-user focus (multi-user support planned)

SQLite used for simplicity

🚀 Future Improvements

Multi-user dashboard

Pagination & filters

Email search

Reply sending from UI

Dark mode

Production-ready auth (refresh tokens, expiry handling)

PostgreSQL support

🤝 Contribution

This project is currently under active development.
Feel free to fork, suggest improvements, or raise issues.

🧑‍💻 Author

Ajay
3rd Year B.Tech CSE (Cloud Computing)
