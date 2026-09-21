from .base import BaseRenderPipeline
from .registry import pipeline_registry, PipelineRegistry
from backend.creative.creative_director import VisualTreatment

from .cartoon_pipeline import CartoonPipeline
from .stock_media_pipeline import StockMediaPipeline
from .stickman_pipeline import StickmanPipeline
from .cinematic_pipeline import CinematicPipeline
from .hyperframes_pipeline import HyperframesPipeline

# Register the default implementations
pipeline_registry.register(VisualTreatment.CARTOON, CartoonPipeline())
pipeline_registry.register(VisualTreatment.WHITEBOARD_STICKMAN, StickmanPipeline())
pipeline_registry.register(VisualTreatment.CINEMATIC, CinematicPipeline())
pipeline_registry.register(VisualTreatment.WEB_RENDER, HyperframesPipeline())

# Set stock media as the fallback for everything else (Animation, Motion Graphics, Maps, etc.)
pipeline_registry.set_fallback(StockMediaPipeline())

__all__ = ["BaseRenderPipeline", "pipeline_registry", "PipelineRegistry"]
