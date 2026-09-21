from typing import List
from pathlib import Path
from backend.models import ScriptModel, VisualAsset
from backend.creative.creative_director import CreativeDirection
from backend.creative.pipelines.base import BaseRenderPipeline
from backend.creative.cartoon_engine import cartoon_engine, CharacterPose

class CartoonPipeline(BaseRenderPipeline):
    def render_assets(
        self,
        project_id: str,
        script: ScriptModel,
        project_dir: Path,
        direction: CreativeDirection,
        topic: str = "",
        aesthetic_style: str = "cartoon",
    ) -> List[VisualAsset]:
        
        visuals_dir = project_dir / "visuals"
        visuals_dir.mkdir(parents=True, exist_ok=True)
        assets: List[VisualAsset] = []

        char_name = direction.character_assigned or "Byte"
        poses = [
            CharacterPose.CONFIDENT,
            CharacterPose.SKEPTICAL,
            CharacterPose.THINKING,
            CharacterPose.SHOCKED,
            CharacterPose.CELEBRATING,
        ]

        for idx, sc in enumerate(script.scenes):
            asset_id = f"asset_{idx+1:03d}"
            target_file = visuals_dir / f"{asset_id}.jpg"
            pose = poses[idx % len(poses)]
            theme = "comedy" if direction.humor_suitability > 60 else "space"

            # Render scene
            cartoon_engine.render_scene(
                character_name=char_name,
                pose=pose,
                caption_title=f"SCENE {idx+1}",
                dialogue=sc.narration[:80] + ("..." if len(sc.narration) > 80 else ""),
                output_path=target_file,
                theme=theme,
            )

            assets.append(
                VisualAsset(
                    asset_id=asset_id,
                    file_path=str(target_file),
                    source_url="local://procedural/cartoon_engine",
                    source_name="Procedural Cartoon Engine",
                    license="Original Copyright Free Channel Asset",
                    creator="Byte & Sam Universe",
                    attribution_required=False,
                    is_procedural=True,
                )
            )

        return assets
