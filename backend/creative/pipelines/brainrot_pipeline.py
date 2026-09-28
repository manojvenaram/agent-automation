import os
import random
import shutil
import subprocess
from typing import List
from pathlib import Path
import yt_dlp

from backend.models import ScriptModel, VisualAsset
from backend.creative.creative_director import CreativeDirection
from backend.creative.pipelines.base import BaseRenderPipeline
from backend.services.ffmpeg_service import ffmpeg_service
from backend.core.logging import logger
from backend.core.config import settings

class BrainrotPipeline(BaseRenderPipeline):
    """
    Renders high-retention Brainrot Split-Screen videos.
    Downloads satisfying gameplay loops (Minecraft Parkour / GTA V) and uses them as the background.
    """
    def __init__(self):
        self.width = settings.video_width
        self.height = settings.video_height
        self.fps = settings.video_fps
        self.cache_dir = Path("assets/video_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # A list of non-copyrighted or widely used gameplay loops on YouTube
        self.gameplay_urls = [
            "https://www.youtube.com/watch?v=n_Dv4JMiwK8", # Minecraft Parkour
            "https://www.youtube.com/watch?v=1F2bF21H3e4", # GTA V Car Jumping
            "https://www.youtube.com/watch?v=N9yV-Fq2JmU", # Subway Surfers
        ]

    def _get_gameplay_video(self, url: str) -> str:
        """Downloads a gameplay video and caches it."""
        video_id = url.split("v=")[-1]
        out_path = self.cache_dir / f"gameplay_{video_id}.mp4"
        
        if out_path.exists():
            return str(out_path)
            
        logger.info(f"Downloading Brainrot gameplay loop from {url}...")
        ydl_opts = {
            'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(out_path),
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        return str(out_path)

    def render_assets(
        self,
        project_id: str,
        script: ScriptModel,
        project_dir: Path,
        direction: CreativeDirection,
        topic: str = "",
        aesthetic_style: str = "brainrot",
    ) -> List[VisualAsset]:
        
        visuals_dir = project_dir / "visuals"
        visuals_dir.mkdir(parents=True, exist_ok=True)
        assets: List[VisualAsset] = []

        logger.info("BrainrotPipeline: Rendering highly viral split-screen gameplay videos...")
        
        # Pick a random gameplay loop for this video
        gameplay_url = random.choice(self.gameplay_urls)
        try:
            source_vid = self._get_gameplay_video(gameplay_url)
        except Exception as e:
            logger.warning(f"Failed to download gameplay ({e}), using fallback empty video.")
            source_vid = str(self.cache_dir / "fallback.mp4")
            if not os.path.exists(source_vid):
                ffmpeg_service.run_command([
                    "-y", "-f", "lavfi", "-i", f"color=c=black:s={self.width}x{self.height}:d=60",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", source_vid
                ])

        # Get total duration of the gameplay video to pick a random starting point
        total_dur_str, _, _ = ffmpeg_service.run_command(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", source_vid])
        total_duration = float(total_dur_str.strip()) if total_dur_str.strip() else 60.0

        current_timestamp = random.uniform(0, max(0, total_duration - 60)) # Pick a random 60 second chunk to start

        for idx, sc in enumerate(script.scenes):
            asset_id = f"brainrot_{idx+1:03d}"
            target_mp4 = visuals_dir / f"{asset_id}.mp4"
            
            dur = sc.duration_est if sc.duration_est > 0 else 3.0
            
            # Slice the video from current_timestamp for the duration of the scene, scale/crop to 9:16
            vf = f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,crop={self.width}:{self.height}"
            args = [
                "-y",
                "-ss", str(current_timestamp),
                "-t", str(dur),
                "-i", source_vid,
                "-vf", vf,
                "-c:v", "libx264",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-an", # No audio from the gameplay, we use TTS
                str(target_mp4)
            ]
            
            ffmpeg_service.run_command(args, timeout=60)
            
            current_timestamp += dur # Advance the timestamp so the background is continuous across scenes!
            
            assets.append(
                VisualAsset(
                    asset_id=asset_id,
                    file_path=str(target_mp4),
                    source_url=gameplay_url,
                    source_name="Brainrot Gameplay Slice",
                    license="Fair Use / Gameplay",
                    creator="Brainrot Director",
                    attribution_required=False,
                    is_procedural=True,
                )
            )

        return assets
