"""
Content Opportunity Engine.
Calculates 13-dimensional predictive opportunity scores (0-100) for candidate topics,
penalizing saturated topics and prioritizing emerging high-retention concepts.
"""

from typing import Any, Dict, List
from backend.core.database import get_category_scores
from backend.core.logging import logger
from backend.memory.memory_manager import memory_manager
from backend.services.llm_service import LLMService
import json


class OpportunityScorer:
    def __init__(self, llm_service=None):
        self.llm = llm_service or LLMService()

    def evaluate_opportunity(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates complete 13-dimension breakdown and composite Opportunity Score (0-100).
        """
        topic = candidate.get("topic", "")
        category = candidate.get("category", "science").lower()
        premise = candidate.get("premise", "")
        trend_type = candidate.get("trend_type", "EVERGREEN")
        velocity = candidate.get("velocity", "STEADY")

        lower_t = (topic + " " + premise).lower()

        # 1. Trend Score (0-100)
        trend_score = 75.0
        if trend_type == "VIRAL": trend_score = 95.0
        elif trend_type == "RISING": trend_score = 90.0
        elif trend_type == "BREAKING": trend_score = 92.0
        elif trend_type == "EMERGING": trend_score = 88.0
        elif trend_type == "SEASONAL": trend_score = 82.0
        elif trend_type == "EVERGREEN": trend_score = 80.0

        # Use LLM for semantic multidimensional scoring
        prompt = f"""
Evaluate the following content topic across 6 dimensions from 0 to 100.
Topic: "{topic}"
Premise: "{premise}"
Category: "{category}"

Provide a JSON output with these keys and integer values:
"audience_score": Tier 1 English market appeal (0-100)
"curiosity_score": Counter-intuitive or 'did you know' factor (0-100)
"originality_score": Avoidance of oversaturated tropes (0-100)
"visual_score": Can be illustrated easily with graphics/photos (0-100)
"story_score": Narrative potential with setup and twist (0-100)
"humor_score": Comedy suitability (0-100)
"""
        try:
            llm_res = self.llm.generate(prompt=prompt, json_mode=True)
            scores = self.llm.parse_json_safely(llm_res) or {}
        except Exception as e:
            logger.warning(f"Semantic scoring failed: {e}. Falling back to default scores.")
            scores = {}

        audience_score = float(scores.get("audience_score", 85.0))
        curiosity_score = float(scores.get("curiosity_score", 78.0))
        originality_score = float(scores.get("originality_score", 86.0))
        visual_score = float(scores.get("visual_score", 84.0))
        story_score = float(scores.get("story_score", 82.0))
        humor_score = float(scores.get("humor_score", 50.0))

        # 8. Shareability Score ("Did you know?" factor)
        shareability_score = (curiosity_score + audience_score) / 2.0

        # 9. Retention Potential (Under 60s pacing)
        retention_potential = 85.0
        if len(topic.split()) <= 12:
            retention_potential += 5.0

        # 10. Competition Level (Lower competition = higher score contribution)
        competition_level = 50.0
        if trend_type == "EMERGING":
            competition_level = 25.0
        elif trend_type == "VIRAL":
            competition_level = 80.0

        # 11. Factual Confidence
        factual_confidence = 92.0
        if category == "original fiction":
            factual_confidence = 95.0

        # 12. Production Cost (Zero dollar feasibility)
        production_cost = 95.0

        # 13. Trend Lifespan
        trend_lifespan = 85.0 if trend_type in ["EVERGREEN", "SEASONAL"] else 60.0

        # Look up Content Brain historical category affinity
        brain_category_boost = 0.0
        try:
            scores = get_category_scores()
            for s in scores:
                if s["category"] == category:
                    brain_category_boost = (s["score"] - 75.0) * 0.15
                    break
        except Exception:
            pass

        # 3. Retrieve Memory Lessons & Semantic Similarity
        # If this is highly similar to a past failure or a recent video, penalize it.
        # If it matches a success pattern, boost it.
        semantic_lessons = []
        try:
            semantic_lessons = memory_manager.search_similar(topic, k=3)
        except Exception:
            pass

        lesson_score = 50.0
        similarity_penalty = 0.0

        for lesson in semantic_lessons:
            lesson_type = lesson.get("type", "")
            if lesson_type == "FAILURE":
                lesson_score -= 15.0
            elif lesson_type == "SUCCESS":
                lesson_score += 15.0

            # Penalize highly similar topics to prevent duplicates
            if lesson.get("distance", 1.0) < 0.2:
                similarity_penalty += 30.0

        lesson_score = max(0.0, min(100.0, lesson_score))

        # Weighted Composite Opportunity Formula
        raw_composite = (
            trend_score * 0.15 +
            curiosity_score * 0.18 +
            retention_potential * 0.15 +
            audience_score * 0.12 +
            visual_score * 0.10 +
            originality_score * 0.10 +
            shareability_score * 0.10 +
            (100.0 - competition_level) * 0.05 +
            trend_lifespan * 0.05
        ) + brain_category_boost

        # Blend the memory lessons (20% weight) and subtract duplication penalty
        raw_composite = (raw_composite * 0.8) + (lesson_score * 0.2) - similarity_penalty
        
        opportunity_score = round(max(0.0, min(100.0, raw_composite)), 1)

        result = dict(candidate)
        result.update({
            "opportunity_score": opportunity_score,
            "metrics": {
                "trend_score": round(trend_score, 1),
                "curiosity_score": round(curiosity_score, 1),
                "originality_score": round(originality_score, 1),
                "retention_potential": round(retention_potential, 1),
                "visual_score": round(visual_score, 1),
                "humor_score": round(humor_score, 1),
                "audience_score": round(audience_score, 1),
                "shareability_score": round(shareability_score, 1),
                "competition_level": round(competition_level, 1),
                "factual_confidence": round(factual_confidence, 1),
                "trend_lifespan": round(trend_lifespan, 1),
            },
        })
        return result

    def score_candidate(self, candidate: Dict[str, Any]) -> Any:
        """Alias for evaluate_opportunity returning an object/dict with fields."""
        data = self.evaluate_opportunity(candidate)
        class ScoredItem:
            def __init__(self, d):
                self.topic = d.get("topic", "")
                self.category = d.get("category", "")
                self.opportunity_score = d.get("opportunity_score", 0.0)
                m = d.get("metrics", {})
                self.curiosity_score = m.get("curiosity_score", 0.0)
                self.factual_confidence = m.get("factual_confidence", 0.0)
                self.competition = "low" if m.get("competition_level", 0) < 50 else ("high" if m.get("competition_level", 0) > 75 else "medium")
        return ScoredItem(data)

    def rank_opportunities(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scores and sorts candidates by highest opportunity score."""
        scored = [self.evaluate_opportunity(c) for c in candidates]
        return sorted(scored, key=lambda x: x.get("opportunity_score", 0.0), reverse=True)


ContentOpportunityScorer = OpportunityScorer
opportunity_scorer = OpportunityScorer()

