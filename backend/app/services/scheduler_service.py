import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.services.briefing_service import BriefingService

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.job_id = "daily_morning_briefing"
        self.is_running = False
        self.last_run: datetime = None

    def _scheduled_job(self):
        logger.info("Executing scheduled morning briefing generation...")
        db = SessionLocal()
        try:
            briefing = BriefingService.generate_briefing(db)
            self.last_run = datetime.now()
            logger.info(f"Scheduled briefing created with ID: {briefing.id} (Source: {briefing.source})")
        except Exception as e:
            logger.error(f"Error in scheduled briefing job: {e}")
        finally:
            db.close()

    def start(self):
        if not self.is_running:
            try:
                hour_str, minute_str = settings.BRIEFING_TIME.split(":")
                hour = int(hour_str)
                minute = int(minute_str)
            except Exception:
                hour, minute = 6, 30

            trigger = CronTrigger(hour=hour, minute=minute)
            self.scheduler.add_job(
                self._scheduled_job,
                trigger=trigger,
                id=self.job_id,
                replace_existing=True
            )
            self.scheduler.start()
            self.is_running = True
            logger.info(f"Scheduler started. Daily briefing set for {hour:02d}:{minute:02d}")

    def reschedule(self, time_str: str):
        try:
            hour_str, minute_str = time_str.split(":")
            hour = int(hour_str)
            minute = int(minute_str)
            trigger = CronTrigger(hour=hour, minute=minute)
            if self.scheduler.get_job(self.job_id):
                self.scheduler.reschedule_job(self.job_id, trigger=trigger)
            else:
                self.scheduler.add_job(
                    self._scheduled_job,
                    trigger=trigger,
                    id=self.job_id,
                    replace_existing=True
                )
            settings.BRIEFING_TIME = time_str
            logger.info(f"Briefing rescheduled to {hour:02d}:{minute:02d}")
            return True
        except Exception as e:
            logger.error(f"Failed to reschedule: {e}")
            return False

    def pause(self):
        if self.scheduler.get_job(self.job_id):
            self.scheduler.pause_job(self.job_id)

    def resume(self):
        if self.scheduler.get_job(self.job_id):
            self.scheduler.resume_job(self.job_id)

    def get_status(self):
        job = self.scheduler.get_job(self.job_id) if self.is_running else None
        next_run = job.next_run_time if job else None
        return {
            "is_running": self.is_running,
            "scheduled_time": settings.BRIEFING_TIME,
            "timezone": settings.TIMEZONE,
            "next_run_time": next_run.isoformat() if next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None
        }

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False

scheduler_service = SchedulerService()
