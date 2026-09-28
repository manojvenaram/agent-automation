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
from backend.services.video_gen_service import video_gen_service
from backend.services.sfx_service import sfx_service
from backend.services.avatar_service import avatar_service


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
        # Add 0.5s to each scene to account for the xfade overlap during concatenation
        scene_duration = (audio_duration / max(1, num_scenes)) + 0.5

        scene_video_files = []
        for idx, scene in enumerate(script.scenes):
            # Select asset matching index
            asset = assets[idx % len(assets)]
            scene_out = str(temp_dir / f"scene_{idx+1:03d}.mp4")
            
            if asset.file_path.endswith('.mp4'):
                logger.info(f"Rendering scene {idx+1}/{num_scenes} ({scene_duration:.2f}s, format: procedural_mp4)...")
                ffmpeg_service.process_video_scene(
                    video_path=asset.file_path,
                    output_path=scene_out,
                    duration=scene_duration,
                )
            else:
                # Alternate zoom directions for engaging visual dynamics on static images
                direction = "in" if idx % 2 == 0 else "out"
                logger.info(f"Rendering scene {idx+1}/{num_scenes} ({scene_duration:.2f}s, format: static_image, zoom: {direction})...")
                logger.info(f"Using VideoGenService to generate cinematic video for scene {idx+1}")
                # Use Video Prompter prompt from script if available, else fallback to basic scene description
                prompt = getattr(scene, 'visual_description', f"High quality cinematic 9:16 vertical video of {asset.file_path}")
                try:
                    video_gen_service.generate_video(
                        prompt=prompt,
                        output_path=scene_out
                    )
                    ffmpeg_service.process_video_scene(
                        video_path=scene_out,
                        output_path=scene_out + "_processed.mp4",
                        duration=scene_duration,
                    )
                    # Swap original generated file with the processed (trimmed/scaled) one
                    import shutil
                    shutil.move(scene_out + "_processed.mp4", scene_out)
                except Exception as e:
                    logger.warning(f"VideoGenService failed ({e}). Falling back to cinematic Ken Burns pan on static image.")
                    ffmpeg_service.create_still_scene_video(
                        image_path=asset.file_path,
                        output_path=scene_out,
                        duration=scene_duration,
                    )
            scene_video_files.append(scene_out)

        # Concatenate scenes
        concatenated_video = str(temp_dir / "scenes_concat.mp4")
        logger.info("Concatenating rendered scenes...")
        ffmpeg_service.concatenate_scenes(scene_video_files, concatenated_video)

        # Select royalty-free ambient music track
        bg_music = asset_service.get_background_music(topic=script.context, duration=int(audio_duration) + 2)
        logger.info(f"Selected background music: {bg_music}")

        # Generate custom SFX
        sfx_path = str(render_dir / "whoosh_sfx.wav")
        logger.info("Generating AI sound effect (cinematic whoosh)...")
        has_sfx = sfx_service.generate_sfx("cinematic heavy whoosh impact sound effect, high quality", sfx_path)
        final_sfx = sfx_path if has_sfx else None

        # Generate SadTalker Avatar
        avatar_vid_path = None
        if getattr(avatar_service, "enabled", False):
            # We assume a default avatar image is available in a core assets folder, or we use a fallback
            default_avatar = str(project_dir.parent.parent / "backend" / "assets" / "default_avatar.jpg")
            if Path(default_avatar).exists():
                out_avatar = str(render_dir / "avatar.mp4")
                success = avatar_service.generate_talking_avatar(audio_path, out_avatar, default_avatar)
                if success:
                    avatar_vid_path = out_avatar

        # Final composition: burn subtitles, mix and duck audio, export final MP4
        final_mp4 = str(render_dir / "final.mp4")
        logger.info("Compositing final video with audio ducking and subtitles...")
        ffmpeg_service.composite_final_short(
            video_input=concatenated_video,
            voiceover_audio=audio_path,
            output_path=final_mp4,
            subtitles_file=subtitles_file,
            background_music=bg_music,
            sfx_file=final_sfx,
            music_volume=0.10,
            avatar_video=avatar_vid_path,
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
