import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.briefing import Briefing
from backend.app.schemas.briefing import BriefingResponse, BriefingGenerateRequest
from backend.app.services.briefing_service import BriefingService

router = APIRouter(prefix="/api/briefings", tags=["Briefings"])

def to_briefing_response(b: Briefing) -> BriefingResponse:
    try:
        top_prios = json.loads(b.top_priorities_json) if b.top_priorities_json else []
    except Exception:
        top_prios = []

    try:
        deadlines = json.loads(b.upcoming_deadlines_json) if b.upcoming_deadlines_json else []
    except Exception:
        deadlines = []

    try:
        unfinished = json.loads(b.unfinished_items_json) if b.unfinished_items_json else []
    except Exception:
        unfinished = []

    return BriefingResponse(
        id=b.id,
        todays_focus=b.todays_focus,
        top_priorities=top_prios,
        upcoming_deadlines=deadlines,
        unfinished_items=unfinished,
        suggested_first_step=b.suggested_first_step,
        raw_markdown=b.raw_markdown or "",
        model_used=b.model_used,
        source=b.source,
        generated_at=b.generated_at
    )

@router.get("", response_model=List[BriefingResponse])
def list_briefings(limit: int = Query(30, ge=1, le=100), db: Session = Depends(get_db)):
    briefings = BriefingService.get_briefing_history(db, limit=limit)
    return [to_briefing_response(b) for b in briefings]

@router.get("/latest", response_model=Optional[BriefingResponse])
def get_latest_briefing(db: Session = Depends(get_db)):
    briefing = BriefingService.get_latest_briefing(db)
    if not briefing:
        return None
    return to_briefing_response(briefing)

@router.get("/{briefing_id}", response_model=BriefingResponse)
def get_briefing(briefing_id: int, db: Session = Depends(get_db)):
    briefing = BriefingService.get_briefing_by_id(db, briefing_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return to_briefing_response(briefing)

@router.post("/generate", response_model=BriefingResponse, status_code=status.HTTP_201_CREATED)
def generate_briefing(
    payload: Optional[BriefingGenerateRequest] = None,
    db: Session = Depends(get_db)
):
    force_fallback = payload.force_fallback if payload else False
    briefing = BriefingService.generate_briefing(db, force_fallback=force_fallback)
    return to_briefing_response(briefing)
