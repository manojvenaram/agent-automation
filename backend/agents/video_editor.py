"""
VideoEditorAgent for YouTube Shorts Composition.
Orchestrates scene rendering with Ken Burns pan/zoom, scene concatenation,
audio ducking (narration 100%, music 10-12%), subtitle burn-in,
and exports final YouTube Shorts compliant 1080x1920 30FPS MP4.
"""

from pathlib import Path
from typing import List, Optional
from backend.core.config import settings
from backend.core.logging import logger
from backend.models import ScriptModel, VisualAsset
from backend.services.asset_service import asset_service
from backend.services.ffmpeg_service import ffmpeg_service


class VideoEditorAgent:
    def render_short(
        self,
        project_id: str,
        script: ScriptModel,
        assets: List[VisualAsset],
        audio_path: str,
        audio_duration: float,
        subtitles_file: str,
        project_dir: Path,
    ) -> str:
        """Compose and render final YouTube Shorts video."""
        logger.info(f"Rendering video for project '{project_id}' (Duration: {audio_duration:.2f}s)...")
        render_dir = project_dir / "render"
        temp_dir = project_dir / "temp"
        render_dir.mkdir(parents=True, exist_ok=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Distribute audio duration across scenes
        num_scenes = len(script.scenes)
        scene_duration = audio_duration / max(1, num_scenes)

        scene_video_files = []
        for idx, scene in enumerate(script.scenes):
            # Select asset matching index
            asset = assets[idx % len(assets)]
            scene_out = str(temp_dir / f"scene_{idx+1:03d}.mp4")
            
            # Alternate zoom directions for engaging visual dynamics
            direction = "in" if idx % 2 == 0 else "out"
            
            logger.info(f"Rendering scene {idx+1}/{num_scenes} ({scene_duration:.2f}s, zoom: {direction})...")
            ffmpeg_service.create_still_scene_video(
                image_path=asset.file_path,
                output_path=scene_out,
                duration=scene_duration,
                zoom_direction=direction,
            )
            scene_video_files.append(scene_out)

        # Concatenate scenes
        concatenated_video = str(temp_dir / "scenes_concat.mp4")
        logger.info("Concatenating rendered scenes...")
        ffmpeg_service.concatenate_scenes(scene_video_files, concatenated_video)

        # Select royalty-free ambient music track
        bg_music = asset_service.get_background_music()
        logger.info(f"Selected background music: {bg_music}")

        # Final composition: burn subtitles, mix and duck audio, export final MP4
        final_mp4 = str(render_dir / "final.mp4")
        logger.info("Compositing final video with audio ducking and subtitles...")
        ffmpeg_service.composite_final_short(
            video_input=concatenated_video,
            voiceover_audio=audio_path,
            output_path=final_mp4,
            subtitles_file=subtitles_file,
            background_music=bg_music,
            music_volume=0.10,
        )

        # Clean temporary scene files
        for sv in scene_video_files:
            try:
                Path(sv).unlink(missing_ok=True)
            except OSError:
                pass

        logger.info(f"Final YouTube Short rendered successfully: {final_mp4}")
        return final_mp4


video_editor_agent = VideoEditorAgent()
