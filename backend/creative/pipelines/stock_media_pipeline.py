from typing import List
from pathlib import Path
from backend.models import ScriptModel, VisualAsset
from backend.creative.creative_director import CreativeDirection
from backend.creative.pipelines.base import BaseRenderPipeline
from backend.agents import visual_agent

class StockMediaPipeline(BaseRenderPipeline):
    def render_assets(
        self,
        project_id: str,
        script: ScriptModel,
        project_dir: Path,
        direction: CreativeDirection,
        topic: str = "",
        aesthetic_style: str = "cinematic",
    ) -> List[VisualAsset]:
        
        # The visual agent handles its own asset directory creation and API fetching
        assets = visual_agent.collect_visuals(
            project_id=project_id,
            topic=topic,
            script=script,
            project_dir=project_dir,
            aesthetic_style=aesthetic_style,
        )
        
        return assets
