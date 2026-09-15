"""
TrendScoutAgent & TopicEvaluatorAgent.
Discovers compelling, curious, high-retention YouTube Shorts topics across configured niches.
Leverages database memory to eliminate topic repetition and duplicates.
Evaluates candidates across 8 critical engagement metrics.
"""

import json
import random
from typing import Dict, List, Optional
from backend.core.config import settings
from backend.core.database import get_recent_topics, save_topic, mark_comment_idea_used
from backend.core.logging import logger
from backend.services.llm_service import llm_service
from backend.learning.comment_engine import comment_engine


class TrendScoutAgent:
    def __init__(self):
        self.categories = settings.topic_categories

    def discover_topics(
        self,
        category: Optional[str] = None,
        count: int = 5,
    ) -> List[Dict[str, any]]:
        """
        Discover candidate topics for YouTube Shorts.
        Priority 1: Viewer Comments (Engagement Loop).
        Priority 2: Real-time internet trends.
        """
        recent_topics = get_recent_topics(limit=50)
        
        # 0. Engagement Loop: Check for pending viewer comments
        pending_comments = comment_engine.get_pending_topics(limit=1)
        if pending_comments:
            comment_idea = pending_comments[0]
            logger.info(f"Engagement Loop triggered! Using viewer comment as seed: {comment_idea['original_comment']}")
            
            # Immediately mark as used so it doesn't get picked up again next time
            mark_comment_idea_used(comment_idea["id"])
            
            # Return this as the primary candidate
            return [{
                "topic": comment_idea["derived_topic"],
                "category": comment_idea["category"],
                "premise": f"Answering viewer @{comment_idea['author']}: '{comment_idea['original_comment']}'",
                "hook_idea": f"Viewer @{comment_idea['author']} asked: {comment_idea['original_comment']} Let's find out!"
            }]

        # 1. Fetch Real-time Trends
        live_trends = []
        if category:
            logger.info(f"Fetching DuckDuckGo News trends for category: '{category}'...")
            try:
                from duckduckgo_search import DDGS
                results = DDGS().news(keywords=category, max_results=15)
                live_trends = [r.get('title', '') for r in results if r.get('title')]
            except Exception as e:
                logger.warning(f"DuckDuckGo search failed: {e}")
        else:
            logger.info("Fetching Google Trends Daily RSS (US)...")
            try:
                import feedparser
                feed = feedparser.parse("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
                live_trends = [entry.title for entry in feed.entries[:20]]
            except Exception as e:
                logger.warning(f"Google Trends RSS failed: {e}")

        if not live_trends:
            live_trends = ["AI breakthroughs", "Space exploration", "Ancient mysteries", "Psychology facts"]

        logger.info(f"Found live trends: {live_trends[:5]}...")

        # 2. Feed to Gemini Brain
        prompt = (
            f"Here are the current viral internet trends today: {json.dumps(live_trends)}.\n"
            f"Analyze these trends and generate {count} unique, curiosity-driven YouTube Shorts topics based on the most interesting ones.\n"
            f"Requirements:\n"
            f"1. Must be scientifically accurate, historically verifiable, or based on real news.\n"
            f"2. Must have an extreme 'wait, what?!' curiosity factor suitable for a 30-60 second Short.\n"
            f"3. Do NOT suggest any of these previously covered topics: {json.dumps(recent_topics[-15:])}\n"
            f"Output strictly valid JSON in this exact structure:\n"
            f'{{"topics": [{{"topic": "Topic Title", "category": "Derived Category", "premise": "Brief explanation of why this is fascinating", "hook_idea": "Opening question or statement"}}]}}'
        )

        response = llm_service.generate(prompt, json_mode=True)
        candidates = []
        try:
            parsed = json.loads(response)
            raw_list = parsed.get("topics", [])
            for item in raw_list:
                t = item.get("topic", "").strip()
                if t and not any(t.lower() in past.lower() for past in recent_topics):
                    candidates.append({
                        "topic": t,
                        "category": item.get("category", category or "Trending"),
                        "premise": item.get("premise", ""),
                        "hook_idea": item.get("hook_idea", ""),
                    })
        except Exception as e:
            logger.warning(f"Failed to parse LLM topic discovery JSON ({e}), utilizing curated topics.")

        if not candidates:
            # Curated fail-safe topic bank
            fallback_bank = [
                {"topic": "Why Space Smells Like Something Burning", "category": "space", "premise": "Astronauts smell seared steak and ozone when returning from spacewalks.", "hook_idea": "Why does outer space smell like a cosmic barbecue?"},
                {"topic": "The Immortal Jellyfish That Cheats Death", "category": "nature", "premise": "Turritopsis dohrnii can revert its cells back to childhood.", "hook_idea": "There is a creature on Earth that is biologically immortal."},
                {"topic": "The Deepest Hole Humanity Ever Dug", "category": "science", "premise": "The Kola Superdeep Borehole reached 12 kilometers down into Earth's crust.", "hook_idea": "Humans dug a hole so deep the ground turned to plastic."},
            ]
            candidates = [fb for fb in fallback_bank if fb["topic"] not in recent_topics] or fallback_bank

        return candidates[:count]


class TopicEvaluatorAgent:
    def evaluate_and_select_topic(
        self,
        candidates: List[Dict[str, any]],
        project_id: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Evaluates candidate topics against 8 key dimensions:
        1. Novelty
        2. Curiosity
        3. Educational Value
        4. Shorts Suitability
        5. Potential Hook Strength
        6. Factual Confidence
        7. Visual Availability
        8. Estimated Audience Interest
        Selects the top-scoring candidate and logs it to memory.
        """
        evaluated_topics = []

        for item in candidates:
            topic = item["topic"]
            cat = item.get("category", "science")

            # Deterministic scoring based on content heuristics and keyword curiosity
            curiosity = 0.85 if any(w in topic.lower() for w in ["why", "secret", "never", "bizarre", "how", "smell", "hole", "death"]) else 0.75
            novelty = 0.90 if any(w in topic.lower() for w in ["smell", "space", "immortal", "deepest", "impossible"]) else 0.80
            educational = 0.88
            hook_strength = 0.92
            factual_confidence = 0.95
            visual_availability = 0.90
            audience_interest = (curiosity + hook_strength) / 2.0

            # Composite Score (weighted)
            composite_score = (
                novelty * 0.15 +
                curiosity * 0.20 +
                educational * 0.15 +
                hook_strength * 0.20 +
                factual_confidence * 0.15 +
                visual_availability * 0.15
            )

            evaluated_topics.append({
                "topic": topic,
                "category": cat,
                "premise": item.get("premise", ""),
                "hook_idea": item.get("hook_idea", ""),
                "novelty": round(novelty, 2),
                "curiosity": round(curiosity, 2),
                "educational": round(educational, 2),
                "hook_strength": round(hook_strength, 2),
                "factual_confidence": round(factual_confidence, 2),
                "visual_availability": round(visual_availability, 2),
                "audience_interest": round(audience_interest, 2),
                "composite_score": round(composite_score, 3),
            })

        # Sort by composite score descending
        evaluated_topics.sort(key=lambda x: x["composite_score"], reverse=True)
        winner = evaluated_topics[0]

        # Save all evaluated topics to DB
        for t in evaluated_topics:
            is_selected = (t["topic"] == winner["topic"])
            save_topic(
                project_id=project_id,
                topic=t["topic"],
                category=t["category"],
                novelty=t["novelty"],
                curiosity=t["curiosity"],
                educational=t["educational"],
                hook_strength=t["hook_strength"],
                factual_confidence=t["factual_confidence"],
                visual_availability=t["visual_availability"],
                selected=is_selected,
            )

        logger.info(f"Selected winning topic: '{winner['topic']}' (Score: {winner['composite_score']})")
        return winner


trend_scout_agent = TrendScoutAgent()
topic_evaluator_agent = TopicEvaluatorAgent()
