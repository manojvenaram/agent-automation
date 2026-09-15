"""
Text-To-Speech (TTS) Service for YouTube Shorts Narration.
Zero paid APIs.
Primary Engine: VoiceStudio (Local OpenAI-compatible API).
Fallback Engine 1: edge-tts (free neural voices e.g., en-US-ChristopherNeural).
Fallback Engine 2: pyttsx3 (offline Windows SAPI5 engine).
Performs volume normalization, silence trimming, and exact duration measurement.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Tuple
import edge_tts
from backend.core.config import settings
from backend.core.logging import logger
from backend.services.ffmpeg_service import ffmpeg_service


class TTSService:
    def __init__(self):
        self.default_voice = settings.tts_voice
        self.default_engine = settings.tts_engine
        self.high_quality_voices = [
            "en-US-ChristopherNeural",
            "en-US-AriaNeural",
            "en-GB-SoniaNeural",
            "en-AU-NatashaNeural",
            "en-US-GuyNeural",
            "en-US-EricNeural",
            "en-US-JennyNeural",
            "en-US-AnaNeural",
            "en-US-AndrewNeural",
            "en-US-BrianNeural",
            "en-US-EmmaNeural",
            "en-GB-RyanNeural",
            "en-AU-WilliamNeural"
        ]

    async def _synthesize_edge_tts(self, text: str, output_path: str, voice: Optional[str] = None) -> str:
        """Synthesize text using Microsoft Edge Neural TTS."""
        voice_to_use = voice or self.default_voice
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice_to_use,
            rate=settings.tts_rate,
            pitch=settings.tts_pitch,
        )
        await communicate.save(output_path)
        return output_path

    def _synthesize_voicestudio(self, text: str, output_path: str, voice: Optional[str] = None) -> str:
        """Synthesize text using local VoiceStudio (OpenAI-compatible) API."""
        import httpx
        import random
        openai_voices = ["alloy", "nova", "shimmer", "echo", "onyx", "fable"]
        voice_to_use = voice or random.choice(openai_voices)
        url = "http://localhost:3900/v1/audio/speech"
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice_to_use
        }
        with httpx.Client(timeout=300.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(response.content)
        return output_path

    def _synthesize_pyttsx3(self, text: str, output_path: str) -> str:
        """Synthesize text using local offline Windows SAPI5 engine."""
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        # Select best available English voice
        voices = engine.getProperty("voices")
        for v in voices:
            if "david" in v.name.lower() or "zira" in v.name.lower() or "english" in v.name.lower():
                engine.setProperty("voice", v.id)
                break

        engine.save_to_file(text, output_path)
        engine.runAndWait()
        return output_path

    def generate_speech(
        self,
        text: str,
        output_file: str,
        voice: Optional[str] = None,
    ) -> Tuple[str, float]:
        """
        Generate narration audio file and return (normalized_audio_path, duration_seconds).
        Automatically attempts primary engine, then offline fallback if network fails.
        """
        out_path = Path(output_file).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        raw_output = str(out_path.with_name("raw_" + out_path.name))

        success = False
        
        # Try VoiceStudio first
        try:
            self._synthesize_voicestudio(text, raw_output, voice)
            if os.path.exists(raw_output) and os.path.getsize(raw_output) > 100:
                success = True
                logger.info("VoiceStudio synthesis succeeded.")
        except Exception as e:
            logger.warning(f"VoiceStudio failed or is not running locally on port 3900 ({e}), attempting edge-tts...")
            
        # Try primary fallback edge-tts
        if not success:
            try:
                # Run async edge-tts in event loop
                asyncio.run(self._synthesize_edge_tts(text, raw_output, voice))
                if os.path.exists(raw_output) and os.path.getsize(raw_output) > 100:
                    success = True
                    logger.info(f"Edge-TTS synthesis completed: {len(text)} chars")
            except Exception as e:
                logger.warning(f"Edge-TTS failed ({e}), attempting pyttsx3 offline fallback...")

        # Try offline pyttsx3 fallback
        if not success:
            try:
                self._synthesize_pyttsx3(text, raw_output)
                if os.path.exists(raw_output) and os.path.getsize(raw_output) > 100:
                    success = True
                    logger.info("pyttsx3 offline synthesis succeeded.")
            except Exception as e:
                logger.error(f"pyttsx3 offline synthesis also failed: {e}")
                raise RuntimeError(f"All TTS engines failed: {e}")

        # Post-process audio: normalize loudness, trim excessive leading/trailing silence, output high quality 44.1kHz AAC
        normalized_output = str(out_path)
        self._normalize_audio(raw_output, normalized_output)

        # Probe final duration
        info = ffmpeg_service.probe_file(normalized_output)
        duration = info["duration"]

        # Clean raw temp file
        if os.path.exists(raw_output) and raw_output != normalized_output:
            try:
                os.remove(raw_output)
            except OSError:
                pass

        return normalized_output, duration

    def _normalize_audio(self, input_file: str, output_file: str):
        """Use FFmpeg to normalize volume (-16 LUFS / loudnorm) and clean silences."""
        # loudnorm=I=-16:TP=-1.5:LRA=11,silenceremove=start_periods=1:start_duration=0.1:start_threshold=-50dB
        af = "loudnorm=I=-16:TP=-1.5:LRA=11,silenceremove=start_periods=1:start_threshold=-50dB"
        args = [
            "-y",
            "-i", input_file,
            "-af", af,
            "-ar", "44100",
            "-ac", "2",
            "-c:a", "aac",
            "-b:a", "192k",
            output_file,
        ]
        ret, stdout, stderr = ffmpeg_service.run_command(args, timeout=60)
        if ret != 0:
            logger.warning(f"Loudnorm filter failed, using basic copy: {stderr[:150]}")
            # Fallback simple conversion
            fb_args = ["-y", "-i", input_file, "-ar", "44100", "-c:a", "aac", output_file]
            ffmpeg_service.run_command(fb_args, timeout=30)


# Global singleton instance
tts_service = TTSService()
