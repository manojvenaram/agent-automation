from typing import Dict, Type
from backend.creative.creative_director import VisualTreatment
from backend.creative.pipelines.base import BaseRenderPipeline
from backend.core.logging import logger

class PipelineRegistry:
    def __init__(self):
        self._pipelines: Dict[VisualTreatment, BaseRenderPipeline] = {}
        self._fallback_pipeline: BaseRenderPipeline = None

    def register(self, treatment: VisualTreatment, pipeline: BaseRenderPipeline) -> None:
        """Register a pipeline engine for a specific visual treatment."""
        self._pipelines[treatment] = pipeline
        logger.debug(f"Registered pipeline {pipeline.__class__.__name__} for treatment {treatment.value}")

    def set_fallback(self, pipeline: BaseRenderPipeline) -> None:
        """Set the default pipeline if a treatment has no specific registry."""
        self._fallback_pipeline = pipeline

    def get_pipeline(self, treatment: VisualTreatment) -> BaseRenderPipeline:
        """Get the pipeline for a given visual treatment, or the fallback."""
        if treatment in self._pipelines:
            return self._pipelines[treatment]
        
        if self._fallback_pipeline:
            logger.warning(f"No pipeline registered for {treatment.value}. Using fallback {self._fallback_pipeline.__class__.__name__}.")
            return self._fallback_pipeline
            
        raise ValueError(f"No pipeline registered for treatment: {treatment.value}, and no fallback set.")

pipeline_registry = PipelineRegistry()
