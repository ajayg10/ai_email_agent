from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

    access_token = Column(String)
    refresh_token = Column(String)
    token_expiry = Column(DateTime)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    emails = relationship("EmailSummary", back_populates="user")


class EmailSummary(Base):
    __tablename__ = "email_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    message_id = Column(String, unique=True, index=True)
    sender = Column(String)
    subject = Column(String)
    snippet = Column(Text)
    summary = Column(Text)
    suggested_reply = Column(Text)
    tag = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="emails")
