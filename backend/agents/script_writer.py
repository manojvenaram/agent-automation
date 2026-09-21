"""
ScriptWriterAgent for YouTube Shorts.
Generates retention-engineered scripts adhering strictly to Shorts pacing:
- 0–3 sec: Strong Hook
- 3–10 sec: Context
- 10–40 sec: Core Facts & Mechanism
- 40–55 sec: Mind-Blowing Payoff
- Final: Optional CTA
Calculates duration (130–160 WPM) and automatically resizes scripts exceeding duration limits.
"""

import json
from typing import List, Optional
from backend.core.config import settings
from backend.core.database import save_script
from backend.core.logging import logger
from backend.models import ResearchSource, ScriptModel, ScriptScene
from backend.services.llm_service import llm_service


class ScriptWriterAgent:
    def __init__(self):
        self.wpm = settings.target_words_per_minute

    def generate_script(
        self,
        project_id: str,
        topic: str,
        sources: List[ResearchSource],
        hook: str,
    ) -> ScriptModel:
        """Craft a high-retention, fact-grounded script and scene breakdown."""
        logger.info(f"Generating script for topic '{topic}'...")

        research_summary = "\n".join([f"- {s.title}: {s.extract[:400]}" for s in sources])

        prompt = (
            f"Topic: {topic}\n"
            f"Selected Hook: {hook}\n"
            f"Research Evidence:\n{research_summary}\n\n"
            f"Task: Write a viral, scientifically accurate 35-45 second YouTube Shorts script.\n"
            f"Rules:\n"
            f"1. Target total words: 80 to 110 words (130-160 WPM pace).\n"
            f"2. Structure:\n"
            f"   - hook: Must be the selected hook or a punchy variation.\n"
            f"   - context: Set the scene in 1-2 sentences.\n"
            f"   - main_facts: Explain the scientific mechanism clearly without jargon.\n"
            f"   - payoff: The mind-bending conclusion or counter-intuitive punchline.\n"
            f"   - cta: Short 1-sentence prompt.\n"
            f"3. Do NOT use filler words like 'welcome back', 'in this video', or 'hey guys'.\n"
            f"4. Provide 4 to 6 scenes with duration_est and visual_description.\n"
            f"5. CRITICAL: Never reuse scripts, narratives, or specific visuals from previous videos. Everything must be 100% unique and original.\n"
            f"Output strictly JSON:\n"
            f'{{"hook": "...", "context": "...", "main_facts": "...", "payoff": "...", "cta": "...", "scenes": [{{"scene_index": 1, "narration": "...", "duration_est": 4.0, "visual_description": "..."}}]}}'
        )

        response = llm_service.generate(prompt, json_mode=True)
        script_data = None
        try:
            # Clean markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            script_data = json.loads(clean_response.strip())
        except Exception as e:
            logger.warning(f"Could not parse script JSON ({e}), utilizing dynamic template.")

        if not script_data or not script_data.get("scenes"):
            # Dynamic fallback script based on topic
            hook_text = hook or f"Have you ever wondered about {topic}?"
            context_text = f"The truth behind {topic} is actually more fascinating than you might think."
            main_facts_text = f"Research shows that this phenomenon has far-reaching implications that scientists are still studying today."
            payoff_text = f"So the next time you think about {topic}, remember that there is always more than meets the eye."
            cta_text = "Subscribe for more incredible facts!"

            scenes = [
                ScriptScene(scene_index=1, narration=hook_text, duration_est=4.0, visual_description=f"Cinematic visual representing {topic}"),
                ScriptScene(scene_index=2, narration=context_text, duration_est=7.5, visual_description="Abstract background related to mystery"),
                ScriptScene(scene_index=3, narration=main_facts_text, duration_est=9.5, visual_description="Research or scientific visualization"),
                ScriptScene(scene_index=4, narration=payoff_text, duration_est=8.5, visual_description="Mind-blowing revelation sequence"),
                ScriptScene(scene_index=5, narration=cta_text, duration_est=3.5, visual_description="Subscribe button animation over dynamic background"),
            ]
            full_narration = f"{hook_text} {context_text} {main_facts_text} {payoff_text} {cta_text}"
        else:
            hook_text = script_data.get("hook", hook)
            context_text = script_data.get("context", "")
            main_facts_text = script_data.get("main_facts", "")
            payoff_text = script_data.get("payoff", "")
            cta_text = script_data.get("cta", "Subscribe for more!")
            full_narration = f"{hook_text} {context_text} {main_facts_text} {payoff_text} {cta_text}".strip()

            scenes = []
            for sc in script_data.get("scenes", []):
                scenes.append(
                    ScriptScene(
                        scene_index=sc.get("scene_index", len(scenes) + 1),
                        narration=sc.get("narration", ""),
                        duration_est=float(sc.get("duration_est", 5.0)),
                        visual_description=sc.get("visual_description", "Cosmic background visualization"),
                    )
                )

        word_count = len(full_narration.split())
        est_duration = round((word_count / self.wpm) * 60, 1)

        # Duration enforcement: if > max_duration (60s), trim sentences
        if est_duration > settings.max_duration:
            logger.info(f"Script duration ({est_duration}s) exceeds max limit ({settings.max_duration}s), trimming...")
            sentences = full_narration.split(". ")
            if len(sentences) > 3:
                full_narration = ". ".join(sentences[:3]) + "."
                word_count = len(full_narration.split())
                est_duration = round((word_count / self.wpm) * 60, 1)

        model = ScriptModel(
            hook=hook_text,
            context=context_text,
            main_facts=main_facts_text,
            payoff=payoff_text,
            cta=cta_text,
            full_narration=full_narration,
            word_count=word_count,
            estimated_duration_sec=est_duration,
            scenes=scenes,
        )

        save_script(project_id, model)
        logger.info(f"Script saved: {word_count} words, ~{est_duration}s duration, {len(scenes)} scenes.")
        return model


script_writer_agent = ScriptWriterAgent()
