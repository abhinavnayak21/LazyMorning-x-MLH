import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.note import Note
from backend.app.models.task import Task
from backend.app.models.imported_file import ImportedFile
from backend.app.models.briefing import Briefing
from backend.app.services.ai_service import ai_service
from backend.app.utils.validators import parse_ai_briefing_response

class BriefingService:
    @staticmethod
    def collect_context(db: Session) -> Dict[str, Any]:
        """Collect all relevant context for morning briefing."""
        # 1. Tasks
        all_tasks = db.query(Task).all()
        pending_tasks = [t for t in all_tasks if not t.is_done]
        completed_tasks = [t for t in all_tasks if t.is_done]

        # Sort pending: High > Medium > Low
        priority_order = {"high": 1, "medium": 2, "low": 3}
        pending_tasks.sort(key=lambda t: priority_order.get((t.priority or "medium").lower(), 2))

        # 2. Notes
        notes = db.query(Note).order_by(Note.updated_at.desc()).limit(10).all()

        # 3. Approved files ONLY (security & privacy approval gate)
        approved_files = db.query(ImportedFile).filter(ImportedFile.is_approved == True).all()

        return {
            "all_tasks": all_tasks,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "notes": notes,
            "approved_files": approved_files
        }

    @staticmethod
    def generate_fallback(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligent, 100% offline rule-based briefing generator.
        Runs when Ollama is offline or unavailable.
        Zero hallucinations, strictly derives from DB records.
        """
        pending: List[Task] = context["pending_tasks"]
        notes: List[Note] = context["notes"]
        files: List[ImportedFile] = context["approved_files"]

        # 1. Today's Focus
        if pending:
            top_titles = [t.title for t in pending[:2]]
            if len(top_titles) == 1:
                todays_focus = f"Focus on making steady progress on '{top_titles[0]}' while maintaining calm momentum."
            else:
                todays_focus = f"Focus on completing {top_titles[0]} and advancing {top_titles[1]} today."
        elif notes:
            todays_focus = f"Review your recent notes on '{notes[0].title}' and plan your upcoming priorities."
        else:
            todays_focus = "Take a moment to plan your day, add your priorities, and start with a clear, peaceful mind."

        # 2. Top 3 Priorities
        top_priorities = []
        for idx, task in enumerate(pending[:3], 1):
            prio = task.priority.capitalize() if task.priority else "Medium"
            due = task.due_date if task.due_date else "Today"
            tag = f"Due {due} - {prio} priority"
            note = task.description if task.description else f"Essential {prio.lower()} priority item to move forward."
            top_priorities.append({
                "rank": idx,
                "title": task.title,
                "tag": tag,
                "note": note
            })

        # 3. Upcoming Deadlines
        upcoming_deadlines = []
        for task in pending:
            if task.due_date:
                upcoming_deadlines.append({
                    "title": task.title,
                    "due": task.due_date,
                    "priority": task.priority.capitalize() if task.priority else "Medium"
                })
            if len(upcoming_deadlines) >= 4:
                break

        # If no explicit deadlines in pending tasks
        if not upcoming_deadlines and pending:
            for task in pending[:2]:
                upcoming_deadlines.append({
                    "title": task.title,
                    "due": task.due_date or "No deadline set",
                    "priority": task.priority.capitalize() if task.priority else "Medium"
                })

        # 4. Unfinished Items
        unfinished_items = [t.title for t in pending[3:8]] if len(pending) > 3 else [t.title for t in pending]
        if not unfinished_items:
            unfinished_items = ["All recorded tasks are completed! Enjoy the breathing room."]

        # 5. Suggested First Step
        if pending:
            first_task = pending[0]
            suggested_first_step = (
                f"Open '{first_task.title}' and spend just 10 minutes getting started on it. "
                "A gentle first step builds easy momentum without morning friction."
            )
        elif notes:
            suggested_first_step = f"Read through '{notes[0].title}' and extract one small action item for today."
        else:
            suggested_first_step = "Create your top 3 tasks for today and enjoy your morning coffee."

        raw_markdown = f"""### Today's Focus
{todays_focus}

### Top Priorities
""" + "\n".join([f"{p['rank']}. **{p['title']}** ({p['tag']}) — {p['note']}" for p in top_priorities]) + f"""

### Upcoming Deadlines
""" + "\n".join([f"- **{d['title']}**: {d['due']} [{d['priority']}]" for d in upcoming_deadlines]) + f"""

### Unfinished Items
""" + "\n".join([f"- {item}" for item in unfinished_items]) + f"""

### Suggested First Step
{suggested_first_step}
"""

        return {
            "todays_focus": todays_focus,
            "top_priorities": top_priorities,
            "upcoming_deadlines": upcoming_deadlines,
            "unfinished_items": unfinished_items,
            "suggested_first_step": suggested_first_step,
            "raw_markdown": raw_markdown,
            "model_used": "local-fallback",
            "source": "fallback"
        }

    @classmethod
    def generate_briefing(cls, db: Session, force_fallback: bool = False) -> Briefing:
        """Generate a briefing using AI if available, or graceful offline fallback."""
        context = cls.collect_context(db)
        pending: List[Task] = context["pending_tasks"]
        notes: List[Note] = context["notes"]
        files: List[ImportedFile] = context["approved_files"]

        used_ai = False
        briefing_dict = None

        if not force_fallback and ai_service.is_available():
            # Build prompt
            tasks_text = "\n".join([f"- [ID:{t.id}] {t.title} (Priority: {t.priority}, Due: {t.due_date}, Note: {t.description})" for t in pending])
            notes_text = "\n".join([f"- [Note] {n.title}: {n.content[:150]}" for n in notes[:5]])
            files_text = "\n".join([f"- [Approved File: {f.filename}]: {f.content_preview}" for f in files[:3]])

            prompt = f"""
You are LazyMorning, a thoughtful overnight personal assistant.
Analyze ONLY the user's authentic context provided below and generate a calm, structured morning briefing.

ACTIVE TASKS:
{tasks_text or "No pending tasks."}

RECENT NOTES:
{notes_text or "No notes recorded."}

APPROVED IMPORTED FILES:
{files_text or "No approved files."}

CRITICAL RULES:
1. NEVER hallucinate or invent tasks, dates, or details that are not explicitly present in the data above.
2. Structure your response into EXACTLY these 5 sections:

TODAY'S FOCUS:
[1-2 sentences summarizing today's key focus]

TOP 3 PRIORITIES:
1. [Task Title] - [Priority Level / Due Date] - [Brief note]
2. [Task Title] - [Priority Level / Due Date] - [Brief note]
3. [Task Title] - [Priority Level / Due Date] - [Brief note]

UPCOMING DEADLINES:
- [Task Title] - [Due Date]

UNFINISHED ITEMS:
- [Item title]
- [Item title]

SUGGESTED FIRST STEP:
[One low-friction, high-impact concrete action to start the morning peacefully]
"""
            ai_response = ai_service.generate(prompt)
            if ai_response:
                valid_task_dicts = [{"title": t.title, "priority": t.priority, "due_date": t.due_date, "description": t.description} for t in pending]
                valid_note_dicts = [{"title": n.title, "content": n.content} for n in notes]

                focus, prios, deadlines, unfinished, first_step = parse_ai_briefing_response(
                    ai_response, valid_task_dicts, valid_note_dicts
                )

                # Fallback any empty critical section
                if not prios and pending:
                    fallback_data = cls.generate_fallback(context)
                    prios = fallback_data["top_priorities"]
                if not deadlines and pending:
                    fallback_data = cls.generate_fallback(context)
                    deadlines = fallback_data["upcoming_deadlines"]

                briefing_dict = {
                    "todays_focus": focus,
                    "top_priorities": prios,
                    "upcoming_deadlines": deadlines,
                    "unfinished_items": unfinished or [t.title for t in pending[:5]],
                    "suggested_first_step": first_step,
                    "raw_markdown": ai_response,
                    "model_used": ai_service.model,
                    "source": "ai"
                }
                used_ai = True

        if not briefing_dict:
            briefing_dict = cls.generate_fallback(context)

        # Save to database
        db_briefing = Briefing(
            todays_focus=briefing_dict["todays_focus"],
            top_priorities_json=json.dumps(briefing_dict["top_priorities"]),
            upcoming_deadlines_json=json.dumps(briefing_dict["upcoming_deadlines"]),
            unfinished_items_json=json.dumps(briefing_dict["unfinished_items"]),
            suggested_first_step=briefing_dict["suggested_first_step"],
            raw_markdown=briefing_dict.get("raw_markdown", ""),
            model_used=briefing_dict.get("model_used", "fallback"),
            source=briefing_dict.get("source", "fallback"),
            generated_at=datetime.now(timezone.utc)
        )
        db.add(db_briefing)
        db.commit()
        db.refresh(db_briefing)
        return db_briefing

    @staticmethod
    def get_latest_briefing(db: Session) -> Optional[Briefing]:
        return db.query(Briefing).order_by(Briefing.generated_at.desc()).first()

    @staticmethod
    def get_briefing_history(db: Session, limit: int = 30) -> List[Briefing]:
        return db.query(Briefing).order_by(Briefing.generated_at.desc()).limit(limit).all()

    @staticmethod
    def get_briefing_by_id(db: Session, briefing_id: int) -> Optional[Briefing]:
        return db.query(Briefing).filter(Briefing.id == briefing_id).first()
