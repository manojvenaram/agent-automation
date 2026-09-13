"""
Dynamic Content Portfolio Engine & Cross-Category Hybridization.
Maintains an evolving category allocation portfolio (80% proven / 20% experiments)
and discovers high-retention cross-category concepts.
"""

import random
from typing import Any, Dict, List, Optional, Tuple
from backend.core.config import settings
from backend.core.database import get_category_scores, list_projects
from backend.core.logging import logger


class ContentPortfolioEngine:
    def __init__(self):
        self.hybrid_combinations = [
            ("science", "cartoons", "Animated science mini-explainer with Byte & Sam"),
            ("sports", "humor", "Absurd or hilarious sports records & bloopers"),
            ("history", "humor", "Satirical review of unbelievable real historical blunders"),
            ("technology", "cartoons", "Byte the robot explains futuristic tech"),
            ("space", "mystery", "Unsolved cosmic signals and astrophysical anomalies"),
            ("animals", "science", "Evolutionary superpowers of bizarre creatures"),
            ("food", "science", "The chemical science behind why foods taste amazing or weird"),
            ("original fiction", "cartoons", "Short comedic sci-fi mini story"),
        ]

    def select_next_portfolio_target(self, forced_category: Optional[str] = None) -> Tuple[str, bool]:
        """
        Determines the next category to target based on 80/20 proven vs experimental allocation.
        Returns (category_name, is_experiment).
        """
        if forced_category:
            logger.info(f"Content Portfolio: Forced category override active -> '{forced_category}'")
            return forced_category.lower(), False

        # Retrieve Content Brain category scores
        category_scores = get_category_scores()
        if not category_scores:
            return "science", False

        # Decide whether this run is an experiment (20% chance) or proven format (80% chance)
        is_experiment = (random.random() < 0.20)

        if is_experiment:
            # Pick from experimental or lower-volume categories
            lower_tier = sorted(category_scores, key=lambda x: x["lifetime_videos"])[:5]
            selected = random.choice(lower_tier)["category"]
            logger.info(f"Content Portfolio: [EXPERIMENT 20%] Testing category '{selected}'")
            return selected, True
        else:
            # Pick from top-performing categories with weighted probability
            top_tier = sorted(category_scores, key=lambda x: x["score"], reverse=True)[:6]
            weights = [max(1.0, c["score"]) for c in top_tier]
            selected = random.choices(top_tier, weights=weights, k=1)[0]["category"]
            logger.info(f"Content Portfolio: [PROVEN 80%] Selected high-performer '{selected}' (Score: {selected})")
            return selected, False

    def check_cross_category_opportunity(self, base_category: str) -> Optional[Dict[str, str]]:
        """Determine if a topic can be enhanced into an original cross-category hybrid."""
        for cat1, cat2, angle in self.hybrid_combinations:
            if base_category.lower() in [cat1, cat2]:
                other = cat2 if base_category.lower() == cat1 else cat1
                return {
                    "primary_category": base_category,
                    "secondary_category": other,
                    "hybrid_angle": angle,
                }
        return None

    def calculate_mix(self, category_scores: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculates dynamic percentage mix based on scores while preserving 80/20 balance."""
        if not category_scores:
            return {"science": 0.30, "cartoons": 0.25, "humor": 0.25, "technology": 0.20}
        total_score = sum(max(1.0, c["score"]) for c in category_scores)
        return {
            c["category"]: round(max(1.0, c["score"]) / total_score, 3)
            for c in category_scores
        }


ContentPortfolioAllocator = ContentPortfolioEngine
content_portfolio = ContentPortfolioEngine()

