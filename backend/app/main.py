import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.models.note import Note
from backend.app.models.task import Task
from backend.app.models.briefing import Briefing
from backend.app.models.imported_file import ImportedFile
from backend.app.services.file_service import FileService
from backend.app.services.briefing_service import BriefingService
from backend.app.services.scheduler_service import scheduler_service
from backend.app.routers import notes, tasks, files, briefings, settings as settings_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LazyMorning")

def seed_initial_data_if_empty():
    db = SessionLocal()
    try:
        # Check notes
        if db.query(Note).count() == 0:
            logger.info("Seeding initial notes matching design mockup...")
            sample_notes = [
                Note(
                    title="Project Ideas",
                    content="Some ideas for the new feature architecture, calm UI design, and offline AI briefing loops.",
                    category="Work",
                    tags="Work, Ideas"
                ),
                Note(
                    title="Meeting Notes",
                    content="Key points from today's alignment meeting: finalize proposal by 5 PM, incorporate stakeholder feedback.",
                    category="Work",
                    tags="Work, Meeting"
                ),
                Note(
                    title="Personal Goals",
                    content="Things I want to achieve this year: read 12 books, walk 10,000 steps daily, maintain morning calm.",
                    category="Personal",
                    tags="Personal, Goals"
                ),
                Note(
                    title="Book Notes",
                    content="Key takeaways from Atomic Habits: optimize environment, focus on systems instead of rigid goals.",
                    category="Learning",
                    tags="Learning, Books"
                )
            ]
            db.add_all(sample_notes)
            db.commit()

        # Check tasks
        if db.query(Task).count() == 0:
            logger.info("Seeding initial tasks matching design mockup...")
            sample_tasks = [
                Task(
                    title="Finish project proposal",
                    description="This is critical for the client meeting. Finalize key figures and submission draft.",
                    priority="High",
                    due_date="Today, 5:00 PM",
                    is_done=False
                ),
                Task(
                    title="Review client feedback",
                    description="Incorporate changes and finalize responses before the team sync.",
                    priority="High",
                    due_date="Today",
                    is_done=False
                ),
                Task(
                    title="Prepare meeting materials",
                    description="Create slides and talking points for tomorrow's 10:00 AM stakeholder sync.",
                    priority="Medium",
                    due_date="Tomorrow",
                    is_done=False
                ),
                Task(
                    title="Update documentation",
                    description="Ensure API routes, schemas, and markdown docs are refreshed.",
                    priority="Low",
                    due_date="Oct 22",
                    is_done=False
                ),
                Task(
                    title="Read research paper",
                    description="Study recent advances in local quantized open-weight LLMs.",
                    priority="Low",
                    due_date="Oct 25",
                    is_done=False
                ),
                Task(
                    title="Review weekly team roadmap",
                    description="Discuss progress on sprint goals and identify blockers.",
                    priority="Medium",
                    due_date="Yesterday",
                    is_done=True
                )
            ]
            db.add_all(sample_tasks)
            db.commit()

        # Sync files
        FileService.scan_and_sync_files(db)

        # Approve sample meeting notes for instant context
        m_file = db.query(ImportedFile).filter(ImportedFile.filename == "meeting-notes.txt").first()
        if m_file:
            m_file.is_approved = True
            db.commit()

        # Check initial briefing
        if db.query(Briefing).count() == 0:
            logger.info("Generating initial morning briefing...")
            BriefingService.generate_briefing(db)

    except Exception as e:
        logger.error(f"Error seeding data: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed
    Base.metadata.create_all(bind=engine)
    seed_initial_data_if_empty()

    # Start scheduler if enabled
    if settings.ENABLE_SCHEDULE:
        try:
            scheduler_service.start()
        except Exception as e:
            logger.warning(f"Could not start scheduler: {e}")

    yield

    # Shutdown
    scheduler_service.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Your Overnight Life Assistant — Automated Local AI Morning Briefings",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes.router)
app.include_router(tasks.router)
app.include_router(files.router)
app.include_router(briefings.router)
app.include_router(settings_router.router)

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "tagline": settings.PROJECT_TAGLINE,
        "status": "online",
        "docs": "/docs"
    }
