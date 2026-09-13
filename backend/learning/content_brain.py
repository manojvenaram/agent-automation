"""
Content Brain for YouTube Shorts Intelligence.
Central repository of learned intelligence:
- Category performance scores and lifetime history
- Dynamic content portfolio allocation (80/20 rule)
- Recurring original characters roster and evolution
- Audience geography and retention signals
- Nightly self-review lessons
- Human override controls (blacklists, forced categories/characters)
"""

from typing import Any, Dict, List, Optional, Tuple
from backend.core.database import (
    get_category_scores,
    update_category_score,
    get_characters,
    save_character,
    increment_character_appearance,
    get_blacklists,
    add_to_blacklist,
    is_blacklisted,
    save_daily_review,
    get_recent_daily_reviews,
    add_comment_idea,
    get_pending_comment_ideas,
    record_analytics,
    list_projects,
)
from backend.core.logging import logger
from backend.intelligence.content_portfolio import ContentPortfolioAllocator
from backend.memory.memory_manager import memory_manager


class ContentBrain:
    def __init__(self):
        self.portfolio_allocator = ContentPortfolioAllocator()

    def get_status(self) -> Dict[str, Any]:
        """Provides a comprehensive summary of the Content Brain state."""
        categories = get_category_scores()
        characters = get_characters()
        blacklists = get_blacklists()
        reviews = get_recent_daily_reviews(limit=3)
        pending_ideas = get_pending_comment_ideas(limit=5)
        portfolio_mix = self.portfolio_allocator.calculate_mix(categories)

        return {
            "total_categories": len(categories),
            "category_leaderboard": categories[:8],
            "characters": characters,
            "blacklists_active": len(blacklists),
            "latest_review": reviews[0] if reviews else None,
            "pending_comment_ideas": len(pending_ideas),
            "dynamic_portfolio_mix": portfolio_mix,
        }

    def get_category_leaderboard(self) -> List[Dict[str, Any]]:
        """Returns categories ordered by performance score descending."""
        return get_category_scores()

    def get_dynamic_mix(self) -> Dict[str, float]:
        """Returns the current dynamic portfolio mix percentages (e.g. 0.25 = 25%)."""
        scores = get_category_scores()
        return self.portfolio_allocator.calculate_mix(scores)

    def record_video_performance(
        self,
        project_id: str,
        category: str,
        quality_score: int,
        views: int = 0,
        retention_pct: float = 70.0,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        top_geography: str = "United States",
    ) -> None:
        """Records telemetry and updates category scores."""
        # 1. Store in analytics table
        record_analytics(
            project_id=project_id,
            views=views,
            retention_pct=retention_pct,
            likes=likes,
            comments=comments,
            shares=shares,
            top_geography=top_geography,
        )

        # 2. Update category composite score
        delta = 1.0 if retention_pct >= 75.0 else (-0.5 if retention_pct < 60.0 else 0.2)
        update_category_score(
            category=category,
            delta=delta,
            new_quality_score=float(quality_score),
            new_retention=retention_pct,
        )
        logger.info(f"Content Brain: Updated performance for category '{category}' (Retention: {retention_pct}%, Quality: {quality_score})")

        # 3. Semantic Memory Lesson Generation
        if retention_pct >= 75.0 or quality_score >= 90:
            memory_manager.store_memory(
                memory_type="SUCCESS",
                content=f"High performance ({retention_pct}% retention) for category '{category}'. Project {project_id}.",
                metadata={"project_id": project_id, "category": category, "retention": retention_pct}
            )
        elif retention_pct < 60.0 or quality_score < 60:
            memory_manager.store_memory(
                memory_type="FAILURE",
                content=f"Poor performance ({retention_pct}% retention) for category '{category}'. Project {project_id}.",
                metadata={"project_id": project_id, "category": category, "retention": retention_pct}
            )

    def get_all_characters(self) -> List[Dict[str, Any]]:
        """Returns list of all recurring characters."""
        return get_characters()

    def register_character_appearance(self, name: str) -> None:
        """Increments appearance count for recurring character."""
        increment_character_appearance(name)

    def add_recurring_character(self, name: str, persona: str, visual_style: str, catchphrase: str = "") -> None:
        """Adds or updates a recurring character."""
        save_character(name, persona, visual_style, catchphrase)

    def check_blacklist(self, topic: str, category: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Checks if a candidate topic or category is blocked by human overrides."""
        if is_blacklisted(topic, category):
            return True, "Violates active human override blacklist."
        return False, None

    def add_override_blacklist(self, list_type: str, value: str, reason: str = "") -> bool:
        """Adds a blacklist rule."""
        return add_to_blacklist(list_type, value, reason)

    def get_active_blacklists(self) -> List[Dict[str, Any]]:
        """Returns active blacklists."""
        return get_blacklists()

    def get_recent_reviews(self, limit: int = 7) -> List[Dict[str, Any]]:
        """Retrieves past nightly self-reviews."""
        return get_recent_daily_reviews(limit=limit)

    def log_daily_review(
        self,
        review_date: str,
        successes: str,
        failures: str,
        lessons: str,
        strategy_changes: str,
    ) -> None:
        """Stores a nightly self-review report."""
        save_daily_review(review_date, successes, failures, lessons, strategy_changes)


content_brain = ContentBrain()
