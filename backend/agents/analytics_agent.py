"""
Analytics Agent.
Pulls performance data from YouTube, calculates an overall "Performance Score",
and automatically updates the database to optimize future video generations (Visual Styles & Categories).
"""

from typing import List, Dict, Any
from datetime import datetime
from backend.core.logging import logger
from backend.core.database import get_db_cursor
from backend.services.youtube_service import youtube_service

class AnalyticsAgent:
    def __init__(self):
        self.service = youtube_service

    def run_analytics_cycle(self) -> None:
        """
        Runs the full analytics gathering and intelligence optimization loop.
        """
        logger.info("📈 Analytics Agent: Starting performance review cycle...")
        
        if not self.service.is_authenticated():
            logger.warning("YouTube service not authenticated. Cannot run Analytics Agent.")
            return

        # 1. Get recent uploads from our local database
        recent_uploads = self._get_recent_uploads(limit=50)
        if not recent_uploads:
            logger.info("No recent uploads found to analyze.")
            return

        video_ids = [row["video_id"] for row in recent_uploads]
        project_ids = {row["video_id"]: row["project_id"] for row in recent_uploads}

        # 2. Fetch stats from YouTube
        stats = self.service.fetch_video_stats(video_ids)
        if not stats:
            logger.warning("No stats returned from YouTube.")
            return

        # 3. Process stats and calculate performance scores
        now = datetime.utcnow().isoformat()
        
        with get_db_cursor() as cur:
            for vid, stat in stats.items():
                project_id = project_ids.get(vid)
                if not project_id:
                    continue

                views = int(stat.get("viewCount", 0))
                likes = int(stat.get("likeCount", 0))
                comments = int(stat.get("commentCount", 0))
                
                # Simple engagement calculation (since retention requires full Analytics API)
                engagement = likes + (comments * 2) # Comments weighted 2x
                score = min(100.0, (views * 0.1) + (engagement * 1.5)) # Base score logic

                # Store history
                cur.execute(
                    """
                    INSERT INTO analytics_history (
                        project_id, views, likes, comments, recorded_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (project_id, views, likes, comments, now)
                )

                # Fetch project details to know what category/style it was
                cur.execute("SELECT category FROM projects WHERE id = ?", (project_id,))
                proj_row = cur.fetchone()
                if proj_row:
                    category = proj_row["category"]
                    
                    # Update category performance
                    cur.execute(
                        """
                        INSERT INTO category_scores (category, score, lifetime_videos, updated_at)
                        VALUES (?, ?, 1, ?)
                        ON CONFLICT(category) DO UPDATE SET
                            score = (score * lifetime_videos + excluded.score) / (lifetime_videos + 1),
                            lifetime_videos = lifetime_videos + 1,
                            updated_at = excluded.updated_at
                        """,
                        (category, score, now)
                    )

            logger.info("✅ Analytics Agent: Updated intelligence tables with latest performance data.")

    def _get_recent_uploads(self, limit: int = 50) -> List[Dict[str, Any]]:
        with get_db_cursor() as cur:
            cur.execute("SELECT video_id, project_id FROM youtube_uploads ORDER BY uploaded_at DESC LIMIT ?", (limit,))
            return [{"video_id": row["video_id"], "project_id": row["project_id"]} for row in cur.fetchall()]


analytics_agent = AnalyticsAgent()

if __name__ == "__main__":
    agent = AnalyticsAgent()
    agent.run_analytics_cycle()
