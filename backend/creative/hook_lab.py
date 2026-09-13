"""
Hook Lab for YouTube Shorts.
Generates at least 10 candidate hooks per topic across diverse psychological archetypes:
1. The Negative Frame ("Stop doing X...")
2. The Unbelievable Fact ("Scientists just found something that shouldn't exist...")
3. The Counter-Intuitive Twist ("The smartest thing to do is the exact opposite...")
4. The Urgent Warning ("If you ever see this, run...")
5. The Curiosity Gap ("Nobody knew why this happened until yesterday...")
6. The Secret Reveal ("Here is the secret they never tell you...")
7. The Absurd Reality ("This sounds fake, but it actually happened...")
8. The Direct Challenge ("99% of people get this completely wrong...")
9. The Time Travel ("In 100 years, historians will look back at this...")
10. The Micro-Story ("A single mistake cost this company 2 billion dollars...")

Scores each on:
- Curiosity (0-100)
- Surprise (0-100)
- Emotional Impact (0-100)
- Clarity (0-100)
- Novelty (0-100)
- Retention Potential (0-100)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
from backend.core.logging import logger
from backend.services.llm_service import LLMService


@dataclass
class CandidateHook:
    text: str
    archetype: str
    curiosity: int
    surprise: int
    emotional_impact: int
    clarity: int
    novelty: int
    retention_potential: int
    composite_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "archetype": self.archetype,
            "curiosity": self.curiosity,
            "surprise": self.surprise,
            "emotional_impact": self.emotional_impact,
            "clarity": self.clarity,
            "novelty": self.novelty,
            "retention_potential": self.retention_potential,
            "composite_score": round(self.composite_score, 1),
        }


class HookLab:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.ollama = llm_service or LLMService()

    def score_hook(
        self,
        text: str,
        archetype: str,
        category: str = "general",
    ) -> CandidateHook:
        """
        Evaluate a hook across the 6 retention dimensions.
        """
        lower = text.lower()
        words = text.split()
        word_count = len(words)

        # Base clarity: punchy (6-14 words) is ideal for 1st-second scroll-stopping
        if 5 <= word_count <= 15:
            clarity = 92
        elif word_count < 5:
            clarity = 75
        else:
            clarity = max(50, 90 - (word_count - 15) * 3)

        # Curiosity signals
        curiosity_signals = ["why", "how", "secret", "nobody", "never", "hidden", "reason", "truth", "what if"]
        curiosity_count = sum(1 for w in curiosity_signals if w in lower)
        curiosity = min(98, 65 + curiosity_count * 10)

        # Surprise signals
        surprise_signals = ["actually", "bizarre", "insane", "impossible", "shocking", "unexpected", "never", "fake", "destroy"]
        surprise_count = sum(1 for w in surprise_signals if w in lower)
        surprise = min(98, 60 + surprise_count * 12)

        # Emotional impact
        emotional_signals = ["warning", "danger", "mistake", "ruined", "hero", "terrifying", "craziest", "genius", "genius"]
        emotional_count = sum(1 for w in emotional_signals if w in lower)
        emotional = min(95, 55 + emotional_count * 12)

        # Novelty
        novelty = 80
        if any(w in lower for w in ["just discovered", "new", "first time", "strange anomaly", "revealed"]):
            novelty = 94

        # Retention potential: derived from strong scroll-stopping patterns
        retention = int(
            0.30 * curiosity
            + 0.25 * surprise
            + 0.20 * clarity
            + 0.15 * emotional
            + 0.10 * novelty
        )

        composite = (
            0.25 * curiosity
            + 0.20 * surprise
            + 0.15 * emotional
            + 0.15 * clarity
            + 0.10 * novelty
            + 0.15 * retention
        )

        return CandidateHook(
            text=text.strip(),
            archetype=archetype,
            curiosity=curiosity,
            surprise=surprise,
            emotional_impact=emotional,
            clarity=clarity,
            novelty=novelty,
            retention_potential=retention,
            composite_score=round(composite, 1),
        )

    def generate_hooks(
        self,
        topic: str,
        category: str,
        key_facts: str = "",
    ) -> List[CandidateHook]:
        """
        Generates at least 10 high-impact candidate hooks.
        """
        prompt = f"""
You are the world's top YouTube Shorts hook specialist.
Generate exactly 10 distinct, scroll-stopping hooks for this topic: "{topic}" (Category: {category}).
Facts: {key_facts}

Each hook must target one of these 10 psychology archetypes:
1. Negative Frame
2. Unbelievable Fact
3. Counter-Intuitive Twist
4. Urgent Warning
5. Curiosity Gap
6. Secret Reveal
7. Absurd Reality
8. Direct Challenge
9. Time Horizon / Evolution
10. High-Stakes Micro-Story

Rules:
- Length: 7 to 14 words per hook.
- Immediate scroll-stop power within 0.8 seconds.
- Output strictly JSON:
{{
  "hooks": [
    {{"archetype": "Negative Frame", "text": "..."}},
    ...
  ]
}}
"""
        response_text = self.ollama.generate(
            prompt=prompt,
            system_prompt="You are an expert short-form viral hook architect. Output only valid JSON.",
            json_mode=True,
            temperature=0.7,
        )

        results: List[CandidateHook] = []
        data = self.ollama.parse_json_safely(response_text)
        if data and "hooks" in data and isinstance(data["hooks"], list):
            for item in data["hooks"]:
                txt = item.get("text", "").strip()
                arch = item.get("archetype", "Psychological Hook")
                if txt and len(txt) > 10:
                    results.append(self.score_hook(txt, arch, category))

        # Ensure we have at least 10 candidate hooks via archetype formulas
        if len(results) < 10:
            fallback_hooks = self._create_archetypal_hooks(topic, category)
            existing_texts = {h.text for h in results}
            for arch, text in fallback_hooks:
                if text not in existing_texts and len(results) < 10:
                    results.append(self.score_hook(text, arch, category))

        # Sort by composite score descending
        results.sort(key=lambda h: h.composite_score, reverse=True)
        logger.info(f"Hook Lab generated {len(results)} hooks. Top score: {results[0].composite_score} ({results[0].archetype})")
        return results

    def _create_archetypal_hooks(self, topic: str, category: str) -> List[tuple]:
        """Generates formulaic hooks across the 10 psychological archetypes."""
        return [
            ("Unbelievable Fact", f"The single strangest fact about {topic} sounds completely made up."),
            ("Curiosity Gap", f"Almost nobody knows the real reason behind {topic}... until now."),
            ("Direct Challenge", f"99% of people have no idea how {topic} actually works."),
            ("Counter-Intuitive Twist", f"Everything you were told about {topic} is completely backwards."),
            ("Negative Frame", f"Stop ignoring {topic} before you make this massive mistake."),
            ("Secret Reveal", f"Here is the bizarre secret about {topic} they never talk about."),
            ("Absurd Reality", f"Scientists still cannot explain how {topic} became this crazy."),
            ("Urgent Warning", f"If you ever encounter {topic}, remember this one rule immediately."),
            ("High-Stakes Micro-Story", f"One single detail about {topic} changed history forever."),
            ("Time Horizon", f"In 50 years, people will look back at {topic} with disbelief."),
        ]

    def select_best_hook(self, topic: str, category: str, key_facts: str = "") -> CandidateHook:
        """Generates 10 hooks and returns the single highest-scoring winner."""
        hooks = self.generate_hooks(topic, category, key_facts)
        return hooks[0]
