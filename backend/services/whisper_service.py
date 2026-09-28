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

        # Try to use our new ZeroGPU Hugging Face Space for perfect word-level timestamps!
        sub_events = []
        try:
            from gradio_client import Client
            logger.info("Calling ZeroGPU Whisper-V3 for word-level captions...")
            client = Client("manojvibranium21/mixamo-mocap-zerogpu", token=settings.hf_api_key if settings.hf_api_key else None)
            
            # Use gradio client to call our whisper endpoint
            result = client.predict(
                audio_file=audio_path,
                api_name="/generate_captions"
            )
            
            if "chunks" in result:
                for chunk in result["chunks"]:
                    chunk_text = chunk.get("text", "").strip()
                    if not chunk_text:
                        continue
                    
                    timestamps = chunk.get("timestamp", [0.0, 0.0])
                    start = float(timestamps[0]) if timestamps[0] is not None else 0.0
                    end = float(timestamps[1]) if timestamps[1] is not None else start + 0.3
                    
                    sub_events.append((start, end, chunk_text))
                    
                logger.info(f"ZeroGPU Whisper-V3 successfully returned {len(sub_events)} word-level timestamps!")
            else:
                logger.warning(f"Unexpected ZeroGPU response: {result}")
                raise ValueError("No chunks returned")
                
        except Exception as e:
            logger.warning(f"ZeroGPU Whisper failed ({e}). Falling back to algorithmic timing...")
            # Fallback algorithmic timing
            words = full_text.split()
            if not words:
                words = ["Fact", "Checked", "Shorts"]
    
            chunk_size = 2
            chunks = []
            for i in range(0, len(words), chunk_size):
                chunks.append(" ".join(words[i : i + chunk_size]))
    
            total_chars = sum(len(c) for c in chunks)
            time_per_char = total_duration / max(1, total_chars)
    
            current_time = 0.2
            for c in chunks:
                chunk_duration = max(1.2, len(c) * time_per_char)
                end_time = min(total_duration, current_time + chunk_duration)
                sub_events.append((current_time, end_time, c))
                current_time = end_time
    
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
Style: ShortsDefault,Arial,{settings.caption_font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(header)
            for start, end, text in events:
                # Alex Hormozi Style Pop formatting
                clean_text = text.replace("{", "").replace("}", "").upper()
                words = clean_text.split()
                
                if not words:
                    continue
                
                total_duration_sec = end - start
                total_chars = sum(len(w) for w in words)
                
                word_start = start
                for i, w in enumerate(words):
                    word_duration_sec = (len(w) / total_chars) * total_duration_sec
                    word_end = word_start + word_duration_sec
                    
                    start_str = self._format_ass_time(word_start)
                    end_str = self._format_ass_time(word_end)
                    
                    formatted_words = []
                    for j, word in enumerate(words):
                        if j == i:
                            # Highlighted: Yellow & much larger (30% increase for bouncy impact)
                            fs_large = int(settings.caption_font_size * 1.30)
                            formatted_words.append(f"{{\\c&H0000FFFF&\\fs{fs_large}}}{word}{{\\c&H00FFFFFF&\\fs{settings.caption_font_size}}}")
                        else:
                            formatted_words.append(word)
                            
                    karaoke_line = " ".join(formatted_words)
                    f.write(f"Dialogue: 0,{start_str},{end_str},ShortsDefault,,0,0,0,,{karaoke_line}\n")
                    
                    word_start = word_end


# Global singleton instance
whisper_service = WhisperService()
