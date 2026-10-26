from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ImportedFileResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    file_type: str
    file_size_str: str
    content_preview: str
    is_approved: bool
    imported_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FileApproveRequest(BaseModel):
    is_approved: bool
