"""
Story Engine for YouTube Shorts.
Implements 5 distinct narrative architectures:
1. Hook -> Setup -> Escalation -> Twist -> Payoff
2. Question -> Mystery -> Clue -> Reveal
3. Problem -> Attempt -> Failure -> Discovery -> Solution
4. Fact -> Why -> Example -> Surprise
5. Character -> Problem -> Chaos -> Resolution

Never repeats the exact same structure. Ensures pacing fits under 60 seconds (120-160 words).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import json
from backend.core.logging import logger
from backend.services.llm_service import LLMService


class StoryStructure(str, Enum):
    HOOK_SETUP_ESCALATION_TWIST_PAYOFF = "HOOK_SETUP_ESCALATION_TWIST_PAYOFF"
    QUESTION_MYSTERY_CLUE_REVEAL = "QUESTION_MYSTERY_CLUE_REVEAL"
    PROBLEM_ATTEMPT_FAILURE_DISCOVERY_SOLUTION = "PROBLEM_ATTEMPT_FAILURE_DISCOVERY_SOLUTION"
    FACT_WHY_EXAMPLE_SURPRISE = "FACT_WHY_EXAMPLE_SURPRISE"
    CHARACTER_PROBLEM_CHAOS_RESOLUTION = "CHARACTER_PROBLEM_CHAOS_RESOLUTION"
    REDDIT_STORY_NARRATIVE = "REDDIT_STORY_NARRATIVE"
    QUIZ_NARRATIVE = "QUIZ_NARRATIVE"


@dataclass
class StoryBeat:
    beat_name: str
    target_start_sec: float
    target_duration_sec: float
    narration: str
    visual_description: str
    camera_movement: str  # e.g., "slow zoom in", "hard cut", "whip pan", "shake", "pan right"
    on_screen_text: str
    sound_effect: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "beat_name": self.beat_name,
            "target_start_sec": self.target_start_sec,
            "target_duration_sec": self.target_duration_sec,
            "narration": self.narration,
            "visual_description": self.visual_description,
            "camera_movement": self.camera_movement,
            "on_screen_text": self.on_screen_text,
            "sound_effect": self.sound_effect,
        }


@dataclass
class StoryScript:
    structure: StoryStructure
    beats: List[StoryBeat]
    total_words: int
    estimated_duration_sec: float
    full_narration: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "structure": self.structure.value,
            "beats": [b.to_dict() for b in self.beats],
            "total_words": self.total_words,
            "estimated_duration_sec": self.estimated_duration_sec,
            "full_narration": self.full_narration,
        }


class StoryEngine:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.ollama = llm_service or LLMService()

    def select_best_structure(self, category: str, format_name: str) -> StoryStructure:
        """Picks the narrative structure best tailored to format and category."""
        cat = category.lower()
        fmt = format_name.upper()

        if fmt in ["MINI_CARTOON", "COMEDY"] or cat in ["cartoon", "humor"]:
            return StoryStructure.CHARACTER_PROBLEM_CHAOS_RESOLUTION

        if fmt in ["MYSTERY", "DOCUMENTARY"] or cat == "mystery":
            return StoryStructure.QUESTION_MYSTERY_CLUE_REVEAL

        if fmt in ["FAST_EXPLAINER", "NEWS_EXPLAINER", "TOP_3", "TOP_5"]:
            return StoryStructure.FACT_WHY_EXAMPLE_SURPRISE

        if fmt in ["WHAT_IF", "VISUAL_EXPERIMENT"]:
            return StoryStructure.PROBLEM_ATTEMPT_FAILURE_DISCOVERY_SOLUTION

        if fmt == "REDDIT_STORY":
            return StoryStructure.REDDIT_STORY_NARRATIVE

        if fmt == "WOULD_YOU_RATHER":
            return StoryStructure.QUIZ_NARRATIVE

        return StoryStructure.HOOK_SETUP_ESCALATION_TWIST_PAYOFF

    def generate_script(
        self,
        topic: str,
        category: str,
        hook: str,
        research_notes: str,
        structure: StoryStructure,
        character_name: Optional[str] = None,
    ) -> StoryScript:
        """
        Generates a rhythmic, high-retention Short script formatted into 4-5 visual beats.
        """
        prompt = f"""
You are an award-winning YouTube Shorts scriptwriter and creative director.
Write a high-retention, viral Short script about: "{topic}" (Category: {category}).

SELECTED NARRATIVE STRUCTURE: {structure.value}
OPENING HOOK: "{hook}"
RESEARCH & FACTS:
{research_notes}

{f"RECURRING CHARACTER: {character_name}" if character_name else ""}

RULES:
1. Total length must be 120 - 150 words (under 45 seconds spoken).
2. Exactly follow the 5 story beats for {structure.value}.
3. Every beat MUST specify:
   - "narration": punchy spoken text (no fluff).
   - "visual": description of 9:16 vertical visual action.
   - "camera": camera movement (e.g., "slow zoom in", "hard punch cut", "whip pan", "dramatic shake").
   - "screen_text": 2-4 words of high-impact on-screen captions.
   - "sfx": optional sound effect (whoosh, hit, bass_drop, record_scratch, pop).

Return pure JSON matching this schema:
{{
  "beats": [
    {{
      "beat_name": "Hook",
      "narration": "...",
      "visual": "...",
      "camera": "punch cut",
      "screen_text": "...",
      "sfx": "bass_drop"
    }}
  ]
}}
"""
        response_text = self.ollama.generate(
            prompt=prompt,
            system_prompt="You are an elite short-form content architect. Output only valid JSON.",
            json_mode=True,
            temperature=0.6,
        )

        data = self.ollama.parse_json_safely(response_text)
        if data and "beats" in data and isinstance(data["beats"], list) and len(data["beats"]) >= 3:
            beats = []
            cur_time = 0.0
            total_beats = len(data["beats"])
            beat_duration = 45.0 / total_beats

            for raw in data["beats"]:
                beat = StoryBeat(
                    beat_name=raw.get("beat_name", "Beat"),
                    target_start_sec=round(cur_time, 2),
                    target_duration_sec=round(beat_duration, 2),
                    narration=raw.get("narration", "").strip(),
                    visual_description=raw.get("visual", "Dynamic scene visual").strip(),
                    camera_movement=raw.get("camera", "slow zoom in").strip(),
                    on_screen_text=raw.get("screen_text", "").strip(),
                    sound_effect=raw.get("sfx"),
                )
                beats.append(beat)
                cur_time += beat_duration

            full_narration = " ".join(b.narration for b in beats)
            total_words = len(full_narration.split())
            est_duration = round(total_words / 2.5, 1)  # ~150 wpm

            return StoryScript(
                structure=structure,
                beats=beats,
                total_words=total_words,
                estimated_duration_sec=est_duration,
                full_narration=full_narration,
            )

        # Resilient fallback procedural script generator
        return self._generate_fallback_script(topic, category, hook, structure, character_name)

    def _generate_fallback_script(
        self,
        topic: str,
        category: str,
        hook: str,
        structure: StoryStructure,
        character_name: Optional[str] = None,
    ) -> StoryScript:
        """Generates deterministic rhythmic beats if LLM is unavailable."""
        char_tag = f"{character_name}: " if character_name else ""

        if structure == StoryStructure.CHARACTER_PROBLEM_CHAOS_RESOLUTION:
            beats = [
                StoryBeat("Character Intro", 0.0, 5.0, hook, f"{character_name or 'Character'} looks straight at camera confidently.", "punch cut", "LOOK AT THIS", "pop"),
                StoryBeat("Problem", 5.0, 10.0, f"{char_tag}Everything seemed completely under control, until one fatal calculation.", "Split screen with warning graphics.", "slow zoom in", "CRITICAL ERROR", "whoosh"),
                StoryBeat("Chaos", 15.0, 15.0, f"{char_tag}Chaos erupted in seconds as the entire system tried to resolve the anomaly!", "Fast-paced visual sequence with motion shakes.", "dramatic shake", "TOTAL CHAOS", "record_scratch"),
                StoryBeat("Climax", 30.0, 10.0, f"{char_tag}Against all odds, the unexpected answer surfaced right in front of us.", "Dynamic glow effect and high-contrast reveal.", "whip pan", "THE ANSWER", "hit"),
                StoryBeat("Resolution", 40.0, 8.0, f"{char_tag}And that is why you never doubt the impossible. Subscribe for more crazy facts!", "Character smirking with channel logo.", "slow zoom out", "SUBSCRIBE", "pop"),
            ]
        elif structure == StoryStructure.QUESTION_MYSTERY_CLUE_REVEAL:
            beats = [
                StoryBeat("Question", 0.0, 5.0, hook, "Dark atmospheric background with glowing question mark.", "slow zoom in", "THE MYSTERY", "bass_drop"),
                StoryBeat("Mystery", 5.0, 12.0, f"For decades, researchers studying {topic} could not explain what they were seeing.", "Archival footage and mysterious map textures.", "pan right", "UNEXPLAINED", "whoosh"),
                StoryBeat("Clue", 17.0, 14.0, "Then, an accidental observation revealed an anomaly nobody expected.", "Close-up microscopic / telescopic visualization.", "punch cut", "THE CLUE", "hit"),
                StoryBeat("Reveal", 31.0, 11.0, "It turns out the entire phenomenon was caused by something right under our noses.", "Vibrant graphic reveal showing the true mechanism.", "whip pan", "REVEALED", "hit"),
                StoryBeat("Payoff", 42.0, 8.0, "Now you know the truth behind {topic}. Did this surprise you? Comment below!", "End card with looping visual teaser.", "slow zoom out", "WHAT DO YOU THINK?", "pop"),
            ]
        elif structure == StoryStructure.FACT_WHY_EXAMPLE_SURPRISE:
            beats = [
                StoryBeat("Fact", 0.0, 5.0, hook, "Massive bold typography on top of vibrant motion background.", "punch cut", "DID YOU KNOW?", "hit"),
                StoryBeat("Why", 5.0, 12.0, f"The reason {topic} works this way comes down to basic physics and psychology.", "Infographic breakdown with smooth diagram animations.", "slow zoom in", "HERE IS WHY", "whoosh"),
                StoryBeat("Example", 17.0, 14.0, "Take a look at what happened when scientists tested this under real conditions.", "Split-screen side-by-side demonstration.", "pan left", "REAL TEST", "pop"),
                StoryBeat("Surprise", 31.0, 10.0, "The result was ten times bigger than anyone predicted.", "Shockwave visual effect with high-contrast text.", "dramatic shake", "10X BIGGER", "bass_drop"),
                StoryBeat("Conclusion", 41.0, 7.0, "Next time you see this, remember this exact detail. Follow for more daily knowledge!", "Dynamic call to action with clean branding.", "punch cut", "FOLLOW FOR MORE", "pop"),
            ]
        else:  # HOOK_SETUP_ESCALATION_TWIST_PAYOFF
            beats = [
                StoryBeat("Hook", 0.0, 5.0, hook, "Extreme close up with dramatic entrance.", "punch cut", "WAIT FOR IT", "hit"),
                StoryBeat("Setup", 5.0, 11.0, f"At first glance, {topic} seems like a normal everyday occurrence.", "Clean smooth establishing visual.", "slow zoom in", "SEEMS NORMAL", "whoosh"),
                StoryBeat("Escalation", 16.0, 14.0, "Except the deeper you look, the stranger the details become.", "Accelerating cuts and energetic motion graphics.", "whip pan", "GETS STRANGER", "bass_drop"),
                StoryBeat("Twist", 30.0, 11.0, "Here is the twist nobody saw coming: the entire premise was inverted.", "Hard contrast flip with bold revelation text.", "dramatic shake", "PLOT TWIST", "record_scratch"),
                StoryBeat("Payoff", 41.0, 7.0, "And that completely changes everything. Drop your thoughts in the comments!", "Polished end-frame with subscribe animation.", "slow zoom out", "COMMENT BELOW", "pop"),
            ]

        full_narration = " ".join(b.narration for b in beats)
        total_words = len(full_narration.split())
        est_duration = round(total_words / 2.5, 1)

        return StoryScript(
            structure=structure,
            beats=beats,
            total_words=total_words,
            estimated_duration_sec=est_duration,
            full_narration=full_narration,
        )
