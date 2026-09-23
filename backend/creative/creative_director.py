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
from backend.core.config import settings
from backend.services.llm_service import LLMService
from backend.learning.content_brain import content_brain
from backend.agents.orchestrator import MultiAgentOrchestrator


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
    REDDIT_STORY = "REDDIT_STORY"
    WOULD_YOU_RATHER = "WOULD_YOU_RATHER"
    SHOWER_THOUGHTS = "SHOWER_THOUGHTS"
    MOTIVATIONAL_QUOTE = "MOTIVATIONAL_QUOTE"
    LONG_FORM_DOCUMENTARY = "LONG_FORM_DOCUMENTARY"
    LONG_FORM_ESSAY = "LONG_FORM_ESSAY"
    STICKMAN_EXPLAINER = "STICKMAN_EXPLAINER"
    VIRAL_PROMPT = "VIRAL_PROMPT"


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
    PANNING_BACKGROUND = "PANNING_BACKGROUND"
    SPLIT_SCREEN_STATIC = "SPLIT_SCREEN_STATIC"
    MINIMAL_TEXT_ONLY = "MINIMAL_TEXT_ONLY"
    WHITEBOARD_STICKMAN = "WHITEBOARD_STICKMAN"
    CINEMATIC = "CINEMATIC"
    WEB_RENDER = "WEB_RENDER"


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
        self.multi_agent = MultiAgentOrchestrator()

    def run_multi_agent_vision(self, topic: str, category: str, video_format: str = "DOCUMENTARY") -> Dict[str, Any]:
        """Runs the new multi-agent collaborative loop to determine script and vision."""
        return self.multi_agent.run_workflow(topic, category, video_format)

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
        Intelligently choose from the 20 Shorts formats based on topic, category, tone, and learned performance.
        """
        lower = topic.lower()
        cat = category.lower()

        if is_fiction_or_cartoon or cat == "cartoon":
            return ShortsFormat.MINI_CARTOON

        # Override to Stickman if explicitly requested by topic (simple heuristic)
        if "stickman" in lower or "whiteboard" in lower:
            return ShortsFormat.STICKMAN_EXPLAINER
            
        # Strongly bias towards VIRAL_PROMPT for tech/AI topics (Must happen before low_resource override)
        if cat in ["technology", "coding", "software"] or "prompt" in lower or "ai" in lower:
            return ShortsFormat.VIRAL_PROMPT

        # In low resource mode, heavily bias toward simple formats
        if settings.render_mode == "low_resource":
            low_resource_formats = [
                ShortsFormat.REDDIT_STORY,
                ShortsFormat.WOULD_YOU_RATHER,
                ShortsFormat.SHOWER_THOUGHTS,
                ShortsFormat.MOTIVATIONAL_QUOTE,
                ShortsFormat.DID_YOU_KNOW
            ]
            import random
            return random.choice(low_resource_formats)

        # Ask Content Brain for the optimal format via Explore/Exploit
        best_format_str = content_brain.select_script_format(category)
            
        try:
            return ShortsFormat[best_format_str]
        except KeyError:
            return ShortsFormat.DOCUMENTARY

    def select_visual_treatment(self, category: str, fmt: ShortsFormat) -> VisualTreatment:
        """
        Determines the optimal visual treatment style.
        """
        if settings.render_mode == "low_resource":
            if fmt == ShortsFormat.REDDIT_STORY:
                return VisualTreatment.PANNING_BACKGROUND
            if fmt == ShortsFormat.WOULD_YOU_RATHER:
                return VisualTreatment.SPLIT_SCREEN_STATIC
            if fmt in [ShortsFormat.SHOWER_THOUGHTS, ShortsFormat.MOTIVATIONAL_QUOTE, ShortsFormat.DID_YOU_KNOW]:
                return VisualTreatment.MINIMAL_TEXT_ONLY

        cat = category.lower()
        if fmt == ShortsFormat.MINI_CARTOON or cat == "cartoon":
            return VisualTreatment.CARTOON
            
        if fmt == ShortsFormat.STICKMAN_EXPLAINER:
            return VisualTreatment.WHITEBOARD_STICKMAN

        if fmt in [ShortsFormat.VISUAL_EXPERIMENT, ShortsFormat.ANIMATION, ShortsFormat.SIMULATION]:
            return VisualTreatment.ANIMATION

        if cat in ["geography", "history"] or fmt == ShortsFormat.TIMELINE:
            return VisualTreatment.MAPS

        if cat in ["technology", "gaming", "coding", "software"]:
            return VisualTreatment.WEB_RENDER

        if fmt in [ShortsFormat.TOP_3, ShortsFormat.TOP_5, ShortsFormat.COUNTDOWN]:
            return VisualTreatment.ORIGINAL_GRAPHICS

        if cat == "news":
            return VisualTreatment.TEXT_ANIMATION
            
        if fmt in [ShortsFormat.REDDIT_STORY]:
            return VisualTreatment.WEB_RENDER
            
        if fmt in [ShortsFormat.DOCUMENTARY, ShortsFormat.LONG_FORM_DOCUMENTARY, ShortsFormat.LONG_FORM_ESSAY, ShortsFormat.MYSTERY, ShortsFormat.DRAMATIC_STORY, ShortsFormat.VIRAL_PROMPT]:
            return VisualTreatment.CINEMATIC

        return VisualTreatment.CINEMATIC # Default everything else to cinematic if it's not a cartoon/stickman

    def determine_direction(
        self,
        topic: str,
        category: str,
        summary: str = "",
        candidate_characters: Optional[List[str]] = None,
        video_format: str = "short",
    ) -> CreativeDirection:
        """
        Creates a complete creative direction strategy for a Video.
        """
        humor_score = self.calculate_humor_suitability(topic, category, summary)
        is_cartoon = category.lower() in ["cartoon", "original fiction"] or "byte" in topic.lower() or "sam" in topic.lower()
        
        if video_format == "long":
            fmt = ShortsFormat.LONG_FORM_DOCUMENTARY if humor_score < 50 else ShortsFormat.LONG_FORM_ESSAY
        else:
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
        elif fmt in [ShortsFormat.LONG_FORM_DOCUMENTARY, ShortsFormat.LONG_FORM_ESSAY]:
            mood = "dramatic"
            pacing = 110
            beat_sec = 5.0
            struct = "HOOK_INTRO_DEEPDIVE_CLIMAX_CONCLUSION"
        elif fmt == ShortsFormat.STICKMAN_EXPLAINER:
            mood = "comedic"
            pacing = 140
            beat_sec = 3.0
            struct = "HOOK_SETUP_ESCALATION_TWIST_PAYOFF"
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
