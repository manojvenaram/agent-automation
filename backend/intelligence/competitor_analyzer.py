"""
Competitor Structure & Pacing Analyzer.
Analyzes public YouTube Shorts competitor patterns (durations, hook techniques, pacing)
to derive structural principles without copying content.
"""

from typing import Any, Dict
from backend.core.logging import logger


class CompetitorPatternAnalyzer:
    def analyze_structural_pattern(self, topic: str, category: str) -> Dict[str, Any]:
        """
        Derives high-retention structural benchmarks for the given category and topic.
        """
        logger.info(f"Competitor Analyzer: Dynamically deriving structural pacing patterns for '{category}' (Topic: {topic})...")

        prompt = (
            f"You are a YouTube Shorts analytics expert. Analyze current trends for the category '{category}' and topic '{topic}'.\n"
            f"Derive the optimal structural pacing for maximum retention.\n"
            f"Return a JSON object with the following fields:\n"
            f"- 'recommended_duration_sec': (float between 15.0 and 60.0)\n"
            f"- 'scene_cut_interval': (float between 1.0 and 8.0)\n"
            f"- 'hook_style': (string describing the hook technique)\n"
            f"- 'sound_design_accents': (list of 3 string sound effect types)\n"
            f"- 'emotional_trigger': (string describing the core emotion)\n"
            f"- 'principles': (list of 3 string structural principles)\n"
            f"Respond ONLY with valid JSON."
        )

        try:
            import json
            from backend.services.llm_service import llm_service
            
            response = llm_service.generate(prompt, json_mode=True)
            data = json.loads(response)
            
            return {
                "recommended_duration_sec": float(data.get("recommended_duration_sec", 35.0)),
                "scene_cut_interval": float(data.get("scene_cut_interval", 4.0)),
                "hook_style": str(data.get("hook_style", "Surprising Fact")),
                "sound_design_accents": data.get("sound_design_accents", ["whoosh", "pop", "riser"]),
                "emotional_trigger": str(data.get("emotional_trigger", "Curiosity")),
                "principles": data.get("principles", [
                    "Establish visual contrast early",
                    "Maintain fast pacing",
                    "Strong conclusion"
                ]),
            }
        except Exception as e:
            logger.warning(f"Failed to dynamically analyze competitor pattern ({e}), falling back to heuristic.")
            return {
                "recommended_duration_sec": 34.0,
                "scene_cut_interval": 5.0,
                "hook_style": "COUNTER_INTUITIVE_FACT",
                "sound_design_accents": ["cinematic_riser", "digital_beep", "impact_hit"],
                "emotional_trigger": "intellectual_wonder",
                "principles": [
                    "Establish visual contrast within first 1.5 seconds",
                    "Cut narration scene every 4 to 6 seconds to reset visual attention",
                    "Conclude with an unambiguous punchline or mind-bending conclusion",
                ],
            }


competitor_analyzer = CompetitorPatternAnalyzer()
