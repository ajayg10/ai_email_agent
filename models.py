# models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from db import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, index=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    emails = relationship("EmailSummary", back_populates="user")
    

class EmailSummary(Base):
    __tablename__ = "email_summaries"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), unique=True, index=True, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    sender = Column(String(320), nullable=True)
    subject = Column(String(1024), nullable=True)
    snippet = Column(Text, nullable=True)

    summary = Column(Text, nullable=True)
    suggested_reply = Column(Text, nullable=True)
    tag = Column(String(128), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="emails")
