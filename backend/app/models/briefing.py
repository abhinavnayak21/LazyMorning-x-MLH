from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.app.database import Base

class Briefing(Base):
    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True, index=True)
    todays_focus = Column(Text, nullable=False)
    top_priorities_json = Column(Text, default="[]")       # JSON array of {rank, title, tag, note}
    upcoming_deadlines_json = Column(Text, default="[]")   # JSON array of {title, due, priority}
    unfinished_items_json = Column(Text, default="[]")     # JSON array of strings
    suggested_first_step = Column(Text, nullable=False)
    raw_markdown = Column(Text, default="")
    model_used = Column(String(100), default="fallback")
    source = Column(String(50), default="fallback")        # "ai" or "fallback"
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
