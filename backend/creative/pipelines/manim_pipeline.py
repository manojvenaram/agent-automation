import subprocess
import os
import shutil
from typing import List
from pathlib import Path

from backend.models import ScriptModel, VisualAsset
from backend.creative.creative_director import CreativeDirection
from backend.creative.pipelines.base import BaseRenderPipeline
from backend.core.logging import logger
from backend.core.config import settings

class ManimPipeline(BaseRenderPipeline):
    """
    Renders clean, educational vector animations using the Manim Engine.
    """
    def __init__(self):
        self.width = settings.video_width
        self.height = settings.video_height
        self.fps = settings.video_fps
        self._check_manim_installed()

    def _check_manim_installed(self):
        if not shutil.which("manim"):
            logger.warning("Manim is not installed or not in PATH! ManimPipeline will fail if called.")

    def _generate_scene_script(self, text: str, duration: float, script_path: Path):
        """Generates a Python script defining a Manim Scene."""
        # Sanitize text for Python string
        safe_text = text.replace('"', '\\"').replace('\n', ' ')
        
        # We render at 1080x1920 (vertical). Manim defaults to 16:9.
        # We configure it via CLI flags, but we must make sure the text wraps appropriately.
        
        manim_code = f"""
from manim import *

# Configure vertical resolution
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9.0
config.frame_height = 16.0
config.background_color = "#1A1A1A"

class ExplainerScene(Scene):
    def construct(self):
        # Create text with word wrap
        text_obj = MarkupText(
            "{safe_text}", 
            justify=True, 
            line_spacing=1.5,
            width=7.5 # Keep inside the 9.0 frame width
        ).scale(0.8)
        
        # Simple animation: Write the text
        self.play(Write(text_obj), run_time=min(2.0, {duration} * 0.5))
        
        # Wait for the remainder of the duration
        remaining = max(0.1, {duration} - min(2.0, {duration} * 0.5))
        self.wait(remaining)
"""
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(manim_code)

    def render_assets(
        self,
        project_id: str,
        script: ScriptModel,
        project_dir: Path,
        direction: CreativeDirection,
        topic: str = "",
        aesthetic_style: str = "educational",
    ) -> List[VisualAsset]:
        
        visuals_dir = project_dir / "visuals"
        visuals_dir.mkdir(parents=True, exist_ok=True)
        assets: List[VisualAsset] = []

        manim_temp_dir = visuals_dir / "manim_temp"
        manim_temp_dir.mkdir(parents=True, exist_ok=True)

        for idx, sc in enumerate(script.scenes):
            asset_id = f"asset_{idx+1:03d}"
            target_mp4 = visuals_dir / f"{asset_id}.mp4"
            
            duration_sec = sc.duration_est
            if duration_sec <= 0:
                duration_sec = 3.0
                
            script_file = manim_temp_dir / f"scene_{idx}.py"
            self._generate_scene_script(sc.narration, duration_sec, script_file)

            logger.info(f"Rendering Manim Explainer scene {idx+1}...")
            
            # Run manim CLI
            # -qk = 4k quality, -qh = 1080p, -qm = 720p, -ql = 480p
            quality = "-qh" if settings.render_mode != "low_resource" else "-ql"
            
            cmd = [
                "manim",
                "render",
                str(script_file),
                "ExplainerScene",
                quality,
                "--format=mp4",
                "--media_dir", str(manim_temp_dir),
                "--fps", str(self.fps),
                "-o", f"{asset_id}.mp4"
            ]
            
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Manim outputs to a nested structure like: media_dir/videos/scene_X/1080p60/asset_xxx.mp4
                # We need to find the output file and move it to target_mp4
                output_video = list(manim_temp_dir.glob(f"**/{asset_id}.mp4"))
                if output_video:
                    shutil.move(str(output_video[0]), str(target_mp4))
                    logger.info(f"Rendered Manim scene {idx+1} -> {target_mp4}")
                else:
                    raise FileNotFoundError(f"Manim output not found for scene {idx+1}")
                    
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode('utf-8', errors='replace') if e.stderr else "Unknown error"
                logger.error(f"Manim rendering failed for scene {idx+1}: {err_msg}")
                raise RuntimeError(f"Manim failed: {err_msg}")

            assets.append(
                VisualAsset(
                    asset_id=asset_id,
                    file_path=str(target_mp4),
                    source_url="local://procedural/manim_engine",
                    source_name="Manim Vector Animation Engine",
                    license="Original Copyright Free Channel Asset",
                    creator="Manim Director",
                    attribution_required=False,
                    is_procedural=True,
                )
            )

        # Cleanup temp directory
        shutil.rmtree(manim_temp_dir, ignore_errors=True)
        return assets
