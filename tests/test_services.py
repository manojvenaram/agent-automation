"""Unit tests for core services (FFmpeg, Subtitles, Procedural Visuals, Research)."""
import os
from pathlib import Path
from backend.services.ffmpeg_service import ffmpeg_service
from backend.services.whisper_service import whisper_service
from backend.services.asset_service import asset_service
from backend.services.research_service import research_service


def test_ffmpeg_binary_availability():
    bin_path = ffmpeg_service.ffmpeg_path
    assert os.path.exists(bin_path)
    ret, stdout, stderr = ffmpeg_service.run_command(["-version"])
    assert ret == 0
    assert "ffmpeg version" in stdout or "ffmpeg version" in stderr


def test_procedural_visual_generation(tmp_path):
    output_img = tmp_path / "test_card.jpg"
    asset_service._generate_procedural_visual(
        output_path=output_img,
        topic="Why Space Smells Like Something Burning",
        scene_index=1,
        text_snippet="Did you know outer space smells like burnt steak?",
    )
    assert output_img.exists()
    assert os.path.getsize(output_img) > 5000


def test_subtitle_generation(tmp_path):
    dummy_audio = tmp_path / "dummy.aac"
    dummy_audio.write_bytes(b"dummy")
    ass_path = tmp_path / "subtitles.ass"
    srt_path = tmp_path / "subtitles.srt"

    full_text = "Did you know that outer space smells like burnt steak? It is completely true."
    whisper_service.generate_subtitles(
        audio_path=str(dummy_audio),
        full_text=full_text,
        total_duration=6.0,
        output_ass_path=str(ass_path),
        output_srt_path=str(srt_path),
    )
    assert ass_path.exists()
    assert srt_path.exists()
    ass_content = ass_path.read_text(encoding="utf-8")
    assert "ShortsDefault" in ass_content
    assert "BURNT STEAK" in ass_content


def test_wikipedia_research_provider():
    sources = research_service.search_wikipedia("International Space Station", max_results=1)
    assert len(sources) >= 1
    assert "Space" in sources[0].title or "Station" in sources[0].title
    assert len(sources[0].extract) > 10
