from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class PriorityItem(BaseModel):
    rank: int
    title: str
    tag: str   # e.g. "Due today - High priority"
    note: str  # e.g. "This is critical for the client meeting."

class DeadlineItem(BaseModel):
    title: str
    due: str
    priority: str  # High, Medium, Low

class BriefingResponse(BaseModel):
    id: int
    todays_focus: str
    top_priorities: List[PriorityItem]
    upcoming_deadlines: List[DeadlineItem]
    unfinished_items: List[str]
    suggested_first_step: str
    raw_markdown: Optional[str] = ""
    model_used: str
    source: str  # "ai" or "fallback"
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BriefingGenerateRequest(BaseModel):
    force_fallback: Optional[bool] = False
    custom_instruction: Optional[str] = None
