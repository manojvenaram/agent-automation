"""
VisualResearchAgent for YouTube Shorts.
Acquires Public Domain / Creative Commons media or synthesizes procedural visuals.
Ensures zero broken scenes, validates dimensions, and logs licensing.
"""

from pathlib import Path
from typing import List
from backend.core.database import save_assets
from backend.core.logging import logger
from backend.models import ScriptModel, VisualAsset
from backend.services.asset_service import asset_service


class VisualResearchAgent:
    def collect_visuals(
        self,
        project_id: str,
        topic: str,
        script: ScriptModel,
        project_dir: Path,
        aesthetic_style: str = "high quality cinematic vertical portrait",
    ) -> List[VisualAsset]:
        """Collect or generate high quality 9:16 visual assets for each scene."""
        logger.info(f"Collecting visual assets for project '{project_id}' ({len(script.scenes)} scenes)...")
        scenes_data = [
            {
                "scene_index": sc.scene_index,
                "narration": sc.narration,
                "visual_description": sc.visual_description,
            }
            for sc in script.scenes
        ]

        assets = asset_service.fetch_or_generate_visuals(
            project_id=project_id,
            topic=topic,
            scenes_info=scenes_data,
            project_dir=project_dir,
            aesthetic_style=aesthetic_style,
        )

        save_assets(project_id, assets)
        logger.info(f"Secured {len(assets)} visual assets for project '{project_id}'.")
        return assets


visual_agent = VisualResearchAgent()
