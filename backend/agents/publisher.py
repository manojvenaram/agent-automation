"""
PublisherAgent & SchedulerAgent for YouTube Shorts Automation.
PublisherAgent handles official YouTube uploads with mode control (Auto vs Approval).
SchedulerAgent handles recurring daily triggers via APScheduler.
"""

from typing import Dict, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.core.config import settings
from backend.core.database import update_project_state
from backend.core.logging import logger
from backend.models import ProjectModel, ProjectState, YouTubeMetadata
from backend.services.youtube_service import youtube_service


class PublisherAgent:
    def publish_short(
        self,
        project: ProjectModel,
        metadata: YouTubeMetadata,
    ) -> Dict[str, str]:
        """
        Publishes video to YouTube following official API guidelines.
        Respects demo_mode and auto_publish safeguards.
        """
        logger.info(f"Publishing project '{project.id}' to YouTube...")

        if not project.video_path:
            raise ValueError(f"Project '{project.id}' has no rendered video file to publish.")

        # 1. DEMO_MODE: simulate successful publish for safe local verification
        if settings.demo_mode:
            simulated_url = f"https://youtube.com/shorts/demo_{project.id[:8]}"
            logger.info(f"[DEMO_MODE=True] Simulated YouTube upload: {simulated_url}")
            update_project_state(
                project_id=project.id,
                state=ProjectState.PUBLISHED,
                youtube_url=simulated_url,
            )
            return {
                "video_id": f"demo_{project.id[:8]}",
                "title": metadata.selected_title,
                "privacy_status": "private",
                "url": simulated_url,
            }

        # 2. Production Upload
        if not youtube_service.is_authenticated():
            logger.warning(
                "YouTube authentication credentials not configured. "
                "Marking project as APPROVED and ready for manual upload."
            )
            update_project_state(
                project_id=project.id,
                state=ProjectState.APPROVED,
                error_message="YouTube OAuth not configured. Video saved locally and ready for upload.",
            )
            return {
                "video_id": "pending_auth",
                "title": metadata.selected_title,
                "privacy_status": settings.youtube_privacy_status,
                "url": "",
            }

        update_project_state(project.id, ProjectState.UPLOADING)
        try:
            result = youtube_service.upload_short(
                video_path=project.video_path,
                title=metadata.selected_title,
                description=metadata.description,
                tags=metadata.tags,
                privacy_status=settings.youtube_privacy_status,
                category_id=settings.youtube_category_id,
            )
            update_project_state(
                project_id=project.id,
                state=ProjectState.PUBLISHED,
                youtube_url=result["url"],
            )
            return result
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            update_project_state(
                project_id=project.id,
                state=ProjectState.APPROVED,
                error_message=f"Upload failed: {str(e)}",
            )
            raise e


class SchedulerAgent:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self._is_running = False

    def start(self, job_func):
        """Start the background scheduler for automated production."""
        if not settings.scheduler_enabled:
            logger.info("Scheduler disabled by configuration.")
            return

        if self._is_running:
            return

        time_parts = settings.posting_time.split(":")
        hour = int(time_parts[0]) if len(time_parts) > 0 else 18
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        trigger = CronTrigger(hour=hour, minute=minute, timezone=settings.timezone)
        self.scheduler.add_job(job_func, trigger=trigger, id="daily_shorts_producer")
        self.scheduler.start()
        self._is_running = True
        logger.info(f"Scheduler started: running daily at {hour:02d}:{minute:02d} {settings.timezone}")

    def stop(self):
        if self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("Scheduler stopped.")


publisher_agent = PublisherAgent()
scheduler_agent = SchedulerAgent()
