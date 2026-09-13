"""
VoiceAgent for YouTube Shorts Narration.
Generates, normalizes, and packages high-fidelity spoken voiceover.
"""

import random
from pathlib import Path
from typing import Tuple
from backend.core.logging import logger
from backend.models import ScriptModel
from backend.services.tts_service import tts_service


class VoiceAgent:
    def produce_voiceover(
        self,
        project_id: str,
        script: ScriptModel,
        project_dir: Path,
    ) -> Tuple[str, float]:
        """Synthesize and normalize voiceover audio."""
        logger.info(f"Producing voiceover for project '{project_id}'...")
        audio_dir = project_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        target_file = str(audio_dir / "narration.m4a")
        
        # Dynamically select a distinct voice
        chosen_voice = random.choice(tts_service.high_quality_voices)
        logger.info(f"Selected diverse voice: {chosen_voice}")
        
        audio_path, duration = tts_service.generate_speech(
            text=script.full_narration,
            output_file=target_file,
            voice=chosen_voice,
        )

        logger.info(f"Voiceover generated: {audio_path} ({duration:.2f}s)")
        return audio_path, duration


voice_agent = VoiceAgent()
