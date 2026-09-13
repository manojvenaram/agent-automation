"""
CaptionAgent for YouTube Shorts Subtitles.
Generates synchronized mobile-optimized ASS and SRT subtitle files.
"""

from pathlib import Path
from typing import Tuple
from backend.core.logging import logger
from backend.models import ScriptModel
from backend.services.whisper_service import whisper_service


class CaptionAgent:
    def create_captions(
        self,
        project_id: str,
        script: ScriptModel,
        audio_path: str,
        audio_duration: float,
        project_dir: Path,
    ) -> Tuple[str, str]:
        """Generate styled ASS and SRT subtitle files."""
        logger.info(f"Generating captions for project '{project_id}'...")
        captions_dir = project_dir / "captions"
        captions_dir.mkdir(parents=True, exist_ok=True)

        ass_file = str(captions_dir / "subtitles.ass")
        srt_file = str(captions_dir / "subtitles.srt")

        ass_path, srt_path = whisper_service.generate_subtitles(
            audio_path=audio_path,
            full_text=script.full_narration,
            total_duration=audio_duration,
            output_ass_path=ass_file,
            output_srt_path=srt_file,
        )

        logger.info(f"Subtitles ready: {ass_path}")
        return ass_path, srt_path


caption_agent = CaptionAgent()
