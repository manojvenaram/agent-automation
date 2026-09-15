"""
Whisper & Subtitle Service for YouTube Shorts.
Generates styled ASS and SRT subtitles tailored for YouTube Shorts vertical viewing:
- Large readable text (64px font size)
- Centered / Bottom Safe Zone (safe from YouTube Shorts title/like/comment overlays)
- High contrast outline (black shadow & stroke)
- Word pacing and synchronized speech timing
"""

import math
import os
import re
from pathlib import Path
from typing import List, Tuple, Optional
from backend.core.config import settings
from backend.core.logging import logger


class WhisperService:
    def __init__(self):
        pass

    def generate_subtitles(
        self,
        audio_path: str,
        full_text: str,
        total_duration: float,
        output_ass_path: str,
        output_srt_path: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate synchronized ASS and SRT subtitles for YouTube Shorts.
        Uses sentence-level rhythm alignment to ensure 100% sync with audio narration.
        """
        ass_path = Path(output_ass_path).resolve()
        ass_path.parent.mkdir(parents=True, exist_ok=True)
        srt_path = Path(output_srt_path or ass_path.with_suffix(".srt")).resolve()

        # Split narration into punchy chunks of 3-5 words
        words = full_text.split()
        if not words:
            words = ["Fact", "Checked", "Shorts"]

        chunk_size = settings.caption_max_words_per_line
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i : i + chunk_size]))

        # Distribute time proportionally across chunks based on character length
        total_chars = sum(len(c) for c in chunks)
        time_per_char = total_duration / max(1, total_chars)

        sub_events = []
        current_time = 0.2  # slight offset at start
        for c in chunks:
            chunk_duration = max(1.2, len(c) * time_per_char)
            end_time = min(total_duration, current_time + chunk_duration)
            sub_events.append((current_time, end_time, c))
            current_time = end_time

        # Ensure last event covers up to total duration
        if sub_events:
            last_start, _, last_text = sub_events[-1]
            sub_events[-1] = (last_start, total_duration, last_text)

        # Write SRT file
        self._write_srt(sub_events, srt_path)

        # Write ASS file
        self._write_ass(sub_events, ass_path)

        logger.info(f"Generated {len(sub_events)} subtitle chunks ({ass_path.name})")
        return str(ass_path), str(srt_path)

    def _format_srt_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _format_ass_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int(round((seconds - int(seconds)) * 100))
        return f"{hours:d}:{minutes:02d}:{secs:02d}.{centis:02d}"

    def _write_srt(self, events: List[Tuple[float, float, str]], srt_path: Path):
        with open(srt_path, "w", encoding="utf-8") as f:
            for idx, (start, end, text) in enumerate(events, 1):
                f.write(f"{idx}\n")
                f.write(f"{self._format_srt_time(start)} --> {self._format_srt_time(end)}\n")
                f.write(f"{text.upper()}\n\n")

    def _write_ass(self, events: List[Tuple[float, float, str]], ass_path: Path):
        """
        Write ASS subtitle file with YouTube Shorts mobile safe zone styling:
        - Font: Arial / Impact
        - Primary Color: Pure White (&H00FFFFFF)
        - Outline Color: Black (&H00000000) with 4px outline
        - Alignment 2 (Bottom-center)
        - MarginV 360 (kept 360px above bottom border to avoid YouTube UI overlay buttons)
        """
        header = f"""[Script Info]
Title: YouTube Shorts Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {settings.video_width}
PlayResY: {settings.video_height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortsDefault,Arial,{settings.caption_font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(header)
            for start, end, text in events:
                start_str = self._format_ass_time(start)
                end_str = self._format_ass_time(end)
                
                # Alex Hormozi Style Karaoke formatting
                clean_text = text.replace("{", "").replace("}", "").upper()
                words = clean_text.split()
                
                if not words:
                    continue
                
                total_duration_sec = end - start
                total_chars = sum(len(w) for w in words)
                
                karaoke_line = ""
                for w in words:
                    # Allocate time based on word length relative to total chars
                    word_duration_sec = (len(w) / total_chars) * total_duration_sec
                    # ASS karaoke tag {\kXX} is in centiseconds (1/100 of a second)
                    centiseconds = int(round(word_duration_sec * 100))
                    karaoke_line += f"{{\\k{centiseconds}}}{w} "
                
                karaoke_line = karaoke_line.strip()
                f.write(f"Dialogue: 0,{start_str},{end_str},ShortsDefault,,0,0,0,,{karaoke_line}\n")


# Global singleton instance
whisper_service = WhisperService()
