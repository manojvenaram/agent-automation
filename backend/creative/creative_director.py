"""
Creative Director Agent for YouTube Shorts Intelligence.
Determines: "What is the most entertaining, original, and visually arresting way to communicate this?"
Selects from 20 shorts formats, determines humor suitability (0-100), chooses visual treatments,
and sets pacing and sound design profiles.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from backend.core.logging import logger
from backend.services.llm_service import LLMService


class ShortsFormat(str, Enum):
    DOCUMENTARY = "DOCUMENTARY"
    NEWS_EXPLAINER = "NEWS_EXPLAINER"
    COMEDY = "COMEDY"
    MYSTERY = "MYSTERY"
    STORY = "STORY"
    COUNTDOWN = "COUNTDOWN"
    TOP_3 = "TOP_3"
    TOP_5 = "TOP_5"
    MYTH_VS_FACT = "MYTH_VS_FACT"
    DID_YOU_KNOW = "DID_YOU_KNOW"
    WHAT_IF = "WHAT_IF"
    VERSUS = "VERSUS"
    TIMELINE = "TIMELINE"
    ANIMATION = "ANIMATION"
    MINI_CARTOON = "MINI_CARTOON"
    POV = "POV"
    SIMULATION = "SIMULATION"
    DRAMATIC_STORY = "DRAMATIC_STORY"
    FAST_EXPLAINER = "FAST_EXPLAINER"
    VISUAL_EXPERIMENT = "VISUAL_EXPERIMENT"


class VisualTreatment(str, Enum):
    STOCK_PUBLIC_MEDIA = "STOCK_PUBLIC_MEDIA"
    ORIGINAL_GRAPHICS = "ORIGINAL_GRAPHICS"
    ANIMATION = "ANIMATION"
    MOTION_GRAPHICS = "MOTION_GRAPHICS"
    CHARTS = "CHARTS"
    MAPS = "MAPS"
    DIAGRAMS = "DIAGRAMS"
    PHOTOS = "PHOTOS"
    VIDEO_CLIPS = "VIDEO_CLIPS"
    SCREEN_RECORDINGS = "SCREEN_RECORDINGS"
    TEXT_ANIMATION = "TEXT_ANIMATION"
    CARTOON = "CARTOON"


@dataclass
class CreativeDirection:
    format: ShortsFormat
    humor_suitability: int  # 0 - 100
    visual_treatment: VisualTreatment
    pacing_bpm: int  # 120 - 160 bpm pacing
    audio_mood: str  # dramatic, comedic, upbeat, mysterious, energetic
    story_structure: str  # narrative architecture key
    character_assigned: Optional[str] = None  # e.g., "Byte" or "Sam"
    humor_techniques: List[str] = field(default_factory=list)
    visual_beat_interval_sec: float = 2.5
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format.value,
            "humor_suitability": self.humor_suitability,
            "visual_treatment": self.visual_treatment.value,
            "pacing_bpm": self.pacing_bpm,
            "audio_mood": self.audio_mood,
            "story_structure": self.story_structure,
            "character_assigned": self.character_assigned,
            "humor_techniques": self.humor_techniques,
            "visual_beat_interval_sec": self.visual_beat_interval_sec,
            "rationale": self.rationale,
        }


class CreativeDirectorAgent:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.ollama = llm_service or LLMService()

    def calculate_humor_suitability(self, topic: str, category: str, summary: str = "") -> int:
        """
        Evaluate HUMOR_SUITABILITY (0 - 100).
        Never force comedy into tragedy, severe disasters, or sacred/solemn events.
        Boost comedy for cartoons, relatable situations, weird science, and sports blunders.
        """
        lower = f"{topic} {summary}".lower()
        cat_lower = category.lower()

        # Hard guardrails: zero humor for serious/somber topics
        serious_signals = [
            "death", "killed", "died", "murder", "casualt", "disaster", "fatal",
            "war", "tragedy", "crisis", "victim", "abuse", "terminal", "suicide",
            "funeral", "genocide", "earthquake", "crash", "flood"
        ]
        if any(w in lower for w in serious_signals):
            return 5

        # Base category defaults
        category_humor_baselines = {
            "humor": 95,
            "cartoon": 90,
            "original fiction": 75,
            "animals": 75,
            "internet culture": 85,
            "gaming": 70,
            "sports": 65,
            "food": 60,
            "technology": 50,
            "science": 45,
            "education": 40,
            "geography": 35,
            "history": 40,
            "mystery": 20,
            "space": 35,
            "entertainment": 65,
            "news": 15,
        }
        score = category_humor_baselines.get(cat_lower, 40)

        # Keyword modifiers
        high_humor_signals = ["funny", "bizarre", "absurd", "ridiculous", "weird", "mistake", "ironic", "clumsy", "meme", "joke"]
        if any(w in lower for w in high_humor_signals):
            score = min(100, score + 25)

        factual_serious_signals = ["breakthrough", "discovery", "announcement", "record", "investigation", "analysis"]
        if any(w in lower for w in factual_serious_signals) and cat_lower in ["news", "science", "technology"]:
            score = max(10, score - 15)

        return score

    def select_format(self, topic: str, category: str, humor_suitability: int, is_fiction_or_cartoon: bool = False) -> ShortsFormat:
        """
        Intelligently choose from the 20 Shorts formats based on topic, category, and tone.
        """
        lower = topic.lower()
        cat = category.lower()

        if is_fiction_or_cartoon or cat == "cartoon":
            return ShortsFormat.MINI_CARTOON

        if cat == "humor" or humor_suitability >= 80:
            if "what if" in lower:
                return ShortsFormat.WHAT_IF
            return ShortsFormat.COMEDY

        if cat == "mystery" or "mystery" in lower or "unsolved" in lower:
            return ShortsFormat.MYSTERY

        if cat == "news":
            return ShortsFormat.NEWS_EXPLAINER

        if "top" in lower or "ranking" in lower or "best" in lower:
            if "3" in lower:
                return ShortsFormat.TOP_3
            if "5" in lower:
                return ShortsFormat.TOP_5
            return ShortsFormat.COUNTDOWN

        if " vs " in lower or " versus " in lower:
            return ShortsFormat.VERSUS

        if "what if" in lower:
            return ShortsFormat.WHAT_IF

        if "myth" in lower or "true or false" in lower or "actually" in lower:
            return ShortsFormat.MYTH_VS_FACT

        if "history" in cat or "timeline" in lower or "evolution" in lower or "origin" in lower:
            return ShortsFormat.TIMELINE

        if "experiment" in lower or "how it works" in lower:
            return ShortsFormat.VISUAL_EXPERIMENT

        if cat in ["science", "space", "animals"]:
            return ShortsFormat.DID_YOU_KNOW

        if cat in ["sports", "gaming"]:
            return ShortsFormat.FAST_EXPLAINER

        return ShortsFormat.DOCUMENTARY

    def select_visual_treatment(self, category: str, fmt: ShortsFormat) -> VisualTreatment:
        """
        Determines the optimal visual treatment style.
        """
        cat = category.lower()
        if fmt == ShortsFormat.MINI_CARTOON or cat == "cartoon":
            return VisualTreatment.CARTOON

        if fmt in [ShortsFormat.VISUAL_EXPERIMENT, ShortsFormat.ANIMATION, ShortsFormat.SIMULATION]:
            return VisualTreatment.ANIMATION

        if cat in ["geography", "history"] or fmt == ShortsFormat.TIMELINE:
            return VisualTreatment.MAPS

        if cat in ["technology", "gaming"]:
            return VisualTreatment.MOTION_GRAPHICS

        if fmt in [ShortsFormat.TOP_3, ShortsFormat.TOP_5, ShortsFormat.COUNTDOWN]:
            return VisualTreatment.ORIGINAL_GRAPHICS

        if cat == "news":
            return VisualTreatment.TEXT_ANIMATION

        return VisualTreatment.MOTION_GRAPHICS

    def determine_direction(
        self,
        topic: str,
        category: str,
        summary: str = "",
        candidate_characters: Optional[List[str]] = None,
    ) -> CreativeDirection:
        """
        Creates a complete creative direction strategy for a Short.
        """
        humor_score = self.calculate_humor_suitability(topic, category, summary)
        is_cartoon = category.lower() in ["cartoon", "original fiction"] or "byte" in topic.lower() or "sam" in topic.lower()
        fmt = self.select_format(topic, category, humor_score, is_fiction_or_cartoon=is_cartoon)
        visual = self.select_visual_treatment(category, fmt)

        # Assign character if cartoon/fiction or high humor storytelling
        assigned_char = None
        if is_cartoon or fmt == ShortsFormat.MINI_CARTOON:
            if candidate_characters and len(candidate_characters) > 0:
                assigned_char = candidate_characters[0]
            else:
                # Default recurring channel duo
                assigned_char = "Byte"

        # Humor techniques
        techniques = []
        if humor_score >= 70:
            techniques = ["unexpected punchline", "deadpan delivery", "visual exaggeration", "absurd comparison"]
        elif humor_score >= 40:
            techniques = ["subtle irony", "playful observation", "curious contrast"]
        else:
            techniques = ["gripping mystery", "suspense build", "scientific precision"]

        # Audio mood and pacing
        if fmt in [ShortsFormat.COMEDY, ShortsFormat.MINI_CARTOON]:
            mood = "comedic"
            pacing = 135
            beat_sec = 2.0
            struct = "CHARACTER_PROBLEM_CHAOS_RESOLUTION" if is_cartoon else "HOOK_SETUP_ESCALATION_TWIST_PAYOFF"
        elif fmt in [ShortsFormat.MYSTERY, ShortsFormat.DRAMATIC_STORY]:
            mood = "mysterious"
            pacing = 115
            beat_sec = 3.0
            struct = "QUESTION_MYSTERY_CLUE_REVEAL"
        elif fmt in [ShortsFormat.NEWS_EXPLAINER, ShortsFormat.FAST_EXPLAINER]:
            mood = "energetic"
            pacing = 145
            beat_sec = 2.2
            struct = "FACT_WHY_EXAMPLE_SURPRISE"
        elif fmt == ShortsFormat.WHAT_IF:
            mood = "dramatic"
            pacing = 130
            beat_sec = 2.5
            struct = "PROBLEM_ATTEMPT_FAILURE_DISCOVERY_SOLUTION"
        else:
            mood = "upbeat"
            pacing = 125
            beat_sec = 2.5
            struct = "HOOK_SETUP_ESCALATION_TWIST_PAYOFF"

        rationale = (
            f"Topic '{topic}' categorized under '{category}'. Humor suitability evaluated at {humor_score}/100. "
            f"Format selected as '{fmt.value}' with visual style '{visual.value}' "
            f"and narrative structure '{struct}'."
        )

        logger.info(f"Creative Direction established: {fmt.value} | Humor: {humor_score} | Visual: {visual.value}")

        return CreativeDirection(
            format=fmt,
            humor_suitability=humor_score,
            visual_treatment=visual,
            pacing_bpm=pacing,
            audio_mood=mood,
            story_structure=struct,
            character_assigned=assigned_char,
            humor_techniques=techniques,
            visual_beat_interval_sec=beat_sec,
            rationale=rationale,
        )
