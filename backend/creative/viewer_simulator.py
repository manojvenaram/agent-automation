"""
Viewer Simulator Agent for YouTube Shorts.
Simulates diverse audience personas:
- Casual US Viewer (wants immediate relevance, high energy, crisp audio)
- Gen Z Viewer (attention span < 1.5s, needs unexpected motion, irony, meme cadence)
- Sports Fan (demands real stats, high-stakes competition, athlete drama)
- Tech Enthusiast (demands factual accuracy, cutting-edge mechanics, zero fluff)
- Comedy Viewer (reacts to absurdity, timing, punchline payoffs)
- Science Buff (seeks cosmic/biological mind-benders, evidence)
- General Global Viewer (needs universal concepts, simple clear English)

Evaluates:
- 1s scroll-stop power
- 3s retention hold
- 5s commitment
- Story clarity & curiosity
- Rewatch potential

Flags weak hooks for rewrite before production.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import json
from backend.core.logging import logger
from backend.services.llm_service import LLMService


class ViewerPersona(str, Enum):
    CASUAL_US = "CASUAL_US"
    GEN_Z = "GEN_Z"
    SPORTS_FAN = "SPORTS_FAN"
    TECH_ENTHUSIAST = "TECH_ENTHUSIAST"
    COMEDY_VIEWER = "COMEDY_VIEWER"
    SCIENCE_BUFF = "SCIENCE_BUFF"
    GENERAL_VIEWER = "GENERAL_VIEWER"


@dataclass
class PersonaEvaluation:
    persona: ViewerPersona
    stopped_scrolling: bool
    retention_1s: int
    retention_3s: int
    retention_5s: int
    clarity_score: int
    curiosity_score: int
    payoff_score: int
    rewatch_potential: int
    verdict_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona": self.persona.value,
            "stopped_scrolling": self.stopped_scrolling,
            "retention_1s": self.retention_1s,
            "retention_3s": self.retention_3s,
            "retention_5s": self.retention_5s,
            "clarity_score": self.clarity_score,
            "curiosity_score": self.curiosity_score,
            "payoff_score": self.payoff_score,
            "rewatch_potential": self.rewatch_potential,
            "verdict_notes": self.verdict_notes,
        }


@dataclass
class SimulationResult:
    composite_retention: float
    scroll_stop_rate: float
    evaluations: List[PersonaEvaluation]
    verdict: str  # "PASS" or "REWRITE_HOOK"
    weakest_point: Optional[str] = None
    suggested_fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "composite_retention": round(self.composite_retention, 1),
            "scroll_stop_rate": round(self.scroll_stop_rate, 2),
            "verdict": self.verdict,
            "weakest_point": self.weakest_point,
            "suggested_fix": self.suggested_fix,
            "evaluations": [e.to_dict() for e in self.evaluations],
        }


class ViewerSimulatorAgent:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.ollama = llm_service or LLMService()

    def simulate(
        self,
        topic: str,
        category: str,
        hook: str,
        opening_script: str = "",
    ) -> SimulationResult:
        """
        Runs the simulation across all 7 viewer personas.
        """
        evaluations: List[PersonaEvaluation] = []
        personas = [
            ViewerPersona.CASUAL_US,
            ViewerPersona.GEN_Z,
            ViewerPersona.SPORTS_FAN,
            ViewerPersona.TECH_ENTHUSIAST,
            ViewerPersona.COMEDY_VIEWER,
            ViewerPersona.SCIENCE_BUFF,
            ViewerPersona.GENERAL_VIEWER,
        ]

        for persona in personas:
            ev = self._evaluate_persona(persona, topic, category, hook, opening_script)
            evaluations.append(ev)

        # Calculate composite metrics
        stop_count = sum(1 for e in evaluations if e.stopped_scrolling)
        scroll_stop_rate = stop_count / len(evaluations)
        avg_retention = sum(
            (e.retention_1s * 0.4 + e.retention_3s * 0.35 + e.retention_5s * 0.25)
            for e in evaluations
        ) / len(evaluations)

        verdict = "PASS"
        weakest = None
        suggested_fix = None

        if avg_retention < 70 or scroll_stop_rate < 0.6:
            verdict = "REWRITE_HOOK"
            # Find the persona with the lowest score
            lowest = min(evaluations, key=lambda e: e.retention_1s)
            weakest = f"Low initial scroll-stop on {lowest.persona.value} ({lowest.retention_1s}/100): {lowest.verdict_notes}"
            suggested_fix = f"Make the first 5 words more visually tangible, cut introductory filler, and start directly inside the action."

        logger.info(f"Viewer Simulation completed: Verdict={verdict} | ScrollStop={scroll_stop_rate:.0%} | Retention={avg_retention:.1f}")

        return SimulationResult(
            composite_retention=avg_retention,
            scroll_stop_rate=scroll_stop_rate,
            evaluations=evaluations,
            verdict=verdict,
            weakest_point=weakest,
            suggested_fix=suggested_fix,
        )

    def _evaluate_persona(
        self,
        persona: ViewerPersona,
        topic: str,
        category: str,
        hook: str,
        opening_script: str,
    ) -> PersonaEvaluation:
        """Calculates persona-specific attention metrics."""
        hook_lower = hook.lower()
        cat_lower = category.lower()
        word_count = len(hook.split())

        # Baseline scores
        r1 = 80
        r3 = 75
        r5 = 70
        clarity = 85
        curiosity = 80
        payoff = 75
        rewatch = 70

        # Adjust for persona preferences
        if persona == ViewerPersona.CASUAL_US:
            if word_count > 14:
                r1 -= 15
                notes = "Hook is too verbose for American casual scrollers."
            elif any(w in hook_lower for w in ["never", "why", "secret", "cost", "mistake"]):
                r1 += 12
                notes = "Strong curiosity hook, resonates with US viewers."
            else:
                notes = "Decent relevance, solid scroll-stop."

        elif persona == ViewerPersona.GEN_Z:
            if word_count > 10:
                r1 -= 20
                r3 -= 15
                notes = "Exceeds 1.5s attention threshold without immediate shock."
            elif any(w in hook_lower for w in ["insane", "literally", "actually", "sounds fake", "wild", "worst"]):
                r1 += 15
                curiosity += 10
                notes = "High-energy phrasing stops Gen-Z scroll immediately."
            else:
                notes = "Needs more unexpected contrast in opening 3 words."

        elif persona == ViewerPersona.SPORTS_FAN:
            if cat_lower == "sports" or any(w in hook_lower for w in ["record", "game", "player", "championship", "win", "impossible"]):
                r1 = 92
                curiosity = 90
                notes = "Direct sports hook captures fan attention immediately."
            else:
                r1 = 65
                notes = "Not primary sports interest, but acceptable general trivia."

        elif persona == ViewerPersona.TECH_ENTHUSIAST:
            if cat_lower in ["technology", "science", "gaming"] or any(w in hook_lower for w in ["ai", "chip", "code", "quantum", "hack"]):
                r1 = 90
                clarity = 88
                notes = "Intellectually intriguing tech angle."
            elif "clickbait" in hook_lower or word_count > 16:
                r1 -= 15
                notes = "Feels slightly generic or speculative."
            else:
                notes = "Acceptable clarity."

        elif persona == ViewerPersona.COMEDY_VIEWER:
            if cat_lower in ["humor", "cartoon"] or any(w in hook_lower for w in ["bizarre", "worst", "mistake", "absurd", "ridiculous"]):
                r1 = 94
                curiosity = 92
                rewatch += 15
                notes = "Strong comedic premise with ironical potential."
            else:
                r1 = 70
                notes = "Factual hook, low immediate laugh expectation."

        elif persona == ViewerPersona.SCIENCE_BUFF:
            if cat_lower in ["science", "space", "animals", "geography"] or any(w in hook_lower for w in ["planet", "gravity", "brain", "atom", "black hole"]):
                r1 = 95
                curiosity = 95
                notes = "Fascinating natural or cosmic mystery."
            else:
                r1 = 68
                notes = "Non-science topic; average interest."

        else:  # GENERAL_VIEWER
            if 6 <= word_count <= 12:
                r1 = 88
                notes = "Broad universal appeal, easy to understand."
            else:
                r1 = 72
                notes = "Moderate general appeal."

        stopped = (r1 >= 68)
        return PersonaEvaluation(
            persona=persona,
            stopped_scrolling=stopped,
            retention_1s=min(100, max(20, r1)),
            retention_3s=min(100, max(20, r3)),
            retention_5s=min(100, max(20, r5)),
            clarity_score=min(100, max(20, clarity)),
            curiosity_score=min(100, max(20, curiosity)),
            payoff_score=min(100, max(20, payoff)),
            rewatch_potential=min(100, max(20, rewatch)),
            verdict_notes=notes,
        )
