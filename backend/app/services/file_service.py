import os
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models.imported_file import ImportedFile

def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

class FileService:
    @staticmethod
    def scan_and_sync_files(db: Session) -> List[ImportedFile]:
        """
        Scan imports/ folder for .txt and .md files.
        Add newly discovered files to the database with is_approved=False.
        """
        imports_dir = Path(settings.IMPORTS_DIR).resolve()
        imports_dir.mkdir(parents=True, exist_ok=True)

        existing_paths = {f.filepath: f for f in db.query(ImportedFile).all()}
        discovered_files = []

        for item in imports_dir.iterdir():
            if item.is_file() and item.suffix.lower() in [".txt", ".md"]:
                resolved_path = str(item.resolve())
                try:
                    size_bytes = item.stat().st_size
                    size_str = format_file_size(size_bytes)
                    ext = item.suffix.lstrip(".").upper()

                    with open(item, "r", encoding="utf-8", errors="replace") as f:
                        full_content = f.read()

                    preview = full_content[:300].strip().replace("\n", " ")

                    if resolved_path in existing_paths:
                        file_record = existing_paths[resolved_path]
                        file_record.file_size_str = size_str
                        file_record.content_preview = preview
                        file_record.full_content = full_content
                    else:
                        file_record = ImportedFile(
                            filename=item.name,
                            filepath=resolved_path,
                            file_type=ext,
                            file_size_str=size_str,
                            content_preview=preview,
                            full_content=full_content,
                            is_approved=False  # Requires explicit user approval
                        )
                        db.add(file_record)
                    discovered_files.append(file_record)
                except Exception as e:
                    print(f"Error reading file {item}: {e}")

        db.commit()
        return db.query(ImportedFile).order_by(ImportedFile.imported_at.desc()).all()

    @staticmethod
    def approve_file(db: Session, file_id: int, is_approved: bool) -> ImportedFile:
        file_record = db.query(ImportedFile).filter(ImportedFile.id == file_id).first()
        if not file_record:
            raise ValueError(f"File with id {file_id} not found")
        file_record.is_approved = is_approved
        db.commit()
        db.refresh(file_record)
        return file_record

    @staticmethod
    def get_approved_files(db: Session) -> List[ImportedFile]:
        return db.query(ImportedFile).filter(ImportedFile.is_approved == True).all()

    @staticmethod
    def delete_file(db: Session, file_id: int) -> bool:
        file_record = db.query(ImportedFile).filter(ImportedFile.id == file_id).first()
        if not file_record:
            return False
        # If the file exists on disk, remove it as well
        try:
            p = Path(file_record.filepath)
            if p.exists() and p.is_file():
                p.unlink()
        except Exception:
            pass
        db.delete(file_record)
        db.commit()
        return True
