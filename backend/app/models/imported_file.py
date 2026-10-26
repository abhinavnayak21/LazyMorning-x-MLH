from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from backend.app.database import Base

class ImportedFile(Base):
    __tablename__ = "imported_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    file_type = Column(String(10), default="TXT")     # TXT or MD
    file_size_str = Column(String(50), default="0 KB")
    content_preview = Column(String(500), default="")
    full_content = Column(Text, default="")
    is_approved = Column(Boolean, default=False)       # Approval gate!
    imported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
