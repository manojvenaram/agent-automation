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
    get_aesthetic_scores,
    update_aesthetic_score,
    get_format_scores,
    update_format_score,
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

    def select_aesthetic_style(self, category: str) -> str:
        """
        Uses Explore vs Exploit to pick a visual aesthetic style.
        80% chance to pick the top-performing style, 20% to try a new one.
        """
        import random
        
        default_styles = [
            "high quality cinematic vertical portrait, intricate details, highly aesthetic, mysterious",
            "anime style, studio ghibli, vibrant colors, detailed scenery, magical",
            "cyberpunk neon lighting, dark moody atmosphere, hyper-realistic",
            "vintage 90s camcorder footage, grainy, nostalgic, liminal space",
            "watercolor painting, soft edges, ethereal, beautiful light",
            "hyper-realistic octane render, 3D, dramatic lighting, 8k resolution"
        ]

        scores = get_aesthetic_scores()
        
        # Epsilon-greedy: 20% exploration, 80% exploitation
        epsilon = 0.2
        if random.random() < epsilon or not scores:
            # Explore: pick randomly from defaults
            logger.info(f"Content Brain: Exploring random visual style for '{category}'...")
            return random.choice(default_styles)
        else:
            # Exploit: pick the best performing style
            best_style = scores[0]["style_name"]
            logger.info(f"Content Brain: Exploiting best visual style: '{best_style}' (Score: {scores[0]['score']:.1f})")
            return best_style

    def select_script_format(self, category: str) -> str:
        """
        Uses Explore vs Exploit to pick a storytelling script format.
        80% chance to pick the top-performing format, 20% to try a new one.
        """
        import random
        from backend.creative.creative_director import ShortsFormat
        
        default_formats = [f.name for f in ShortsFormat]

        scores = get_format_scores()
        
        epsilon = 0.2
        if random.random() < epsilon or not scores:
            # Explore
            chosen = random.choice(default_formats)
            logger.info(f"Content Brain: Exploring random script format for '{category}': {chosen}")
            return chosen
        else:
            # Exploit
            best_format = scores[0]["format_name"]
            logger.info(f"Content Brain: Exploiting best script format: '{best_format}' (Score: {scores[0]['score']:.1f})")
            return best_format

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
        aesthetic_style: Optional[str] = None,
        script_format: Optional[str] = None,
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

        # 3. Update aesthetic score if provided
        if aesthetic_style:
            update_aesthetic_score(
                style_name=aesthetic_style,
                delta=delta,
                new_quality_score=float(quality_score),
                new_retention=retention_pct,
            )
            logger.info(f"Content Brain: Updated performance for aesthetic style (Score delta: {delta})")

        # 4. Update script format score if provided
        if script_format:
            update_format_score(
                format_name=script_format,
                delta=delta,
                new_quality_score=float(quality_score),
                new_retention=retention_pct,
            )
            logger.info(f"Content Brain: Updated performance for script format (Score delta: {delta})")

        # 5. Semantic Memory Lesson Generation
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
