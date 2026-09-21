import os
import shutil
from typing import List
from pathlib import Path
from backend.models import ScriptModel, VisualAsset
from backend.creative.creative_director import CreativeDirection
from backend.creative.pipelines.base import BaseRenderPipeline
from backend.agents import visual_agent
from backend.services.ffmpeg_service import ffmpeg_service
from backend.core.logging import logger

class CinematicPipeline(BaseRenderPipeline):
    """
    The 'Dramaclaw' Cinematic Pipeline.
    Uses free unwatermarked stock footage, but applies heavy dramatic color-grading,
    contrast enhancement, and cinematic letterboxing via FFmpeg.
    """
    
    def apply_dramaclaw_effect(self, input_path: str, output_path: str) -> bool:
        """
        Applies a gritty cinematic look and letterboxing using FFmpeg filtergraphs.
        """
        # Desaturate slightly, increase contrast, lower brightness
        eq_filter = "eq=contrast=1.15:saturation=0.7:brightness=-0.05"
        # Letterbox: top and bottom 12% black bars
        letterbox_filter = "drawbox=x=0:y=0:w=iw:h=ih*0.12:color=black:t=fill,drawbox=x=0:y=ih-ih*0.12:w=iw:h=ih*0.12:color=black:t=fill"
        
        vf = f"{eq_filter},{letterbox_filter}"
        
        args = [
            "-y",
            "-i", input_path,
            "-vf", vf,
            "-c:v", "libx264",
            "-crf", "20",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        
        try:
            ret, stdout, stderr = ffmpeg_service.run_command(args, timeout=120)
            if ret == 0 and os.path.exists(output_path):
                return True
            else:
                logger.error(f"Dramaclaw effect failed: {stderr}")
                return False
        except Exception as e:
            logger.error(f"Dramaclaw effect exception: {e}")
            return False

    def render_assets(
        self,
        project_id: str,
        script: ScriptModel,
        project_dir: Path,
        direction: CreativeDirection,
        topic: str = "",
        aesthetic_style: str = "cinematic",
    ) -> List[VisualAsset]:
        
        # 1. Fetch raw, unwatermarked stock footage
        # visual_agent is configured to use Pexels API which guarantees royalty-free, unwatermarked media
        assets = visual_agent.collect_visuals(
            project_id=project_id,
            topic=topic,
            script=script,
            project_dir=project_dir,
            aesthetic_style="dark, moody, cinematic, slow motion, high quality",
        )
        
        # 2. Apply the Dramaclaw cinematic effects to each raw asset
        logger.info(f"[CinematicPipeline] Applying Dramaclaw effects to {len(assets)} assets...")
        
        for asset in assets:
            if not asset.path or not os.path.exists(asset.path):
                continue
                
            input_ext = Path(asset.path).suffix
            # Only apply to videos for now, images get Ken Burns later which might conflict if we filter them here.
            # Actually, the pipeline creates video clips out of images inside orchestrator.py OR visual_agent.
            # visual_agent returns mixed media (mp4 and jpg).
            
            if input_ext.lower() in [".mp4", ".mov", ".avi"]:
                graded_path = str(Path(asset.path).with_name(f"graded_{Path(asset.path).name}"))
                success = self.apply_dramaclaw_effect(asset.path, graded_path)
                if success:
                    asset.path = graded_path
            
        return assets
