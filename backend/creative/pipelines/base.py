from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path
from backend.models import ScriptModel, VisualAsset
from backend.creative.creative_director import CreativeDirection

class BaseRenderPipeline(ABC):
    """
    Abstract base class for all visual rendering pipelines.
    A pipeline is responsible for reading the script scenes and producing
    a list of VisualAssets (images, video clips, animations) that match the scenes.
    """

    @abstractmethod
    def render_assets(
        self,
        project_id: str,
        script: ScriptModel,
        project_dir: Path,
        direction: CreativeDirection,
        topic: str = "",
        aesthetic_style: str = "cinematic",
    ) -> List[VisualAsset]:
        """
        Produce or collect visuals for every scene in the script.
        Returns a list of VisualAsset objects in order.
        """
        pass
