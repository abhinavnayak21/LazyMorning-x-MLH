from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class NoteBase(BaseModel):
    title: str
    content: str
    category: Optional[str] = "General"
    tags: Optional[str] = ""

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None

class NoteResponse(NoteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
