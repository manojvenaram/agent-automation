from datetime import datetime, timedelta, timezone
from typing import Optional
from backend.core.database import get_db_connection
from backend.core.logging import logger

class SchedulerService:
    """
    Automated posting scheduler inspired by AutoSocial.
    Calculates the next available optimal YouTube publishAt slot for a given video format.
    """
    def __init__(self):
        # We can configure this via .env later
        self.shorts_post_hours_utc = [14, 18] # 2 PM and 6 PM UTC (2 daily)
        self.longform_post_days = [2, 5]      # Wednesday and Saturday (2 weekly)
        self.longform_post_hour_utc = 14      # 2 PM UTC

    def _get_latest_scheduled_time(self, is_short: bool) -> Optional[datetime]:
        """Finds the latest publishAt time currently scheduled in the database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # We assume scheduled videos are tracked somewhere, or we just rely on state.
        # But for now, we'll just check what the latest Project publish_at is.
        # Since we don't have a publish_at column in our Projects table, we will
        # calculate slots strictly sequentially starting from TODAY.
        # Note: A real AutoSocial integration would query the DB for the last scheduled time.
        pass

    def calculate_next_slot(self, video_format: str) -> str:
        """
        Calculates the next available upload slot and returns an ISO 8601 string.
        """
        now = datetime.now(timezone.utc)
        
        if video_format in ["short", "mini_cartoon", "stickman_explainer"]:
            # Schedule for today at the next available slot, else tomorrow first slot
            slot = None
            for hour in self.shorts_post_hours_utc:
                candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                if candidate > now:
                    slot = candidate
                    break
            if not slot:
                # All slots passed today, use first slot tomorrow
                slot = now.replace(hour=self.shorts_post_hours_utc[0], minute=0, second=0, microsecond=0) + timedelta(days=1)
        else:
            # Long form: Next available Wednesday or Saturday at 2 PM UTC
            slot = None
            for day_offset in range(0, 8):
                candidate_date = now + timedelta(days=day_offset)
                if candidate_date.weekday() in self.longform_post_days:
                    candidate_slot = candidate_date.replace(hour=self.longform_post_hour_utc, minute=0, second=0, microsecond=0)
                    if candidate_slot > now:
                        slot = candidate_slot
                        break
            if not slot:
                # Fallback safeguard
                slot = now + timedelta(days=7)
                slot = slot.replace(hour=self.longform_post_hour_utc, minute=0, second=0, microsecond=0)
                
        iso_str = slot.isoformat()
        logger.info(f"[Scheduler] Assigned next slot for format '{video_format}' -> {iso_str}")
        return iso_str

scheduler_service = SchedulerService()
