from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models.imported_file import ImportedFile
from backend.app.schemas.imported_file import ImportedFileResponse, FileApproveRequest
from backend.app.services.file_service import FileService

router = APIRouter(prefix="/api/files", tags=["Files"])

@router.get("", response_model=List[ImportedFileResponse])
def list_files(
    file_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ImportedFile)
    if file_type and file_type != "All Types":
        query = query.filter(ImportedFile.file_type.ilike(file_type))
    if search:
        s = f"%{search}%"
        query = query.filter(ImportedFile.filename.ilike(s))
    return query.order_by(ImportedFile.imported_at.desc()).all()

@router.post("/scan", response_model=List[ImportedFileResponse])
def scan_files(db: Session = Depends(get_db)):
    return FileService.scan_and_sync_files(db)

@router.post("/upload", response_model=ImportedFileResponse)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = Path(file.filename).suffix.lower()
    if ext not in [".txt", ".md"]:
        raise HTTPException(status_code=400, detail="Only .txt and .md files are allowed.")

    imports_dir = Path(settings.IMPORTS_DIR).resolve()
    imports_dir.mkdir(parents=True, exist_ok=True)
    target_path = imports_dir / file.filename

    # Read content
    content_bytes = await file.read()
    content_str = content_bytes.decode("utf-8", errors="replace")

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content_str)

    # Sync and return
    FileService.scan_and_sync_files(db)
    record = db.query(ImportedFile).filter(ImportedFile.filename == file.filename).first()
    return record

@router.patch("/{file_id}/approve", response_model=ImportedFileResponse)
def approve_file(file_id: int, payload: FileApproveRequest, db: Session = Depends(get_db)):
    try:
        return FileService.approve_file(db, file_id, payload.is_approved)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: int, db: Session = Depends(get_db)):
    success = FileService.delete_file(db, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File record not found")
    return None
