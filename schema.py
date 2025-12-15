# schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EmailCreate(BaseModel):
    sender: str
    subject: str
    snippet: Optional[str] = None
    summary: Optional[str] = None
    tag: Optional[str] = None

class EmailOut(BaseModel):
    id: int
    sender: str
    subject: str
    snippet: Optional[str] = None
    summary: Optional[str] = None
    tag: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True # pydantic v2

