import { useEffect, useState } from "react";
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

// attach JWT automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function App() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);

  // 🔐 handle redirect token
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");

    if (token) {
      localStorage.setItem("access_token", token);
      setLoggedIn(true);
      window.history.replaceState({}, "", "/");
    } else {
      const existing = localStorage.getItem("access_token");
      if (existing) setLoggedIn(true);
    }
  }, []);

  // 🔵 login
  const loginWithGoogle = () => {
    window.location.href = "http://localhost:8000/auth/google";
  };

  // 📥 fetch summaries
  const fetchSummaries = async () => {
    try {
      setLoading(true);
      const res = await api.get("/fetch_emails");
      console.log("BACKEND RESPONSE:", res.data);
      setEmails(res.data.emails ?? []);
    } catch (err) {
      console.error(err);
      alert("Failed to fetch summaries");
    } finally {
      setLoading(false);
    }
  };

  // 🔴 logout
  const logout = () => {
    localStorage.removeItem("access_token");
    setEmails([]);
    setLoggedIn(false);
  };

  return (
    <div style={{ padding: 20, fontFamily: "Arial" }}>
      
      <h2 style={{
  fontSize: "1.8rem",
  fontWeight: 700,
  marginBottom: 20,
}}>Email AI Agent</h2>

      {!loggedIn ? (
        <button  o
style={{
    padding: "10px 18px",
    borderRadius: 10,
    border: "none",
    background: "linear-gradient(90deg, #22c55e, #16a34a)",
    color: "white",
    fontWeight: 600,
    fontSize: 14,
    cursor: "pointer",
    boxShadow: "0 6px 18px rgba(34,197,94,0.45)",
    transition: "transform 0.2s ease, box-shadow 0.2s ease",
  }}
  onMouseEnter={e => {
    e.target.style.transform = "translateY(-2px)";
    e.target.style.boxShadow = "0 10px 24px rgba(34,197,94,0.6)";
  }}
  onMouseLeave={e => {
    e.target.style.transform = "translateY(0)";
    e.target.style.boxShadow = "0 6px 18px rgba(34,197,94,0.45)";
  }}onClick={loginWithGoogle}>
          Login with Google
        </button>
      ) : (
        <>
          <button onClick={logout} style={{
    padding: "8px 14px",
    borderRadius: 8,
    border: "1px solid #ef4444",
    background: "transparent",
    color: "#ef4444",
    fontWeight: 600,
    fontSize: 13,
    cursor: "pointer",
    transition: "all 0.2s ease",
  }}
  onMouseEnter={e => {
    e.target.style.background = "#fee2e2";
  }}
  onMouseLeave={e => {
    e.target.style.background = "transparent";
  }}>
            Logout 
          </button>

          <button style={{
    padding: "10px 16px",
    borderRadius: 8,
    border: "none",
    background: "linear-gradient(90deg, #6366f1, #8b5cf6)",
    color: "white",
    fontWeight: 600,
    cursor: "pointer",
    boxShadow: "0 6px 16px rgba(99,102,241,0.4)"
  }} onClick={fetchSummaries}>
            Fetch Summaries
          </button>
        </>
      )}

      <hr />

      <p><strong>Emails count:</strong> {emails.length}</p>

      {loading && <p>Loading summaries...</p>}

      {!loading && emails.length === 0 && loggedIn && (
        <p>No summaries yet</p>
      )}

      {emails.map((email) => (
  <div
    
  key={email.id}
  className="email-card"
>

    {/* SUBJECT */}
    <h3 style={{
  marginBottom: 6,
  fontSize: "1.1rem",
  fontWeight: 600,
  color: "#111827"
}}>Subject: &nbsp;
  {email.subject || "No Subject"}
</h3>

    {/* SUMMARY */}
    <p> Summary:
      {email.summary
        ? email.summary
        : "No summary generated"}
    </p>

    {/* SUGGESTED REPLY */}
    <div
  style={{
    background: "#f9fafb",
    borderLeft: "4px solid #6366f1",
    padding: 12,
    borderRadius: 8,
    marginTop: 10,
  }}
>
  <strong style={{ color: "#4f46e5" }}>
    Suggested Reply
  </strong>
  <p style={{ marginTop: 6 }}>
    {email.suggested_reply || "No reply generated"}
  </p>
</div>

    {/* TAG */}
    <span
  style={{
    display: "inline-block",
    background: "#e0e7ff",
    color: "#3730a3",
    padding: "4px 10px",
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 500,
    marginTop: 8,
  }}
>Tag: &nbsp;
  {email.tag || "General"}
</span>
  </div>
))}
    </div>

  );
}

export default App;